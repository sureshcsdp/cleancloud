# CleanCloud Rules

This document describes all hygiene rules implemented by CleanCloud across AWS and Azure.

---

## Design Principles

All CleanCloud rules follow these principles:

### 1. Read-Only Always
- Uses read-only cloud APIs exclusively
- No `Delete*`, `Modify*`, `Tag*`, or `Update*` operations
- Safe for production environments

### 2. Conservative by Default
- Multiple signals preferred over single indicators
- Age-based thresholds prevent false positives on temporary resources
- Prefer false negatives over false positives

### 3. Explicit Confidence Levels
Every finding includes a confidence level:
- **HIGH** - Multiple strong signals, very likely orphaned
- **MEDIUM** - Moderate signals, worth reviewing
- **LOW** - Weak signals, informational only

### 4. Review-Only Recommendations
- Findings are candidates for human review, not automated action
- Clear reasoning provided for each finding
- Detailed metadata included for investigation
- No rule should justify deletion on its own

### 5. IaC-Aware
- Designed for elastic, automated infrastructure
- Age thresholds account for autoscaling and deployment churn
- Respects that resources may be temporarily unattached

---

## Rule Lifecycle

### Rule Maturity Stages

**MVP** - Implemented with conservative defaults, proven safe  
**Planned** - Designed but not yet implemented  
**Considered** - Under evaluation for safety and signal quality

### Rule Stability Guarantee

Once a rule reaches MVP status:
- ✅ Rule ID remains stable
- ✅ Confidence semantics unchanged
- ✅ Backwards compatibility preserved
- ✅ Schema additions only (no breaking changes)

This guarantees trust for long-running CI/CD integrations.

---

## AWS Rules

### 1. Unattached EBS Volumes

**Rule ID:** `aws.ebs.volume.unattached`  
**Status:** MVP  
**Confidence:** HIGH  
**Risk:** LOW

**What it detects:**  
EBS volumes not attached to any EC2 instance.

**Detection signal:**
```
volume.state != "in-use"
```

**Why this is safe:**
- Volume attachment state is deterministic
- No age thresholds needed (state alone is reliable)
- No heuristics or inference required

**Common causes:**
- Volumes from terminated EC2 instances
- Volumes created by autoscaling groups during scale-down
- Failed deployments or rollbacks
- Manual detachment without deletion

**What to review:**
- Check if volume contains data needed for recovery
- Verify volume is not part of disaster recovery plan
- Confirm volume tags don't indicate "reserved for future use"

**Required IAM permissions:**
- `ec2:DescribeVolumes`

**Example finding:**
```json
{
  "rule_id": "aws.ebs.volume.unattached",
  "resource_id": "vol-0abc123def456789",
  "region": "us-east-1",
  "confidence": "HIGH",
  "details": {
    "size_gb": 100,
    "state": "available",
    "create_time": "2024-11-15T10:30:00Z"
  }
}
```

---

### 2. Old EBS Snapshots

**Rule ID:** `aws.ebs.snapshot.old`  
**Status:** MVP  
**Confidence:** HIGH  
**Risk:** LOW

**What it detects:**  
EBS snapshots older than 90 days.

**Detection signals:**
- Snapshot age ≥ 90 days
- Owned by current account (`OwnerIds=["self"]`)

**Why this is safe:**
- 90-day threshold is conservative
- Only flags snapshots owned by the scanning account
- Does NOT attempt to detect AMI linkage (to avoid false positives)

**Conservative approach:**  
CleanCloud intentionally does NOT check if snapshots are referenced by AMIs at MVP stage. This prevents false positives but may miss some snapshots that should be retained. AMI linkage detection is a planned enhancement.

**Common causes:**
- Snapshots from CI/CD backup jobs
- Over-retention without lifecycle policies
- Snapshots from deleted volumes
- Manual backups never cleaned up

**What to review:**
- Verify snapshot is not required for compliance retention
- Check if snapshot is documented in disaster recovery plans
- Confirm snapshot is not being used for AMI creation

**Required IAM permissions:**
- `ec2:DescribeSnapshots`

**Configuration:**  
Default threshold: 90 days (not yet configurable)

**Example finding:**
```json
{
  "rule_id": "aws.ebs.snapshot.old",
  "resource_id": "snap-0abc123def456789",
  "region": "us-west-2",
  "confidence": "HIGH",
  "details": {
    "age_days": 127,
    "volume_id": "vol-xyz789",
    "start_time": "2024-08-10T05:00:00Z"
  }
}
```

---

### 3. CloudWatch Log Groups (Infinite Retention)

**Rule ID:** `aws.cloudwatch.logs.infinite_retention`  
**Status:** MVP  
**Confidence:** HIGH  
**Risk:** LOW

**What it detects:**  
CloudWatch log groups with no retention policy configured (logs never expire).

**Detection signal:**
```
log_group.retentionInDays == null
```

**Why this is safe:**
- Only flags missing retention policy
- Does NOT infer ingestion activity (to avoid false positives)
- Does NOT recommend specific retention periods

**Conservative approach:**  
CleanCloud does NOT attempt to detect "inactive" log groups based on last ingestion time at MVP stage. This would require additional API calls and could produce false positives for legitimately idle services.

**Common causes:**
- Log groups created by Lambda/ECS without explicit retention
- Log groups from deleted services still accumulating storage costs
- Default CloudWatch behavior (no automatic expiration)

**What to review:**
- Verify log group is still used by an active service
- Check if logs are required for compliance audit trails
- Consider setting appropriate retention period (7, 30, 90, 365 days)

**Required IAM permissions:**
- `logs:DescribeLogGroups`

**Example finding:**
```json
{
  "rule_id": "aws.cloudwatch.logs.infinite_retention",
  "resource_id": "/aws/lambda/old-function",
  "region": "eu-west-1",
  "confidence": "HIGH",
  "details": {
    "stored_bytes": 15728640,
    "retention_days": null
  }
}
```

---

### 4. Untagged Resources

**Rule ID:** `aws.resource.untagged`  
**Status:** MVP  
**Confidence:** MEDIUM  
**Risk:** LOW

**What it detects:**  
Resources with no tags at all.

**Resources scanned:**
- EBS volumes
- S3 buckets
- CloudWatch log groups

**Detection signal:**
```
resource.tags == [] OR resource.tags == null
```

**Why MEDIUM confidence:**
- Lack of tags alone doesn't indicate orphaned status
- Some organizations don't mandate tagging
- Tags may be managed externally (e.g., via IaC)

**Why this matters:**
- Untagged resources are difficult to attribute to owners
- Makes cost allocation and showback impossible
- High risk for becoming orphaned over time
- Tag hygiene is foundational for cloud governance

**Common causes:**
- Resources created manually via console
- Resources created before tagging policies were enforced
- Resources created by third-party tools
- Legacy infrastructure

**What to review:**
- Identify resource owner through AWS CloudTrail (who created it)
- Apply baseline tags: Owner, Environment, CostCenter, Project
- Consider implementing tag policies via AWS Organizations

**Required IAM permissions:**
- `ec2:DescribeVolumes`
- `s3:ListAllMyBuckets`
- `s3:GetBucketTagging`
- `logs:DescribeLogGroups`

**Example finding:**
```json
{
  "rule_id": "aws.resource.untagged",
  "resource_type": "ebs_volume",
  "resource_id": "vol-0abc123def456789",
  "region": "us-east-1",
  "confidence": "MEDIUM",
  "details": {
    "size_gb": 50,
    "availability_zone": "us-east-1a"
  }
}
```

---

## Azure Rules

### 5. Unattached Managed Disks

**Rule ID:** `azure.unattached_managed_disk`  
**Status:** MVP  
**Confidence:** HIGH (14+ days), MEDIUM (7-13 days)  
**Risk:** LOW

**What it detects:**  
Managed disks not attached to any virtual machine and older than 7 days.

**Detection signals:**
- `disk.managed_by == null` (not attached to VM)
- Disk age ≥ 14 days → HIGH confidence
- Disk age ≥ 7 days → MEDIUM confidence
- Disk age < 7 days → Not flagged

**Why age thresholds:**
- IaC tools and autoscaling create temporary unattached disks
- 7-day minimum prevents false positives on legitimate temporary resources
- 14-day threshold provides very high confidence

**Common causes:**
- Disks from deleted virtual machines
- Failed VM deployments
- Autoscaling group scale-down events
- Disk resize or migration operations

**What to review:**
- Check disk tags for owner information
- Verify disk is not part of planned VM deployment
- Confirm disk doesn't contain data needed for recovery

**Required Azure permissions:**
- `Microsoft.Compute/disks/read`

**Example finding:**
```json
{
  "rule_id": "azure.unattached_managed_disk",
  "resource_id": "/subscriptions/.../disks/disk-old-123",
  "region": "eastus",
  "confidence": "HIGH",
  "details": {
    "resource_name": "disk-old-123",
    "age_days": 47,
    "size_gb": 128,
    "sku": "Premium_LRS"
  }
}
```

---

### 6. Old Managed Disk Snapshots

**Rule ID:** `azure.old_snapshot`  
**Status:** MVP  
**Confidence:** HIGH (90+ days), MEDIUM (30-89 days)  
**Risk:** LOW

**What it detects:**  
Managed disk snapshots older than 30 days.

**Detection signals:**
- Snapshot age ≥ 90 days → HIGH confidence
- Snapshot age ≥ 30 days → MEDIUM confidence
- Snapshot age < 30 days → Not flagged

**Why this is safe:**
- Conservative 30/90 day thresholds
- Age-based only, no complex heuristics

**Conservative approach:**  
CleanCloud does NOT attempt to detect if snapshots are referenced by VM images at MVP stage. This prevents false positives but may miss some snapshots that should be retained.

**Common causes:**
- Snapshots from backup automation
- Over-retention without lifecycle policies
- Snapshots from deleted disks
- Manual backups never cleaned up

**What to review:**
- Verify snapshot is not required for compliance
- Check if snapshot is needed for disaster recovery
- Confirm snapshot is not being used for image creation

**Required Azure permissions:**
- `Microsoft.Compute/snapshots/read`

**Example finding:**
```json
{
  "rule_id": "azure.old_snapshot",
  "resource_id": "/subscriptions/.../snapshots/snap-backup-2024-08",
  "region": "westeurope",
  "confidence": "HIGH",
  "details": {
    "resource_name": "snap-backup-2024-08",
    "age_days": 125,
    "disk_size_gb": 256,
    "sku": "Standard_LRS"
  }
}
```

---

### 7. Untagged Resources

**Rule ID:** `azure.untagged_resource`  
**Status:** MVP  
**Confidence:** MEDIUM (unattached disks), LOW (other resources)  
**Risk:** LOW

**What it detects:**  
Resources with no tags at all.

**Resources scanned:**
- Managed disks
- Managed disk snapshots (7+ days old only)

**Detection signals:**
- `resource.tags == null OR resource.tags == {}`
- For disks: MEDIUM confidence if also unattached, otherwise LOW
- For snapshots: LOW confidence (with 7+ day age filter)

**Why confidence varies:**
- Unattached + untagged disk = higher risk (MEDIUM)
- Tagged resources easier to track and attribute

**Why this matters:**
- Untagged resources are difficult to attribute to owners or cost centers
- Makes Azure cost allocation impossible
- Tag hygiene is foundational for cloud governance

**Common causes:**
- Resources created manually via portal
- Resources created before tagging policies
- Legacy infrastructure
- Resources created by third-party tools

**What to review:**
- Identify resource owner through Azure Activity Log
- Apply baseline tags: Owner, Environment, CostCenter, Project
- Consider implementing Azure Policy for tag enforcement

**Required Azure permissions:**
- `Microsoft.Compute/disks/read`
- `Microsoft.Compute/snapshots/read`

**Example finding:**
```json
{
  "rule_id": "azure.untagged_resource",
  "resource_type": "azure.managed_disk",
  "resource_id": "/subscriptions/.../disks/unnamed-disk-42",
  "region": "eastus",
  "confidence": "MEDIUM",
  "details": {
    "resource_name": "unnamed-disk-42",
    "tags_present": false,
    "managed_by": null
  }
}
```

---

### 8. Unused Public IP Addresses

**Rule ID:** `azure.public_ip_unused`  
**Status:** MVP  
**Confidence:** HIGH  
**Risk:** LOW

**What it detects:**  
Public IP addresses not attached to any network interface.

**Detection signal:**
```
public_ip.ip_configuration == null
```

**Why this is safe:**
- Attachment state is deterministic
- No age thresholds needed
- No heuristics required

**Why this matters:**
- Unused public IPs incur Azure charges even when unattached
- Security best practice: minimize exposed IP address inventory

**Common causes:**
- IPs from deleted virtual machines
- IPs from deleted load balancers or application gateways
- Reserved IPs no longer in use
- Failed deployments

**What to review:**
- Verify IP is not reserved for planned deployment
- Check if IP is documented in networking diagrams
- Confirm IP is not being used for DNS or firewall rules

**Required Azure permissions:**
- `Microsoft.Network/publicIPAddresses/read`

**Example finding:**
```json
{
  "rule_id": "azure.public_ip_unused",
  "resource_id": "/subscriptions/.../publicIPAddresses/unused-ip-47",
  "region": "westus",
  "confidence": "HIGH",
  "details": {
    "resource_name": "unused-ip-47",
    "attached": false,
    "ip_address": "40.112.45.123"
  }
}
```

---

## Planned Rules

These rules are designed but not yet implemented. Each will follow the same conservative design principles.

### AWS (Planned)

**Unused Elastic IP Addresses**
- Rule ID: `aws.ec2.eip.unused`
- Detection: Elastic IPs not associated with any instance or network interface
- Confidence: HIGH
- Rationale: Unused EIPs incur charges and increase attack surface

**Old AMIs**
- Rule ID: `aws.ec2.ami.old`
- Detection: AMIs older than 180 days with no recent launches
- Confidence: MEDIUM
- Rationale: Old AMIs accumulate storage costs

**Empty Security Groups**
- Rule ID: `aws.ec2.security_group.empty`
- Detection: Security groups with no attached instances or interfaces
- Confidence: MEDIUM
- Rationale: Unused security groups complicate network governance

**Unused RDS Snapshots**
- Rule ID: `aws.rds.snapshot.old`
- Detection: Manual RDS snapshots older than 90 days
- Confidence: HIGH
- Rationale: Similar to EBS snapshots, accumulate costs over time

### Azure (Planned)

**Unused Network Interfaces (NICs)**
- Rule ID: `azure.network_interface.unused`
- Detection: NICs not attached to any VM
- Confidence: HIGH (14+ days)
- Rationale: Unused NICs indicate deleted or failed VMs

**Old VM Images**
- Rule ID: `azure.vm_image.old`
- Detection: Custom VM images older than 180 days
- Confidence: MEDIUM
- Rationale: Similar to AWS AMIs

**Empty Network Security Groups**
- Rule ID: `azure.nsg.empty`
- Detection: NSGs with no attached subnets or NICs
- Confidence: MEDIUM
- Rationale: Unused NSGs complicate network governance

---

## Rules NOT Planned

CleanCloud will NOT implement rules for:

### Cost Optimization
- Rightsizing recommendations
- Reserved instance analysis
- Savings plan suggestions
- Spot instance opportunities

**Why:** CleanCloud is focused on hygiene, not FinOps. Cost tools already exist.

### Remediation / Automation
- Automatic deletion
- Automatic tagging
- Automatic attachment
- Policy enforcement

**Why:** CleanCloud is review-only. Automation removes human oversight and increases risk.

### Active Services
- Running instances/VMs
- Active databases
- In-use load balancers
- Production workloads

**Why:** CleanCloud focuses on orphaned resources, not optimizing active services.

---

## Why So Few Rules?

CleanCloud intentionally maintains a small, high-quality rule set because:

1. **Quality over quantity** - 10 reliable rules > 100 noisy ones
2. **Trust is earned slowly** - Each rule must prove its value
3. **Safety first** - No rule should cause production incidents
4. **Clear value proposition** - Every rule must save meaningful time/cost

### Rule Addition Criteria

A new rule is only added if it meets ALL of:
- ✅ Uses read-only APIs exclusively
- ✅ Has clear, measurable signals (not heuristics)
- ✅ Provides actionable findings (not informational noise)
- ✅ Applies to most organizations (not niche use cases)
- ✅ Can assign explicit confidence levels
- ✅ Has been validated in multiple environments

This restraint is **a feature, not a limitation**.

---

## Confidence Level Reference

### HIGH Confidence
- Multiple strong signals present
- Age thresholds exceeded significantly (14+ days for disks, 90+ days for snapshots)
- Deterministic attachment state (unattached, unused)
- Very likely orphaned or unnecessary

**Action:** High priority for review and potential cleanup

### MEDIUM Confidence
- Moderate signals present
- Age thresholds partially met (7-13 days for disks, 30-89 days for snapshots)
- Some ambiguity in resource state
- Worth investigating

**Action:** Medium priority for review, verify before cleanup

### LOW Confidence
- Weak or single signal only
- Informational finding
- May be legitimate active resource
- Requires deeper investigation

**Action:** Low priority, review during regular audits

---

## Using Rules in CI/CD

### Policy Enforcement Strategies

**Strategy 1: Block on HIGH confidence only (Recommended)**
```bash
cleancloud scan --fail-on-confidence HIGH
```
- ✅ Catches clear hygiene issues
- ✅ Low false positive rate
- ✅ Doesn't block on ambiguous findings

**Strategy 2: Block on MEDIUM or higher**
```bash
cleancloud scan --fail-on-confidence MEDIUM
```
- ⚠️ More aggressive
- ⚠️ May require tuning for your environment
- ⚠️ Higher false positive risk

**Strategy 3: Block on any finding (Not recommended)**
```bash
cleancloud scan --fail-on-findings
```
- ❌ Too noisy for most environments
- ❌ Blocks on LOW confidence findings
- ❌ Requires constant exceptions

### Recommended Approach

**Development/Staging:**
- Run informational scans (no --fail-on flags)
- Generate reports for manual review
- Build baseline understanding

**Production:**
- Start with `--fail-on-confidence HIGH`
- Monitor for false positives over 2-4 weeks
- Adjust threshold based on findings

---

## Next Steps

- **AWS Setup:** [aws.md](aws.md)
- **Azure Setup:** [azure.md](azure.md)
- **CI/CD Integration:** [ci.md](ci.md)

---

## Feedback

CleanCloud rules are designed based on real SRE team feedback. If you have suggestions for new rules or improvements to existing ones, please:

1. Ensure the rule meets the addition criteria above
2. Provide concrete examples of resources it would detect
3. Explain why existing tools don't address this use case
4. Demonstrate the rule can maintain HIGH/MEDIUM confidence levels

Submit feedback via GitHub issues with the label `rule-proposal