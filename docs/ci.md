# CI/CD Integration Guide

Complete guide for integrating CleanCloud into continuous integration and deployment pipelines.

---

## Overview

CleanCloud is designed for CI/CD integration with:
- **Predictable exit codes** - Control pipeline behavior based on findings
- **Machine-readable output** - JSON/CSV for parsing and storage
- **Read-only operations** - Safe to run in any environment
- **Fast execution** - Scans complete in seconds to minutes

**Supported CI platforms:**
- GitHub Actions ✅
- Azure DevOps Pipelines ✅
- GitLab CI 🔜 Planned
- Jenkins 🔜 Planned
- CircleCI 🔜 Planned

---

## Goals of CI Integration

### 1. Early Detection
Identify orphaned resources before they accumulate:
- Catch unattached volumes during development
- Flag missing tags before merging to main
- Detect resource leaks from failed deployments

### 2. Policy Enforcement
Enforce hygiene standards automatically:
- Block PRs with HIGH confidence findings
- Generate compliance reports for audits
- Prevent hygiene debt from reaching production

### 3. Visibility
Track hygiene trends over time:
- Store scan results as artifacts
- Compare findings across branches
- Monitor hygiene score improvements

### 4. Safe by Default
Never risk production stability:
- Read-only operations only
- No resource modifications
- No automated cleanup

---

## Exit Codes

CleanCloud uses standard Unix exit codes for CI control.

| Exit Code | Meaning | CI Behavior |
|-----------|---------|-------------|
| `0` | Success - no policy violations | Pipeline continues |
| `1` | Configuration error or unexpected failure | Pipeline fails |
| `2` | Policy violation - findings detected | Pipeline fails (when enforcement enabled) |
| `3` | Missing credentials or insufficient permissions | Pipeline fails |

### Exit Code Examples

**Informational mode (default):**
```bash
cleancloud scan --provider aws
# Always exits 0, even if findings exist
```

**Enforcement mode - fail on any findings:**
```bash
cleancloud scan --provider aws --fail-on-findings
# Exits 2 if any findings exist
```

**Enforcement mode - fail on confidence threshold:**
```bash
cleancloud scan --provider aws --fail-on-confidence HIGH
# Exits 2 only if HIGH confidence findings exist
```

---

## Credentials & Secrets Management

### Best Practices

**✅ DO:**
- Use environment-specific secrets (dev, staging, prod)
- Rotate credentials regularly
- Use least-privilege IAM roles/RBAC
- Store secrets in platform secret managers

**❌ DON'T:**
- Use repository-level secrets for production
- Hard-code credentials in workflows
- Share credentials across environments
- Use overly permissive roles

### GitHub Actions Environment Strategy

Create separate environments for different stages:

| Environment | Purpose | Secrets |
|------------|---------|---------|
| `cleancloud-dev` | PR checks, development scans | AWS/Azure dev account credentials |
| `cleancloud-staging` | Main branch validation | AWS/Azure staging credentials |
| `cleancloud-prod` | Production monitoring | AWS/Azure production credentials (read-only) |

Each environment should have:
- Manual approval requirements (for prod)
- Deployment protection rules
- Separate cloud account credentials

---

## GitHub Actions Integration

### Basic Example (AWS)

```yaml
name: CleanCloud AWS Scan

on:
  pull_request:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday at midnight

jobs:
  scan-aws:
    runs-on: ubuntu-latest
    
    steps:
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install CleanCloud
        run: pip install cleancloud

      - name: Run AWS scan
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: us-east-1
        run: |
          cleancloud scan \
            --provider aws \
            --all-regions \
            --output json \
            --output-file results.json \
            --fail-on-confidence HIGH

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: cleancloud-aws-results
          path: results.json
```

### Basic Example (Azure)

```yaml
name: CleanCloud Azure Scan

on:
  pull_request:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday at midnight

jobs:
  scan-azure:
    runs-on: ubuntu-latest
    
    steps:
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install CleanCloud
        run: pip install cleancloud

      - name: Run Azure scan
        env:
          AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
        run: |
          cleancloud scan \
            --provider azure \
            --output json \
            --output-file results.json \
            --fail-on-confidence HIGH

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: cleancloud-azure-results
          path: results.json
```

### Multi-Cloud Example

```yaml
name: CleanCloud Multi-Cloud Scan

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  scan-aws:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - run: pip install cleancloud
      
      - name: Scan AWS
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          cleancloud scan --provider aws --all-regions \
            --output json --output-file aws-results.json \
            --fail-on-confidence HIGH
      
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: aws-results
          path: aws-results.json

  scan-azure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - run: pip install cleancloud
      
      - name: Scan Azure
        env:
          AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
        run: |
          cleancloud scan --provider azure \
            --output json --output-file azure-results.json \
            --fail-on-confidence HIGH
      
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: azure-results
          path: azure-results.json
```

### Advanced: Environment-Based Enforcement

```yaml
name: CleanCloud with Environment Gates

on:
  pull_request:
  push:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    environment: ${{ 
      github.event_name == 'pull_request' && 'cleancloud-dev' ||
      github.ref == 'refs/heads/main' && 'cleancloud-staging' ||
      'cleancloud-prod'
    }}
    
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - run: pip install cleancloud

      - name: Scan with environment-specific policy
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          if [ "${{ github.event_name }}" == "pull_request" ]; then
            # Strict enforcement for PRs
            cleancloud scan --provider aws --fail-on-confidence MEDIUM
          elif [ "${{ github.ref }}" == "refs/heads/main" ]; then
            # Moderate enforcement for main
            cleancloud scan --provider aws --fail-on-confidence HIGH
          else
            # Informational for prod (monitor only)
            cleancloud scan --provider aws
          fi

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: results-${{ github.sha }}
          path: results.json
```

---

## Azure DevOps Pipelines Integration

### Basic Pipeline (AWS)

```yaml
trigger:
  - main

schedules:
  - cron: "0 0 * * 1"  # Weekly on Monday
    displayName: Weekly hygiene scan
    branches:
      include:
        - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'
    displayName: 'Use Python 3.11'

  - script: |
      pip install cleancloud
    displayName: 'Install CleanCloud'

  - script: |
      cleancloud scan \
        --provider aws \
        --all-regions \
        --output json \
        --output-file $(Build.ArtifactStagingDirectory)/results.json \
        --fail-on-confidence HIGH
    displayName: 'Run CleanCloud AWS Scan'
    env:
      AWS_ACCESS_KEY_ID: $(AWS_ACCESS_KEY_ID)
      AWS_SECRET_ACCESS_KEY: $(AWS_SECRET_ACCESS_KEY)

  - task: PublishBuildArtifacts@1
    condition: always()
    inputs:
      pathToPublish: '$(Build.ArtifactStagingDirectory)/results.json'
      artifactName: 'cleancloud-results'
    displayName: 'Publish scan results'
```

### Basic Pipeline (Azure)

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: pip install cleancloud
    displayName: 'Install CleanCloud'

  - script: |
      cleancloud scan \
        --provider azure \
        --output json \
        --output-file $(Build.ArtifactStagingDirectory)/results.json \
        --fail-on-confidence HIGH
    displayName: 'Run CleanCloud Azure Scan'
    env:
      AZURE_CLIENT_ID: $(AZURE_CLIENT_ID)
      AZURE_TENANT_ID: $(AZURE_TENANT_ID)
      AZURE_CLIENT_SECRET: $(AZURE_CLIENT_SECRET)

  - task: PublishBuildArtifacts@1
    condition: always()
    inputs:
      pathToPublish: '$(Build.ArtifactStagingDirectory)/results.json'
      artifactName: 'cleancloud-results'
```

---

## Policy Enforcement Strategies

### Strategy 1: Block on HIGH Confidence (Recommended)

**Use case:** Production environments, main branches

```bash
cleancloud scan --provider aws --fail-on-confidence HIGH
```

**Behavior:**
- ✅ Blocks on very likely orphaned resources
- ✅ Low false positive rate
- ✅ Allows MEDIUM/LOW confidence findings through
- ✅ Good balance of safety and strictness

**Best for:**
- Teams new to CleanCloud
- Environments with active development
- Avoiding pipeline disruption

---

### Strategy 2: Block on MEDIUM or Higher

**Use case:** Staging environments, scheduled audits

```bash
cleancloud scan --provider aws --fail-on-confidence MEDIUM
```

**Behavior:**
- ⚠️ Blocks on likely orphaned resources
- ⚠️ Higher false positive potential
- ⚠️ May require tuning for your environment

**Best for:**
- Mature hygiene practices
- Regular review processes in place
- Staging environment validation

---

### Strategy 3: Informational Only

**Use case:** Initial rollout, monitoring

```bash
cleancloud scan --provider aws
```

**Behavior:**
- ✅ Never blocks pipelines
- ✅ Generates reports for review
- ✅ Builds baseline understanding

**Best for:**
- First-time CleanCloud users
- Understanding your hygiene baseline
- Production monitoring without enforcement

---

### Strategy 4: Strict Mode

**Use case:** Critical compliance requirements

```bash
cleancloud scan --provider aws --fail-on-findings
```

**Behavior:**
- ❌ Blocks on ANY findings (including LOW confidence)
- ❌ Very high false positive rate
- ❌ Requires constant maintenance

**Best for:**
- Compliance-driven organizations
- Highly regulated environments
- Teams with dedicated SRE resources

**Warning:** Not recommended for most teams. Start with Strategy 1.

---

## Output Management

### Storing Results

**Upload as artifacts:**
```yaml
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: cleancloud-results-${{ github.run_number }}
    path: results.json
    retention-days: 90
```

**Commit to repository (not recommended):**
```yaml
- run: |
    git config user.name "CleanCloud Bot"
    git add results.json
    git commit -m "Update hygiene scan results"
    git push
```

**Send to external storage:**
```yaml
- name: Upload to S3
  run: |
    aws s3 cp results.json s3://my-bucket/cleancloud/results-${{ github.sha }}.json
```

### Parsing Results in CI

**Check for specific findings:**
```bash
# Count HIGH confidence findings
HIGH_COUNT=$(jq '.summary.by_confidence.HIGH // 0' results.json)

if [ "$HIGH_COUNT" -gt 0 ]; then
  echo "Found $HIGH_COUNT HIGH confidence findings"
  exit 1
fi
```

**Generate summary comment (GitHub Actions):**
```yaml
- name: Comment PR with results
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      const fs = require('fs');
      const results = JSON.parse(fs.readFileSync('results.json'));
      
      const body = `## CleanCloud Scan Results
      
      - Total findings: ${results.summary.total_findings}
      - HIGH confidence: ${results.summary.by_confidence.HIGH || 0}
      - MEDIUM confidence: ${results.summary.by_confidence.MEDIUM || 0}
      - LOW confidence: ${results.summary.by_confidence.LOW || 0}
      `;
      
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: body
      });
```

---

## Scheduled Scans

### Weekly Hygiene Audit

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC

jobs:
  weekly-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - run: pip install cleancloud
      
      - name: Run comprehensive scan
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          cleancloud scan \
            --provider aws \
            --all-regions \
            --output json \
            --output-file weekly-audit.json
      
      - name: Email results
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 465
          username: ${{ secrets.EMAIL_USERNAME }}
          password: ${{ secrets.EMAIL_PASSWORD }}
          subject: Weekly AWS Hygiene Report
          body: See attached scan results
          to: sre-team@company.com
          from: cleancloud@company.com
          attachments: weekly-audit.json
```

### Daily Production Monitoring

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC

jobs:
  daily-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - run: pip install cleancloud
      
      - name: Scan production
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.PROD_AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.PROD_AWS_SECRET_ACCESS_KEY }}
        run: |
          cleancloud scan --provider aws --region us-east-1 \
            --output json --output-file prod-scan.json
      
      - name: Check for critical issues
        run: |
          HIGH_COUNT=$(jq '.summary.by_confidence.HIGH // 0' prod-scan.json)
          if [ "$HIGH_COUNT" -gt 10 ]; then
            echo "⚠️ HIGH confidence findings exceeded threshold: $HIGH_COUNT"
            # Send alert to Slack/PagerDuty
          fi
```

---

## Troubleshooting CI Integration

### "No AWS credentials found"

**Cause:** Credentials not properly passed to workflow

**Solution:**
```yaml
# Ensure secrets are correctly referenced
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### "Permission denied" errors

**Cause:** Insufficient IAM/RBAC permissions

**Solution:**
1. Run `cleancloud doctor` locally with same credentials
2. Verify required permissions (see [AWS](aws.md) or [Azure](azure.md) docs)
3. Update IAM policy/RBAC role

### Pipeline times out

**Cause:** Scanning too many regions or resources

**Solution:**
```yaml
# Increase timeout
timeout-minutes: 30

# Or scan fewer regions
run: cleancloud scan --provider aws --region us-east-1
```

### Results not uploaded

**Cause:** Artifact upload runs only on success

**Solution:**
```yaml
# Always upload, even on failure
- uses: actions/upload-artifact@v4
  if: always()  # ← Add this
  with:
    name: results
    path: results.json
```

---

## Best Practices

### 1. Start Small
- Begin with informational scans (no enforcement)
- Build baseline understanding over 2-4 weeks
- Enable enforcement gradually

### 2. Separate Environments
- Use different credentials per environment
- Apply stricter policies to development/staging
- Monitor production without blocking

### 3. Store Results
- Archive scan results for trend analysis
- Keep results for 90 days minimum
- Use consistent naming: `results-{date}-{sha}.json`

### 4. Monitor Performance
- Track scan duration over time
- Alert on unexpected slowdowns
- Optimize by limiting regions/subscriptions

### 5. Automate Responses
- Generate tickets for HIGH confidence findings
- Send weekly digest reports
- Track remediation time

---

## Security Considerations

### Secrets Management
- ✅ Use platform secret stores (GitHub Secrets, Azure Key Vault)
- ✅ Rotate credentials quarterly
- ✅ Use least-privilege IAM roles
- ❌ Never commit credentials to repositories
- ❌ Never log credentials in workflow output

### Network Security
- CleanCloud only makes HTTPS API calls
- No data sent to third parties
- Results stored in your infrastructure

### Compliance
- CleanCloud is read-only and audit-friendly
- Scan results can be retained for compliance
- No PII or sensitive data in findings

---

## Roadmap

Planned CI/CD enhancements:

**Short-term (Next 3 months):**
- SARIF output format for GitHub code scanning
- GitLab CI example workflows
- Jenkins pipeline examples

**Medium-term (3-6 months):**
- GitHub PR annotations with findings
- Slack/Teams notifications
- Trend analysis across scans

**Long-term (6-12 months):**
- CleanCloud GitHub App (no credentials needed)
- Native Azure DevOps extension
- CircleCI orb

---

## Next Steps

- **AWS CI Setup:** See [AWS documentation](aws.md) for credential configuration
- **Azure CI Setup:** See [Azure documentation](azure.md) for service principal setup
- **Rule Documentation:** Review [rules.md](rules.md) for finding details

---

## Support

If you encounter issues with CI/CD integration:

1. Review this guide and provider-specific docs
2. Run `cleancloud doctor` locally with same credentials
3. Check GitHub Actions logs for specific error messages
4. Submit issues with workflow YAML and error logs (redact credentials!)