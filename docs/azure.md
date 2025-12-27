# Azure Setup & Rules

Azure-specific authentication, RBAC permissions, and detailed rule specifications.

> **For general usage:** See [README.md](../README.md)  
> **For CI/CD integration:** See [ci.md](ci.md)

---

## Authentication

### 1. Azure OIDC with Workload Identity (Recommended for CI/CD)

**Microsoft Entra ID Workload Identity Federation** - No client secrets, temporary tokens only.

**Benefits:**
- No `AZURE_CLIENT_SECRET` stored
- Short-lived tokens (1 hour)
- Enterprise security compliant
- Consistent with AWS OIDC approach

**Setup Steps:**

**Step 1:** Create App Registration
```bash
az ad app create --display-name "CleanCloudScanner"
```

**Step 2:** Create Service Principal
```bash
az ad sp create --id <APP_ID>
```

**Step 3:** Configure Federated Identity Credential
```bash
az ad app federated-credential create \
  --id <APP_ID> \
  --parameters '{
    "name": "CleanCloudGitHub",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:YOUR_ORG/YOUR_REPO:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

Replace `YOUR_ORG/YOUR_REPO` with your repository.

**Step 4:** Assign Reader Role
```bash
az role assignment create \
  --assignee <APP_ID> \
  --role "Reader" \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID
```

**Step 5:** GitHub Actions Usage
```yaml
permissions:
  id-token: write
  contents: read

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      
      - name: Run CleanCloud
        run: |
          pip install cleancloud
          cleancloud scan --provider azure
```

**Required GitHub Secrets:**
- `AZURE_CLIENT_ID` - App registration application ID
- `AZURE_TENANT_ID` - Azure tenant ID
- `AZURE_SUBSCRIPTION_ID` - Subscription to scan

**No secret needed:** `AZURE_CLIENT_SECRET` ✅

---

### 2. Azure CLI (Local Development)

```bash
# Login
az login

# Set subscription
az account set --subscription YOUR_SUBSCRIPTION_ID

# Run scan
cleancloud scan --provider azure
```

CleanCloud automatically uses your active Azure CLI session.

---

## RBAC Permissions

### Reader Role (Recommended)

Built-in **Reader** role provides all required permissions:

```bash
az role assignment create \
  --assignee <APP_ID> \
  --role "Reader" \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID
```

**What Reader allows:**
- ✅ `Microsoft.Compute/disks/read`
- ✅ `Microsoft.Compute/snapshots/read`
- ✅ `Microsoft.Network/publicIPAddresses/read`
- ✅ `Microsoft.Resources/subscriptions/read`

**What Reader does NOT allow:**
- ❌ Delete operations (`*/delete`)
- ❌ Modification operations (`*/write`)
- ❌ Tagging operations (`Microsoft.Resources/tags/*`)
- ❌ Billing data access (`Microsoft.CostManagement/*`)

### Custom Role (Optional Least-Privilege)

```json
{
  "Name": "CleanCloud Scanner",
  "Description": "Minimal read-only access for CleanCloud",
  "Actions": [
    "Microsoft.Compute/disks/read",
    "Microsoft.Compute/snapshots/read",
    "Microsoft.Network/publicIPAddresses/read",
    "Microsoft.Resources/subscriptions/read"
  ],
  "NotActions": [],
  "AssignableScopes": [
    "/subscriptions/YOUR_SUBSCRIPTION_ID"
  ]
}
```

Create and assign:
```bash
az role definition create --role-definition cleancloud-role.json

az role assignment create \
  --assignee <APP_ID> \
  --role "CleanCloud Scanner" \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID
```

---

## Subscription Scanning

### Single Subscription (Default)

```bash
# Specify via environment
export AZURE_SUBSCRIPTION_ID="12345678-1234-1234-1234-123456789abc"
cleancloud scan --provider azure

# Or via CLI login
az account set --subscription YOUR_SUBSCRIPTION_ID
cleancloud scan --provider azure
```

### All Accessible Subscriptions

```bash
# Remove AZURE_SUBSCRIPTION_ID
unset AZURE_SUBSCRIPTION_ID
cleancloud scan --provider azure
```

CleanCloud scans all subscriptions the service principal can access.

### Region Filtering

```bash
# Scan only East US resources
cleancloud scan --provider azure --region eastus

# Scan only West Europe resources
cleancloud scan --provider azure --region westeurope
```

---

## Azure Rules (4 Total)

### 1. Unattached Managed Disks

**Rule ID:** `azure.unattached_managed_disk`

**Detects:** Disks not attached to any VM

**Confidence:**
- HIGH: Unattached ≥ 14 days
- MEDIUM: Unattached 7-13 days
- Not flagged: < 7 days

**Detection logic:**
```python
if disk.managed_by is None:  # Not attached
    age_days = calculate_age(disk.time_created)
    if age_days >= 14:
        confidence = "HIGH"
    elif age_days >= 7:
        confidence = "MEDIUM"
```

**Required permission:** `Microsoft.Compute/disks/read`

**Common causes:**
- Disks from deleted VMs
- Failed deployments
- Autoscaling cleanup gaps

---

### 2. Old Managed Disk Snapshots

**Rule ID:** `azure.old_snapshot`

**Detects:** Snapshots older than configured thresholds

**Confidence:**
- HIGH: Age ≥ 90 days
- MEDIUM: Age ≥ 30 days

**Limitations:** Does NOT check if snapshot is referenced by images (by design, avoids false positives)

**Required permission:** `Microsoft.Compute/snapshots/read`

**Common causes:**
- Snapshots from backup jobs
- Over-retention without lifecycle policies
- Snapshots from deleted disks

---

### 3. Untagged Resources

**Rule ID:** `azure.untagged_resource`

**Detects:** Resources with zero tags

**Resources:** Managed disks, snapshots (7+ days old)

**Confidence:**
- MEDIUM: Untagged disk that's also unattached
- LOW: Untagged snapshot or attached disk

**Required permissions:**
- `Microsoft.Compute/disks/read`
- `Microsoft.Compute/snapshots/read`

---

### 4. Unused Public IP Addresses

**Rule ID:** `azure.public_ip_unused`

**Detects:** Public IPs not attached to any network interface

**Confidence:**
- HIGH: Not attached (deterministic state)

**Detection logic:**
```python
if public_ip.ip_configuration is None:
    confidence = "HIGH"
```

**Required permission:** `Microsoft.Network/publicIPAddresses/read`

**Note:** Unused public IPs incur charges even when unattached.

---

## Troubleshooting

### "Missing Azure environment variables"

**For OIDC (GitHub Actions):**
```yaml
# Ensure these secrets are set
secrets:
  AZURE_CLIENT_ID
  AZURE_TENANT_ID
  AZURE_SUBSCRIPTION_ID
```

**For local CLI:**
```bash
# Verify you're logged in
az account show
```

### "Azure authentication failed"

**For OIDC:**
1. Verify federated credential subject matches your repo:
   ```bash
   az ad app federated-credential list --id <APP_ID>
   ```
2. Ensure `subject` is: `repo:YOUR_ORG/YOUR_REPO:ref:refs/heads/main`

**For CLI:**
```bash
# Re-login
az login
az account set --subscription YOUR_SUBSCRIPTION_ID
```

### "No accessible subscriptions"

```bash
# Check role assignments
az role assignment list --assignee <APP_ID>

# Assign Reader role
az role assignment create \
  --assignee <APP_ID> \
  --role "Reader" \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID
```

### "Missing permission: Microsoft.Compute/disks/read"

```bash
# Verify Reader role is assigned
az role assignment list \
  --assignee <APP_ID> \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID

# Wait 5-10 minutes for RBAC propagation
```

---

## Azure vs AWS Differences

| Aspect | AWS | Azure |
|--------|-----|-------|
| **OIDC Setup** | IAM role trust policy | Federated identity credential |
| **Permissions** | IAM policies | RBAC roles |
| **Regions** | Must specify or auto-detect | All locations by default |
| **Resource IDs** | Short (e.g., `vol-abc123`) | Full ARM paths |
| **Authentication** | OIDC or access keys | OIDC or client secrets |

---

## Performance

| Subscriptions | Resources | Scan Time |
|---------------|-----------|-----------|
| 1 subscription | ~500 resources | 30-60 sec |
| 1 subscription | ~2,000 resources | 2-3 min |
| 3 subscriptions | ~6,000 resources | 5-8 min |

**API calls:** All free (read-only operations have no cost)

---

## Security Best Practices

✅ Use OIDC for CI/CD (no stored secrets)  
✅ Use Reader role (least privilege)  
✅ Restrict federated credential to specific repo/branch  
✅ Monitor Azure Activity Log for CleanCloud actions  
✅ Use separate service principals per environment

❌ Don't use client secrets in CI/CD  
❌ Don't grant Contributor role  
❌ Don't share credentials across teams

---

## Supported Azure Clouds

- ✅ Azure Commercial
- ⚠️ Azure Government (not tested)
- ⚠️ Azure China (not tested)

---

## Next Steps

- **CI/CD Integration:** [ci.md](ci.md)
- **Rule Details:** [rules.md](rules.md)
- **AWS Setup:** [aws.md](aws.md)