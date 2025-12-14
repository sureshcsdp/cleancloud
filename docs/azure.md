# Azure Setup Guide

Complete configuration guide for running CleanCloud against Azure subscriptions.

---

## Overview

CleanCloud scans Azure subscriptions to identify orphaned, untagged, and potentially inactive resources using **read-only APIs only**. No resources are ever modified, deleted, or tagged.

**What CleanCloud detects:**
- Unattached managed disks (7-14+ days old)
- Old managed disk snapshots (30+ days)
- Untagged managed disks and snapshots
- Unused public IP addresses

**What CleanCloud does NOT do:**
- ❌ Delete or modify resources
- ❌ Make cost optimization recommendations
- ❌ Enforce policies automatically
- ❌ Require billing/cost data access

---

## Quick Start

### 1. Validate Credentials

```bash
cleancloud doctor --provider azure
```

This validates:
- Azure service principal credentials are configured
- Required RBAC permissions exist
- Subscription access works

### 2. Run a Scan

```bash
# All accessible subscriptions
cleancloud scan --provider azure

# Specific region filter
cleancloud scan --provider azure --region eastus

# Export to JSON
cleancloud scan --provider azure --output json --output-file results.json
```

---

## RBAC Permissions

CleanCloud requires **read-only permissions** only.

### Recommended Role Assignment

Assign the built-in **Reader** role to your service principal:

```bash
# Get your subscription ID
az account show --query id -o tsv

# Create service principal with Reader role
az ad sp create-for-rbac \
  --name "CleanCloudScanner" \
  --role "Reader" \
  --scopes /subscriptions/{subscription-id}
```

This returns credentials needed for authentication (see below).

### What Reader Role Allows

The Reader role provides read-only access to:
- ✅ Microsoft.Compute/disks/read
- ✅ Microsoft.Compute/snapshots/read
- ✅ Microsoft.Network/publicIPAddresses/read
- ✅ Microsoft.Resources/subscriptions/read

### What Reader Role Does NOT Allow

- ❌ Delete operations (`*/delete`)
- ❌ Modification operations (`*/write`)
- ❌ Tagging operations (`Microsoft.Resources/tags/*`)
- ❌ Billing data access (`Microsoft.CostManagement/*`)

### Custom Role (Optional)

If your organization requires least-privilege policies, create a custom role:

```json
{
  "Name": "CleanCloud Scanner",
  "Description": "Read-only access for CleanCloud hygiene scanning",
  "Actions": [
    "Microsoft.Compute/disks/read",
    "Microsoft.Compute/snapshots/read",
    "Microsoft.Network/publicIPAddresses/read",
    "Microsoft.Resources/subscriptions/read"
  ],
  "NotActions": [],
  "AssignableScopes": [
    "/subscriptions/{subscription-id}"
  ]
}
```

Save as `cleancloud-role.json` and create:

```bash
az role definition create --role-definition cleancloud-role.json

az role assignment create \
  --assignee {service-principal-app-id} \
  --role "CleanCloud Scanner" \
  --scope /subscriptions/{subscription-id}
```

---

## Authentication

CleanCloud uses Azure service principal authentication via environment variables.

### Required Environment Variables

```bash
export AZURE_CLIENT_ID="<service-principal-app-id>"
export AZURE_TENANT_ID="<azure-tenant-id>"
export AZURE_CLIENT_SECRET="<service-principal-password>"
```

### Optional Environment Variable

```bash
# Scan only a specific subscription (otherwise scans all accessible)
export AZURE_SUBSCRIPTION_ID="<subscription-id>"
```

### Creating Service Principal Credentials

```bash
# Create service principal and capture output
az ad sp create-for-rbac \
  --name "CleanCloudScanner" \
  --role "Reader" \
  --scopes /subscriptions/{subscription-id}

# Output (save these values):
{
  "appId": "12345678-1234-1234-1234-123456789abc",      # → AZURE_CLIENT_ID
  "displayName": "CleanCloudScanner",
  "password": "abcdef123456...",                         # → AZURE_CLIENT_SECRET
  "tenant": "87654321-4321-4321-4321-fedcba987654"      # → AZURE_TENANT_ID
}
```

### Non-Interactive Authentication

CleanCloud is designed for CI/CD and does NOT support:
- ❌ Interactive browser login
- ❌ Device code flow
- ❌ Azure CLI credential passthrough

This ensures CleanCloud works in:
- ✅ GitHub Actions
- ✅ GitLab CI
- ✅ Jenkins
- ✅ Kubernetes jobs
- ✅ Headless environments

---

## Rules

CleanCloud implements 4 conservative, high-signal rules for Azure.

### 1. Unattached Managed Disks

**Rule ID:** `azure.unattached_managed_disk`

**Detects:** Managed disks not attached to any virtual machine and older than 7-14 days.

**Signals:**
- `disk.managed_by == null` (not attached to VM)
- Disk age ≥ 14 days (HIGH confidence)
- Disk age ≥ 7 days (MEDIUM confidence)

**Why age thresholds:** IaC and autoscaling create temporary disks. Age filtering prevents false positives on legitimate short-lived resources.

**Confidence:** HIGH (14+ days), MEDIUM (7-13 days)  
**Risk:** LOW

**Common causes:**
- Disks from deleted VMs
- Failed deployments
- Autoscaling group churn

**Required permission:** `Microsoft.Compute/disks/read`

---

### 2. Old Managed Disk Snapshots

**Rule ID:** `azure.old_snapshot`

**Detects:** Managed disk snapshots older than 30-90 days.

**Signals:**
- Snapshot age ≥ 90 days (HIGH confidence)
- Snapshot age ≥ 30 days (MEDIUM confidence)

**Conservative approach:** Age-based only. Does NOT attempt to detect if snapshot is referenced by images or restore points (to avoid false positives).

**Confidence:** HIGH (90+ days), MEDIUM (30-89 days)  
**Risk:** LOW

**Common causes:**
- Snapshots from backup jobs
- Over-retention without lifecycle policies
- Snapshots from deleted disks

**Required permission:** `Microsoft.Compute/snapshots/read`

---

### 3. Untagged Resources

**Rule ID:** `azure.untagged_resource`

**Detects:** Resources with no tags at all.

**Resources scanned:**
- Managed disks
- Managed disk snapshots (7+ days old only)

**Signals:**
- Empty or missing tag collection
- For disks: MEDIUM confidence if also unattached, otherwise LOW
- For snapshots: LOW confidence (requires 7+ day age filter)

**Why this matters:** Untagged resources are difficult to attribute to owners or cost centers, making them high-risk for becoming orphaned.

**Confidence:** LOW to MEDIUM  
**Risk:** LOW

**Required permissions:**
- `Microsoft.Compute/disks/read`
- `Microsoft.Compute/snapshots/read`

---

### 4. Unused Public IP Addresses

**Rule ID:** `azure.public_ip_unused`

**Detects:** Public IP addresses not attached to any network interface.

**Signal:** `publicIP.ip_configuration == null`

**Why safe:** Attachment state is deterministic. No age thresholds or heuristics needed.

**Confidence:** HIGH  
**Risk:** LOW

**Common causes:**
- IPs from deleted VMs or load balancers
- Reserved IPs no longer in use
- Failed deployments

**Azure cost note:** Unused public IPs incur charges even when unattached.

**Required permission:** `Microsoft.Network/publicIPAddresses/read`

---

## Multi-Subscription Scanning

### All Subscriptions (Default)

```bash
cleancloud scan --provider azure
```

CleanCloud discovers all subscriptions accessible to the service principal and scans them sequentially.

### Single Subscription

```bash
export AZURE_SUBSCRIPTION_ID="12345678-1234-1234-1234-123456789abc"
cleancloud scan --provider azure
```

When `AZURE_SUBSCRIPTION_ID` is set, only that subscription is scanned.

### Region Filtering

```bash
# Scan only resources in East US region
cleancloud scan --provider azure --region eastus

# Scan only resources in West Europe
cleancloud scan --provider azure --region westeurope
```

Azure uses "location" terminology internally but CleanCloud accepts `--region` for consistency with AWS.

---

## Output Formats

### Human-Readable (Default)

```bash
cleancloud scan --provider azure

# Example output:
🔍 Found 2 hygiene issues:

1. [AZURE] Unattached Azure managed disk
   Resource : azure.managed_disk → /subscriptions/.../disk-old-123
   Region   : eastus
   Confidence: HIGH
   Reason   : Disk has no VM attachment and exceeds age threshold
   Details:
     - age_days: 47
     - size_gb: 100
```

### JSON

```bash
cleancloud scan --provider azure --output json --output-file results.json
```

**Schema:**
```json
{
  "summary": {
    "total_findings": 8,
    "by_provider": {"azure": 8},
    "by_confidence": {"HIGH": 5, "MEDIUM": 2, "LOW": 1},
    "scanned_at": "2025-01-15T10:30:00Z"
  },
  "findings": [
    {
      "provider": "azure",
      "rule_id": "azure.unattached_managed_disk",
      "resource_type": "azure.managed_disk",
      "resource_id": "/subscriptions/abc.../disk-123",
      "region": "eastus",
      "confidence": "HIGH",
      "risk": "LOW",
      "detected_at": "2025-01-15T10:30:00Z",
      "details": {
        "resource_name": "disk-old-123",
        "subscription_id": "abc123...",
        "age_days": 47,
        "size_gb": 100
      }
    }
  ]
}
```

### CSV

```bash
cleancloud scan --provider azure --output csv --output-file results.csv
```

**Columns:** provider, rule_id, resource_type, resource_id, region, title, confidence, risk, detected_at

---

## CI/CD Integration

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Scan completed successfully, no policy violations |
| 1 | Configuration error or unexpected failure |
| 2 | Policy violation detected (findings present with enforcement flag) |
| 3 | Missing Azure credentials or insufficient permissions |

### Policy Enforcement

**Informational mode (default):**
```bash
cleancloud scan --provider azure
# Exit code 0 even if findings exist
```

**Fail on HIGH confidence findings (recommended):**
```bash
cleancloud scan --provider azure --fail-on-confidence HIGH
# Exit code 2 if any HIGH confidence findings exist
```

**Fail on any findings (strict):**
```bash
cleancloud scan --provider azure --fail-on-findings
# Exit code 2 if any findings exist (not recommended - too noisy)
```

### GitHub Actions Example

```yaml
name: CleanCloud Azure Scan

on:
  pull_request:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - name: Run CleanCloud scan
        env:
          AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
        run: |
          pip install cleancloud
          cleancloud scan --provider azure \
            --output json --output-file results.json \
            --fail-on-confidence HIGH

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: cleancloud-results
          path: results.json
```

### Azure DevOps Example

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'

- script: |
    pip install cleancloud
    cleancloud scan --provider azure --output json --output-file results.json --fail-on-confidence HIGH
  displayName: 'Run CleanCloud Scan'
  env:
    AZURE_CLIENT_ID: $(AZURE_CLIENT_ID)
    AZURE_TENANT_ID: $(AZURE_TENANT_ID)
    AZURE_CLIENT_SECRET: $(AZURE_CLIENT_SECRET)

- task: PublishBuildArtifacts@1
  condition: always()
  inputs:
    pathToPublish: 'results.json'
    artifactName: 'cleancloud-results'
```

---

## Troubleshooting

### "Missing Azure environment variables for authentication"

**Cause:** Required environment variables not set.

**Solution:**
```bash
# Verify variables are set
echo $AZURE_CLIENT_ID
echo $AZURE_TENANT_ID
echo $AZURE_CLIENT_SECRET

# If not, export them
export AZURE_CLIENT_ID="..."
export AZURE_TENANT_ID="..."
export AZURE_CLIENT_SECRET="..."
```

### "Azure authentication failed"

**Cause:** Invalid service principal credentials.

**Solution:**
1. Verify credentials are correct:
   ```bash
   az login --service-principal \
     -u $AZURE_CLIENT_ID \
     -p $AZURE_CLIENT_SECRET \
     --tenant $AZURE_TENANT_ID
   ```
2. If login fails, recreate service principal
3. Update environment variables with new credentials

### "No accessible Azure subscriptions found"

**Cause:** Service principal lacks Reader role on any subscription.

**Solution:**
```bash
# List current role assignments
az role assignment list --assignee $AZURE_CLIENT_ID

# Assign Reader role if missing
az role assignment create \
  --assignee $AZURE_CLIENT_ID \
  --role "Reader" \
  --scope /subscriptions/{subscription-id}
```

### "Missing required Azure permission: Microsoft.Compute/disks/read"

**Cause:** Service principal has insufficient RBAC permissions.

**Solution:**
1. Run `cleancloud doctor --provider azure` to validate permissions
2. Ensure Reader role is assigned (see RBAC Permissions section)
3. Wait 5-10 minutes for RBAC propagation
4. Retry scan

### "Rate limit exceeded"

**Cause:** Too many API requests in short time period.

**Solution:**
- CleanCloud automatically handles pagination
- Azure rate limits are generous for read operations
- If rate-limited, wait 5-10 minutes and retry
- Consider adding `--region` filter to reduce scope

---

## Design Philosophy

CleanCloud for Azure follows these principles:

1. **Age-based confidence** - Resources must exist for 7-14+ days before flagging
2. **Multiple signals preferred** - Combine attachment state + age when possible
3. **Explicit confidence levels** - Always state LOW/MEDIUM/HIGH confidence
4. **Review-only recommendations** - Never justify automated deletion

These principles make CleanCloud safe for:
- Production Azure subscriptions
- Regulated environments (HIPAA, SOC2, ISO 27001)
- Security-reviewed CI/CD pipelines
- Multi-tenant infrastructure

---

## Supported Azure Services

| Service | Resources | Status |
|---------|-----------|--------|
| Compute | Managed disks | ✅ Supported |
| Compute | Managed disk snapshots | ✅ Supported |
| Network | Public IP addresses | ✅ Supported |
| Compute | VM images | 🔜 Planned |
| Network | Network interfaces (NICs) | 🔜 Planned |
| Network | Network security groups | 🔜 Planned |
| Storage | Blob storage containers | 🔜 Planned |

---

## Azure vs AWS Differences

### Authentication
- **AWS:** Uses IAM roles/users with access keys
- **Azure:** Uses service principals with client secrets

### Regions
- **AWS:** Must specify region(s) to scan
- **Azure:** Resources discovered across all locations by default

### Permissions Model
- **AWS:** IAM policies with fine-grained actions
- **Azure:** RBAC roles (Reader role typically sufficient)

### Resource Naming
- **AWS:** Short resource IDs (e.g., `vol-abc123`)
- **Azure:** Full ARM resource IDs (e.g., `/subscriptions/.../disks/...`)

---

## Next Steps

- Review detected findings: [Rule documentation](rules.md)
- Integrate with CI/CD: [CI/CD guide](ci.md)
- Configure AWS scanning: [AWS setup](aws.md)

---

## FAQ

**Q: Will CleanCloud delete my Azure resources?**  
A: No. CleanCloud is read-only and never modifies, deletes, or tags resources.

**Q: Does CleanCloud access Azure cost data?**  
A: No. CleanCloud does not require or access Azure Cost Management APIs.

**Q: Can I scan multiple subscriptions at once?**  
A: Yes. By default, CleanCloud scans all subscriptions accessible to the service principal. Use `AZURE_SUBSCRIPTION_ID` to limit to one.

**Q: Why do I need a service principal? Can't I use my Azure CLI login?**  
A: CleanCloud requires non-interactive authentication for CI/CD compatibility. Azure CLI authentication is not supported.

**Q: Can I customize age thresholds for disks/snapshots?**  
A: Not yet. Conservative defaults (7-14 days for disks, 30-90 days for snapshots) are hardcoded at MVP stage. Configuration support is planned.

**Q: Why so few rules compared to AWS?**  
A: CleanCloud prioritizes high-signal, low-risk rules over breadth. Azure support was added in MVP; more rules will follow the same safety bar.

**Q: Does CleanCloud support Azure Government Cloud?**  
A: Not tested. Standard commercial Azure only at MVP stage.

**Q: What about Azure DevOps integration?**  
A: Yes! See the CI/CD Integration section for Azure Pipelines example.