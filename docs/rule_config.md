# Rule Configuration Guide

Configure rule thresholds to match your organization's risk tolerance and environment requirements.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Methods](#configuration-methods)
- [Rule Configuration Reference](#rule-configuration-reference)
- [Common Use Cases](#common-use-cases)
- [CLI Examples](#cli-examples)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Create a Configuration File

Create `cleancloud.yaml` in your project directory:

```yaml
rules:
  aws:
    old_ebs_snapshots:
      days_old: 180  # Flag snapshots older than 6 months
      confidence:
        high: 365    # >1 year = HIGH confidence
        medium: 180  # >6 months = MEDIUM confidence
    
    unattached_volumes:
      confidence:
        high: 14   # Unattached >14 days = HIGH confidence
        medium: 7  # Unattached >7 days = MEDIUM confidence
  
  azure:
    unattached_disks:
      confidence:
        high: 14
        medium: 7
    
    old_snapshots:
      confidence:
        high: 90
        medium: 30
```

### 2. Run Scan

```bash
# CleanCloud automatically uses cleancloud.yaml in current directory
cleancloud scan --provider aws --region us-east-1

# Or specify a config file explicitly
cleancloud scan --provider aws --config prod.yaml
```

### 3. Override for One-Off Scans

```bash
# Override just one setting
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.old_ebs_snapshots.days_old=90
```

---

## Configuration Methods

CleanCloud supports **4 configuration methods** with the following priority (highest to lowest):

### Priority 1: CLI Overrides (Highest)

Override any setting via command-line flags:

```bash
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.old_ebs_snapshots.days_old=90 \
  --rule-config aws.unattached_volumes.confidence.high=30
```

**Use when:** One-off scans, testing different thresholds, CI/CD per-environment overrides

---

### Priority 2: Explicit Config File

Specify a config file with `--config`:

```bash
cleancloud scan --provider aws --config prod.yaml
cleancloud scan --provider azure --config dev.yaml
```

**Use when:** Multiple environments (prod/dev/test), team-shared configs

---

### Priority 3: Current Directory Config

CleanCloud automatically loads `./cleancloud.yaml` if it exists:

```bash
# Create in project root
cat > cleancloud.yaml << EOF
rules:
  aws:
    old_ebs_snapshots:
      days_old: 180
EOF

# Automatically used
cleancloud scan --provider aws --region us-east-1
```

**Use when:** Project-specific settings, version-controlled configs

---

### Priority 4: User Home Config

CleanCloud loads `~/.cleancloud/config.yaml` for user-wide defaults:

```bash
# Create user-wide config
mkdir -p ~/.cleancloud
cat > ~/.cleancloud/config.yaml << EOF
rules:
  aws:
    old_ebs_snapshots:
      days_old: 365  # Conservative defaults
EOF
```

**Use when:** Personal defaults, organization-wide baselines

---

### Priority 5: Built-in Defaults (Lowest)

If no config is provided, CleanCloud uses conservative built-in defaults:

```python
AWS:
  old_ebs_snapshots: 365 days
  unattached_volumes: HIGH=14 days, MEDIUM=7 days

Azure:
  unattached_disks: HIGH=14 days, MEDIUM=7 days
  old_snapshots: HIGH=90 days, MEDIUM=30 days
```

**Use when:** Getting started, no customization needed

---

## Rule Configuration Reference

### AWS Rules

#### `old_ebs_snapshots`

Find EBS snapshots older than threshold.

**Configuration:**

```yaml
rules:
  aws:
    old_ebs_snapshots:
      days_old: 365  # Minimum age to flag (default: 365)
      confidence:
        high: 365    # Age for HIGH confidence (default: 365)
        medium: 180  # Age for MEDIUM confidence (default: 180)
```

**How it works:**
- Snapshots older than `days_old` are flagged
- Confidence level determined by age:
    - `>= high` threshold → HIGH confidence
    - `>= medium` threshold → MEDIUM confidence
    - `< medium` threshold → LOW confidence

**CLI override:**

```bash
# Change minimum age
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.old_ebs_snapshots.days_old=90

# Change confidence thresholds
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.old_ebs_snapshots.confidence.high=180 \
  --rule-config aws.old_ebs_snapshots.confidence.medium=90
```

**Example scenarios:**

```yaml
# Conservative (production)
old_ebs_snapshots:
  days_old: 730      # 2 years
  confidence:
    high: 730
    medium: 365

# Aggressive (development)
old_ebs_snapshots:
  days_old: 30       # 1 month
  confidence:
    high: 90
    medium: 30

# Cost optimization
old_ebs_snapshots:
  days_old: 90       # 3 months
  confidence:
    high: 180
    medium: 90
```

---

#### `unattached_volumes`

Find EBS volumes not attached to instances.

**Configuration:**

```yaml
rules:
  aws:
    unattached_volumes:
      confidence:
        high: 14   # Unattached >14 days = HIGH (default: 14)
        medium: 7  # Unattached >7 days = MEDIUM (default: 7)
```

**How it works:**
- Volumes not attached to any instance are checked
- Confidence based on how long they've been unattached:
    - `>= high` days → HIGH confidence
    - `>= medium` days → MEDIUM confidence
    - `< medium` days → Not flagged (too recent)

**CLI override:**

```bash
# More aggressive
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.unattached_volumes.confidence.high=7 \
  --rule-config aws.unattached_volumes.confidence.medium=3

# More conservative
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.unattached_volumes.confidence.high=30 \
  --rule-config aws.unattached_volumes.confidence.medium=14
```

---

#### `infinite_log_retention`

Find CloudWatch log groups with infinite retention.

**Configuration:**

```yaml
rules:
  aws:
    infinite_log_retention:
      confidence:
        high: 30  # Log group >30 days old = HIGH (default: 30)
```

**How it works:**
- Log groups with infinite retention are flagged
- Confidence based on log group age:
    - `>= high` days old → HIGH confidence
    - `< high` days old → MEDIUM confidence (new groups get benefit of doubt)

**CLI override:**

```bash
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.infinite_log_retention.confidence.high=90
```

---

#### `untagged_resources`

Find AWS resources without tags.

**Configuration:**

```yaml
rules:
  aws:
    untagged_resources:
      min_age_days: 7  # Ignore resources <7 days old (default: 7)
```

**How it works:**
- Resources without any tags are flagged
- Resources newer than `min_age_days` are ignored (assume they're being set up)
- Confidence based on attachment state (unattached = higher confidence)

**CLI override:**

```bash
# Flag immediately (compliance focus)
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.untagged_resources.min_age_days=1

# More lenient (allow time for tagging)
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.untagged_resources.min_age_days=30
```

---

### Azure Rules

#### `unattached_disks`

Find Azure managed disks not attached to VMs.

**Configuration:**

```yaml
rules:
  azure:
    unattached_disks:
      confidence:
        high: 14   # Unattached >14 days = HIGH (default: 14)
        medium: 7  # Unattached >7 days = MEDIUM (default: 7)
```

**How it works:**
- Disks with `managed_by = None` (not attached) are checked
- Confidence based on how long they've been unattached:
    - `>= high` days → HIGH confidence
    - `>= medium` days → MEDIUM confidence
    - `< medium` days → Not flagged

**CLI override:**

```bash
cleancloud scan --provider azure \
  --rule-config azure.unattached_disks.confidence.high=30 \
  --rule-config azure.unattached_disks.confidence.medium=14
```

---

#### `old_snapshots`

Find old Azure managed disk snapshots.

**Configuration:**

```yaml
rules:
  azure:
    old_snapshots:
      confidence:
        high: 90   # >90 days = HIGH (default: 90)
        medium: 30 # >30 days = MEDIUM (default: 30)
```

**How it works:**
- Snapshots older than thresholds are flagged
- Confidence based on age:
    - `>= high` days → HIGH confidence
    - `>= medium` days → MEDIUM confidence
    - `< medium` days → Not flagged

**CLI override:**

```bash
# More aggressive
cleancloud scan --provider azure \
  --rule-config azure.old_snapshots.confidence.high=60 \
  --rule-config azure.old_snapshots.confidence.medium=14

# More conservative
cleancloud scan --provider azure \
  --rule-config azure.old_snapshots.confidence.high=180 \
  --rule-config azure.old_snapshots.confidence.medium=90
```

---

#### `untagged_resources`

Find Azure resources without tags.

**Configuration:**

```yaml
rules:
  azure:
    untagged_resources:
      min_age_days: 7  # Ignore resources <7 days old (default: 7)
```

**How it works:**
- Resources without any tags are flagged
- Resources newer than `min_age_days` are ignored
- Snapshots must be at least `min_age_days` old to be flagged

**CLI override:**

```bash
cleancloud scan --provider azure \
  --rule-config azure.untagged_resources.min_age_days=14
```

---

#### `unused_public_ips`

Find Azure public IPs not attached to resources.

**Configuration:**

```yaml
rules:
  azure:
    unused_public_ips:
      confidence:
        high: 0  # Immediate HIGH confidence (default: 0)
```

**How it works:**
- Public IPs not attached to any resource are flagged
- **Always HIGH confidence** (cost + security risk)
- `high: 0` means immediate flagging (no grace period)

**CLI override:**

```bash
# Add grace period (if needed)
cleancloud scan --provider azure \
  --rule-config azure.unused_public_ips.confidence.high=1
```

---

## Common Use Cases

### Use Case 1: Production (Conservative)

**Goal:** Avoid false positives in production environments

**Configuration:**

```yaml
rules:
  aws:
    old_ebs_snapshots:
      days_old: 730      # 2 years
      confidence:
        high: 730
        medium: 365
    
    unattached_volumes:
      confidence:
        high: 30         # 1 month
        medium: 14
  
  azure:
    unattached_disks:
      confidence:
        high: 30
        medium: 14
    
    old_snapshots:
      confidence:
        high: 180        # 6 months
        medium: 90
```

**Usage:**

```bash
cleancloud scan --provider aws --config prod.yaml --all-regions
```

---

### Use Case 2: Development (Aggressive)

**Goal:** Quickly identify and clean up dev/test resources

**Configuration:**

```yaml
rules:
  aws:
    old_ebs_snapshots:
      days_old: 30       # 1 month
      confidence:
        high: 90
        medium: 30
    
    unattached_volumes:
      confidence:
        high: 3          # 3 days
        medium: 1
  
  azure:
    unattached_disks:
      confidence:
        high: 3
        medium: 1
    
    old_snapshots:
      confidence:
        high: 30
        medium: 7
    
    untagged_resources:
      min_age_days: 1    # Flag almost immediately
```

**Usage:**

```bash
cleancloud scan --provider aws --config dev.yaml --region us-east-1
```

---

### Use Case 3: Cost Optimization Focus

**Goal:** Identify expensive resources quickly

**Configuration:**

```yaml
rules:
  aws:
    old_ebs_snapshots:
      days_old: 90       # 3 months
      confidence:
        high: 180
        medium: 90
    
    unattached_volumes:
      confidence:
        high: 7          # Flag quickly (cost impact)
        medium: 3
    
    infinite_log_retention:
      confidence:
        high: 7          # Log retention = storage cost
  
  azure:
    unattached_disks:
      confidence:
        high: 7
        medium: 3
    
    old_snapshots:
      confidence:
        high: 60
        medium: 30
    
    unused_public_ips:
      confidence:
        high: 0          # Public IPs cost money immediately
```

**Usage:**

```bash
cleancloud scan --provider aws --config cost-optimization.yaml --all-regions
```

---

### Use Case 4: Compliance/Audit Focus

**Goal:** Ensure all resources are properly tagged

**Configuration:**

```yaml
rules:
  aws:
    untagged_resources:
      min_age_days: 1    # Flag almost immediately
    
    # Other rules more lenient
    old_ebs_snapshots:
      days_old: 365
    
    unattached_volumes:
      confidence:
        high: 30
        medium: 14
  
  azure:
    untagged_resources:
      min_age_days: 1    # Strict tagging requirement
    
    unattached_disks:
      confidence:
        high: 30
        medium: 14
```

**Usage:**

```bash
cleancloud scan --provider aws --config compliance.yaml --all-regions
```

---

## CLI Examples

### Basic Usage

```bash
# Use default config (built-in)
cleancloud scan --provider aws --region us-east-1

# Use cleancloud.yaml in current directory
cleancloud scan --provider aws --region us-east-1

# Use specific config file
cleancloud scan --provider aws --config prod.yaml --region us-east-1
```

---

### Single Override

```bash
# Override just snapshot threshold
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.old_ebs_snapshots.days_old=90

# Override just volume confidence
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.unattached_volumes.confidence.high=30
```

---

### Multiple Overrides

```bash
# Override multiple AWS settings
cleancloud scan --provider aws --region us-east-1 \
  --rule-config aws.old_ebs_snapshots.days_old=90 \
  --rule-config aws.old_ebs_snapshots.confidence.high=180 \
  --rule-config aws.unattached_volumes.confidence.high=30

# Override multiple Azure settings
cleancloud scan --provider azure \
  --rule-config azure.unattached_disks.confidence.high=30 \
  --rule-config azure.old_snapshots.confidence.medium=60
```

---

### Environment-Specific Scans

```bash
# Production (conservative)
cleancloud scan --provider aws --config config/prod.yaml --all-regions

# Development (aggressive)
cleancloud scan --provider aws --config config/dev.yaml --region us-east-1

# Test (very aggressive)
cleancloud scan --provider aws --config config/test.yaml --region us-west-2
```

---

### Combining Config File + CLI Overrides

```bash
# Use prod.yaml but test different snapshot threshold
cleancloud scan --provider aws --config prod.yaml --region us-east-1 \
  --rule-config aws.old_ebs_snapshots.days_old=180

# CLI override has highest priority
```

---

### Verbose Mode (Show Configuration)

```bash
# Show what configuration is being used
cleancloud scan --provider aws --region us-east-1 --verbose

# Output includes:
# 📋 Configuration loaded from:
#    ✓ ./cleancloud.yaml
#    ✓ Built-in defaults
#
# 🔍 Scanning region us-east-1
#    Rule configs:
#      • unattached_volumes: {'confidence': {'high': 14, 'medium': 7}}
#      • old_ebs_snapshots: {'days_old': 180, 'confidence': {...}}
```

---

### Validate Configuration

```bash
# Validate cleancloud.yaml
cleancloud config validate

# Validate specific file
cleancloud config validate --config prod.yaml

# Output:
# ✅ Configuration is valid!
# 
# Configuration summary:
#   AWS rules: 4 configured
#   Azure rules: 4 configured
```

---

### Show Merged Configuration

```bash
# Show all configuration
cleancloud config show

# Show just AWS config
cleancloud config show --provider aws

# Show with overrides applied
cleancloud config show \
  --rule-config aws.old_ebs_snapshots.days_old=90 \
  --provider aws

# Output (JSON):
# {
#   "old_ebs_snapshots": {
#     "days_old": 90,
#     "confidence": {
#       "high": 365,
#       "medium": 180
#     }
#   },
#   ...
# }
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: CleanCloud Scan

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly

jobs:
  scan-production:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install CleanCloud
        run: pip install cleancloud
      
      - name: Scan AWS (Conservative)
        run: |
          cleancloud scan \
            --provider aws \
            --config .cleancloud/prod.yaml \
            --all-regions \
            --output json \
            --output-file aws-findings.json
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  
  scan-development:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Scan AWS (Aggressive)
        run: |
          cleancloud scan \
            --provider aws \
            --config .cleancloud/dev.yaml \
            --region us-east-1 \
            --fail-on-confidence HIGH
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.DEV_AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.DEV_AWS_SECRET_ACCESS_KEY }}
```

---

### GitLab CI

```yaml
stages:
  - scan

scan-production:
  stage: scan
  image: python:3.11
  script:
    - pip install cleancloud
    - |
      cleancloud scan \
        --provider aws \
        --config config/prod.yaml \
        --all-regions \
        --output json \
        --output-file findings.json
  artifacts:
    paths:
      - findings.json
  only:
    - schedules

scan-development:
  stage: scan
  image: python:3.11
  script:
    - pip install cleancloud
    - |
      cleancloud scan \
        --provider aws \
        --config config/dev.yaml \
        --region us-east-1 \
        --fail-on-confidence HIGH \
        --output json \
        --output-file findings.json
  artifacts:
    paths:
      - findings.json
  only:
    - merge_requests
```

---

### Per-Environment Overrides

```bash
# Use base config + environment-specific overrides
export ENV=production

if [ "$ENV" = "production" ]; then
  cleancloud scan --provider aws \
    --config base.yaml \
    --rule-config aws.old_ebs_snapshots.days_old=730 \
    --rule-config aws.unattached_volumes.confidence.high=30 \
    --all-regions
elif [ "$ENV" = "development" ]; then
  cleancloud scan --provider aws \
    --config base.yaml \
    --rule-config aws.old_ebs_snapshots.days_old=30 \
    --rule-config aws.unattached_volumes.confidence.high=3 \
    --region us-east-1
fi
```

---

## Troubleshooting

### Issue: Configuration Not Loading

**Symptom:** CleanCloud doesn't seem to use my config file

**Check:**

1. **File location:**
   ```bash
   # Should be one of:
   ./cleancloud.yaml           # Current directory
   ~/.cleancloud/config.yaml   # User home
   # Or specified with --config
   ```

2. **File syntax:**
   ```bash
   # Validate YAML
   cleancloud config validate
   
   # Show what's loaded
   cleancloud config show
   ```

3. **File permissions:**
   ```bash
   ls -la cleancloud.yaml
   # Should be readable
   ```

---

### Issue: CLI Override Not Working

**Symptom:** `--rule-config` flag seems ignored

**Check:**

1. **Correct format:**
   ```bash
   # CORRECT
   --rule-config aws.old_ebs_snapshots.days_old=90
   
   # WRONG (missing equals)
   --rule-config aws.old_ebs_snapshots.days_old 90
   
   # WRONG (spaces around equals)
   --rule-config aws.old_ebs_snapshots.days_old = 90
   ```

2. **Verify override applied:**
   ```bash
   # Use --verbose to see config
   cleancloud scan --provider aws --region us-east-1 \
     --rule-config aws.old_ebs_snapshots.days_old=90 \
     --verbose
   
   # Or show config
   cleancloud config show \
     --rule-config aws.old_ebs_snapshots.days_old=90 \
     --provider aws
   ```

3. **Check rule name spelling:**
   ```bash
   # CORRECT
   aws.old_ebs_snapshots
   azure.unattached_disks
   
   # WRONG (typos)
   aws.old_snapshots           # Missing "ebs"
   azure.unattached_volumes    # Wrong (it's "disks")
   ```

---

### Issue: Invalid Configuration Error

**Symptom:** `❌ Configuration error: ...`

**Common causes:**

1. **Invalid YAML syntax:**
   ```yaml
   # WRONG (missing space after colon)
   rules:
     aws:
       old_ebs_snapshots:
         days_old:180  # ❌ Missing space
   
   # CORRECT
   rules:
     aws:
       old_ebs_snapshots:
         days_old: 180  # ✅ Space after colon
   ```

2. **Wrong indentation:**
   ```yaml
   # WRONG
   rules:
   aws:              # ❌ Should be indented
     old_ebs_snapshots:
   
   # CORRECT
   rules:
     aws:            # ✅ Indented under rules
       old_ebs_snapshots:
   ```

3. **Invalid values:**
   ```yaml
   # WRONG
   old_ebs_snapshots:
     days_old: "ninety"  # ❌ Must be number
   
   # CORRECT
   old_ebs_snapshots:
     days_old: 90        # ✅ Number
   ```

---

### Issue: Unexpected Confidence Levels

**Symptom:** Resources flagged with wrong confidence

**Check:**

1. **Verify thresholds:**
   ```bash
   # Show config being used
   cleancloud config show --provider aws
   ```

2. **Check resource age:**
    - Confidence is based on age thresholds
    - A 20-day-old snapshot with `high: 90, medium: 30` will be MEDIUM
    - Verify the resource age matches your expectations

3. **Review finding details:**
   ```bash
   # Check JSON output to see thresholds used
   cleancloud scan --provider aws --region us-east-1 \
     --output json \
     --output-file findings.json
   
   # Each finding includes "thresholds_used"
   cat findings.json | jq '.findings[0].details.thresholds_used'
   ```

---

### Issue: Too Many/Few Findings

**Symptom:** Getting more or fewer findings than expected

**Solution:**

1. **Adjust thresholds:**
   ```yaml
   # Too many findings? Increase thresholds
   old_ebs_snapshots:
     days_old: 365  # Was 90
   
   # Too few findings? Decrease thresholds
   old_ebs_snapshots:
     days_old: 30   # Was 365
   ```

2. **Test incrementally:**
   ```bash
   # Start aggressive, see what you get
   cleancloud scan --provider aws --region us-east-1 \
     --rule-config aws.old_ebs_snapshots.days_old=30
   
   # Too many? Increase
   cleancloud scan --provider aws --region us-east-1 \
     --rule-config aws.old_ebs_snapshots.days_old=90
   
   # Find sweet spot, then save to config
   ```

3. **Use tag filtering:**
   ```yaml
   # Ignore production resources
   tag_filtering:
     enabled: true
     ignore:
       - key: env
         value: production
   ```

---

## Best Practices

### 1. Start Conservative

```yaml
# Begin with high thresholds
rules:
  aws:
    old_ebs_snapshots:
      days_old: 365  # 1 year
    
    unattached_volumes:
      confidence:
        high: 30     # 1 month
        medium: 14
```

**Then gradually reduce as you build confidence in CleanCloud.**

---

### 2. Version Control Your Configs

```bash
# Store in git
git add cleancloud.yaml
git add config/prod.yaml config/dev.yaml
git commit -m "Add CleanCloud configs"

# Benefits:
# ✅ Audit trail
# ✅ Team collaboration
# ✅ Rollback capability
```

---

### 3. Environment-Specific Configs

```
config/
├── prod.yaml      # Conservative
├── staging.yaml   # Moderate
├── dev.yaml       # Aggressive
└── test.yaml      # Very aggressive
```

---

### 4. Use Verbose Mode When Testing

```bash
# See exactly what config is used
cleancloud scan --provider aws --region us-east-1 --verbose
```

---

### 5. Validate Before Committing

```bash
# Always validate before git commit
cleancloud config validate --config prod.yaml

# Add to pre-commit hook
```

---

### 6. Document Your Rationale

```yaml
# Add comments explaining why
rules:
  aws:
    old_ebs_snapshots:
      # Conservative: Allow 2 years for long-term backups
      # Based on Q4 2024 audit requirements
      days_old: 730
      confidence:
        high: 730
        medium: 365
```

---

### 7. Test Changes in Dev First

```bash
# Test new thresholds in dev
cleancloud scan --provider aws --config dev-test.yaml --region us-east-1

# Verify results make sense
# Then apply to staging → production
```

---

## See Also

- [CleanCloud README](../README.md)
- [AWS Setup Guide](aws.md)
- [Azure Setup Guide](azure.md)
- [CI/CD Integration](ci.md)
- [Tag Filtering](tag-filtering.md)

---

## Support

**Questions?** Open an issue on GitHub: https://github.com/cleancloud-io/cleancloud/issues

**Found a bug?** Report it: https://github.com/cleancloud-io/cleancloud/issues/new