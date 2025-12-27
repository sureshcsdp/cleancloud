# AWS Setup & Rules

AWS-specific authentication, IAM policies, region handling, and detailed rule specifications.

> **For general usage:** See [README.md](../README.md)  
> **For CI/CD integration:** See [ci.md](ci.md)

---

## Authentication

### 1. OIDC with IAM Roles (Recommended for CI/CD)

No credentials stored, temporary tokens only, SOC2 compliant.

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "repo:YOUR_ORG/YOUR_REPO:ref:refs/heads/main"
      }
    }
  }]
}
```

Replace `YOUR_ACCOUNT_ID`, `YOUR_ORG`, and `YOUR_REPO` with your values.

**Example:**
```json
"token.actions.githubusercontent.com:sub": "repo:acme-corp/infrastructure:ref:refs/heads/main"
```

This restricts the role to only be assumable from your team's specific repository.

**GitHub Actions:**
```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::YOUR_ACCOUNT_ID:role/CleanCloudScanner
    aws-region: us-east-1

- name: Run CleanCloud
  run: |
    pip install cleancloud
    cleancloud scan --provider aws
```

### 2. AWS CLI Profiles (Local Development)

```bash
aws configure --profile cleancloud
cleancloud scan --provider aws --profile cleancloud
```

### 3. Environment Variables

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
cleancloud scan --provider aws
```

---

## IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2ReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVolumes",
        "ec2:DescribeSnapshots",
        "ec2:DescribeInstances",
        "ec2:DescribeRegions",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogsReadOnly",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:ListTagsLogGroup"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3ReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:GetBucketTagging",
        "s3:GetBucketLocation"
      ],
      "Resource": "*"
    },
    {
      "Sid": "STSIdentity",
      "Effect": "Allow",
      "Action": "sts:GetCallerIdentity",
      "Resource": "*"
    }
  ]
}
```

**Does NOT allow:** Delete*, Modify*, Tag*, Attach*, billing access.

---

## Region Behavior

CleanCloud automatically detects which regions to scan.

**Auto-detect (default):**
```bash
cleancloud scan --provider aws
# Scans only regions with resources (3-5 typically)
```

**All regions:**
```bash
cleancloud scan --provider aws --all-regions
# Scans all enabled regions (25+)
```

**Specific regions:**
```bash
cleancloud scan --provider aws --regions us-east-1,us-west-2
```

### Service-Specific Behavior

**Regional services** (query each region):
- EC2, EBS, RDS, Lambda, DynamoDB, CloudWatch Logs

**Global services** (query once from us-east-1):
- S3 buckets (list is global, each bucket has a region)
- IAM (truly global)

CleanCloud handles this automatically - no duplicate findings, 60% faster scans.

---

## Rules (4 Total)

### 1. Unattached EBS Volumes

**Rule ID:** `aws.ebs.volume.unattached`

**Detects:** Volumes not attached to any instance

**Confidence:**
- HIGH: Unattached ≥ 14 days
- MEDIUM: Unattached 7-13 days
- Not flagged: < 7 days

**Required permission:** `ec2:DescribeVolumes`

---

### 2. Old EBS Snapshots

**Rule ID:** `aws.ebs.snapshot.old`

**Detects:** Snapshots ≥ 365 days old

**Confidence:**
- HIGH: Age ≥ 365 days

**Limitations:** Does NOT check AMI linkage (by design, to avoid false positives)

**Required permission:** `ec2:DescribeSnapshots`

---

### 3. CloudWatch Log Groups (Infinite Retention)

**Rule ID:** `aws.cloudwatch.logs.infinite_retention`

**Detects:** Log groups with no retention policy

**Confidence:**
- HIGH: No retention policy, ≥ 30 days old

**Required permission:** `logs:DescribeLogGroups`

---

### 4. Untagged Resources

**Rule ID:** `aws.resource.untagged`

**Detects:** Resources with zero tags

**Resources:** EBS volumes, S3 buckets, CloudWatch log groups

**Confidence:**
- MEDIUM: Zero tags (always MEDIUM)

**Required permissions:** `ec2:DescribeVolumes`, `s3:GetBucketTagging`, `logs:ListTagsLogGroup`

---

## Troubleshooting

**Credentials not found:**
```bash
aws sts get-caller-identity  # Verify credentials work
```

**Access denied:**
```bash
cleancloud doctor --provider aws  # Check permissions
```

**Missing findings:**
- Check you're scanning the right regions
- Resources may be excluded by age thresholds (volumes < 7 days, snapshots < 365 days)

**Rate limiting:**
- CleanCloud auto-handles with exponential backoff
- If persistent: scan fewer regions, wait 5-10 minutes

---

## Performance

| Regions | Scan Time |
|---------|-----------|
| 1 region | 15-30 sec |
| 3 regions (auto-detect) | 2-3 min |
| All regions (25+) | 8-10 min |

**API calls:** All free (read-only operations have no cost)

---

## Security

✅ Use OIDC for CI/CD (no stored credentials)  
✅ Use least-privilege IAM policy (CleanCloudReadOnly)  
✅ Enable CloudTrail logging  
✅ Restrict OIDC trust to specific repos

❌ Don't use long-lived access keys in CI/CD  
❌ Don't use overly broad policies (e.g., ReadOnlyAccess)

---

## Supported Regions

All AWS commercial regions. Auto-detects opt-in status.

**Not tested:** GovCloud, China regions.