# CleanCloud IAM Proof Pack

This directory contains the **IAM Proof Pack** - a collection of artifacts for security teams to verify CleanCloud's read-only security model.

## Contents

| File | Description |
|------|-------------|
| `aws-readonly-policy.json` | AWS IAM policy with minimum required read-only permissions |
| `verify-aws-policy.sh` | Script to verify AWS IAM policy contains no write/delete permissions |
| `verify-azure-role.sh` | Script to verify Azure role is read-only |

---

## Usage

### 1. AWS IAM Policy Verification

**Verify the policy file:**

```bash
./verify-aws-policy.sh aws-readonly-policy.json
```

**Expected output:**
```
🔍 Verifying AWS IAM Policy: aws-readonly-policy.json

✅ PASS: No write/delete/tag permissions found

Allowed actions:
ec2:DescribeInstances
ec2:DescribeRegions
ec2:DescribeSnapshots
ec2:DescribeVolumes
ec2:DescribeTags
logs:DescribeLogGroups
logs:DescribeLogStreams
logs:GetLogEvents
s3:GetBucketTagging
s3:ListAllMyBuckets
sts:GetCallerIdentity
```

**Create IAM policy in AWS:**

```bash
# Create IAM policy
aws iam create-policy \
  --policy-name CleanCloudReadOnly \
  --policy-document file://aws-readonly-policy.json

# Attach to existing role (e.g., OIDC role)
aws iam attach-role-policy \
  --role-name CleanCloudCIReadOnly \
  --policy-arn arn:aws:iam::123456789012:policy/CleanCloudReadOnly
```

---

### 2. Azure Role Verification

**Verify the Reader role:**

```bash
# Login to Azure first
az login

# Run verification script
./verify-azure-role.sh Reader
```

**Expected output:**
```
🔍 Verifying Azure Role: Reader

Fetching role definition...
✅ PASS: Role is read-only

Allowed actions:
*/read
```

**Assign Reader role to service principal:**

```bash
az role assignment create \
  --assignee <service-principal-id> \
  --role "Reader" \
  --scope /subscriptions/<subscription-id>
```

---

## For Security Reviews

This IAM Proof Pack can be provided to security teams for:

- **Policy review** - Verify no write/delete/tag permissions
- **Compliance audits** - Evidence of least privilege principle
- **Penetration testing** - Test that CleanCloud cannot mutate resources
- **Risk assessment** - Demonstrate limited blast radius

---

## Automated Testing

These policies are also validated in CI/CD:

```bash
# Run safety regression tests
pytest cleancloud/safety/aws/test_iam_policy_readonly.py -v
pytest cleancloud/safety/azure/test_role_definition_readonly.py -v
```

See [`docs/safety.md`](../docs/safety.md) for details on automated safety testing.

---

## Additional Resources

- [Information Security Readiness Guide](../docs/infosec-readiness.md) - Comprehensive security documentation
- [AWS Setup Guide](../docs/aws.md) - AWS authentication and IAM setup
- [Azure Setup Guide](../docs/azure.md) - Azure authentication and RBAC setup
- [Safety Documentation](../docs/safety.md) - Multi-layer safety regression tests

---

**Questions?**

Email: suresh@getcleancloud.com
GitHub Issues: https://github.com/cleancloud-io/cleancloud/issues
