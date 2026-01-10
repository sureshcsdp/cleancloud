# CleanCloud

**A trust-first cloud hygiene engine for production environments.
CleanCloud provides conservative, read-only hygiene signals for AWS and Azure that are safe to run in production and CI pipelines.**

CleanCloud helps SRE and platform teams safely identify **review-only candidates**
for orphaned, untagged, or inactive cloud resources — **without deleting anything,
changing tags, or optimizing costs.**

> ⚠️ CleanCloud never modifies cloud resources.  
> ⚠️ No auto-cleanup. No cost optimization. No telemetry.

![PyPI](https://img.shields.io/pypi/v/cleancloud)
![Python Versions](https://img.shields.io/pypi/pyversions/cleancloud)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![GitHub stars](https://img.shields.io/github/stars/cleancloud-io/cleancloud?style=social)

## Who CleanCloud Is (and Is Not) For

**CleanCloud is for:**
- SRE / Platform teams reviewing cloud hygiene safely
- Security-reviewed and regulated environments
- CI/CD pipelines that must never mutate infrastructure
- Teams using IaC and ephemeral resources

**CleanCloud is NOT:**
- ❌ A cost optimization or FinOps tool
- ❌ An automated cleanup or deletion service
- ❌ A replacement for Trusted Advisor or Config
- ❌ A dashboard that flags everything

CleanCloud exists to answer one question safely:

> CleanCloud exists to help SRE and platform teams reduce unknown state in cloud environments — safely and without mutations.

## Why CleanCloud?

CleanCloud uses multiple conservative signals and assigns explicit confidence levels (LOW / MEDIUM / HIGH) to every finding, so teams can enforce policy without false positives.

Modern cloud environments continuously create and destroy resources.
Over time, **storage and logs lose ownership**, and deleting them becomes risky.

Most tools do one of two things:
1. **Auto-delete** → unsafe
2. **Flag everything** → noisy

**CleanCloud takes a third approach:**

- Multiple conservative signals
- Explicit confidence levels (LOW / MEDIUM / HIGH)
- Review-only findings
- Zero mutations

This makes it safe to run in **production accounts and CI pipelines**.

---

### What makes CleanCloud different

| CleanCloud | Typical tools |
|----------|---------------|
| Read-only, review-only | Auto-delete or mutate |
| Explicit confidence levels | Binary flags |
| Conservative signal design | Noisy heuristics |
| Safe for CI and prod | Often blocked by security |
| No telemetry | Hidden data collection |

---

## Where CleanCloud Fits

CleanCloud is designed to generate trusted hygiene signals that can be consumed by humans, CI pipelines, or higher-level security and observability platforms.

It sits between:
- native cloud provider checks (e.g. AWS Config, Trusted Advisor)
- and automated cleanup / mutation tools

For a visual overview of this positioning, see:
→ [Where CleanCloud Fits (design diagram)](docs/design.md#where-cleancloud-fits)

## Built for Production & Enterprise Use
CleanCloud is designed to be approved by security teams, not bypassed.

- ✅ **Read-only by design** (no Delete*, Modify*, or Tag* permissions)
- ✅ **OIDC-first authentication** (AWS & Azure)
- ✅ **Parallel, multi-region scanning**
- ✅ **CI/CD friendly** (exit codes, JSON/CSV output)
- ✅ **Audit-friendly** (deterministic output, no side effects)

**Security model:**
- 🔒 No credentials stored
- 🔐 Short-lived tokens only
- 🧪 Safety regression tests prevent write APIs
- 🌐 Zero outbound calls (except AWS/Azure APIs)

→ **For InfoSec teams:** [Information Security Readiness Guide](docs/infosec-readiness.md)
→ **IAM Proof Pack:** [Ready-to-use policies and verification scripts](security/) | [Documentation](docs/infosec-readiness.md#iam-proof-pack)
→ **Threat Model:** [Comprehensive threat analysis and mitigations](docs/infosec-readiness.md#threat-model)

## CI/CD at a Glance

CleanCloud is designed for policy enforcement without side effects.

```bash
# Fail only on high-confidence hygiene risks
cleancloud scan --provider aws --region us-east-1 --fail-on-confidence HIGH
```
Exit codes are stable and intentional:

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Scan completed successfully, no blocking findings |
| `1` | Configuration error, invalid region/location, or unexpected error |
| `2` | Policy violation (findings detected with `--fail-on-findings` or `--fail-on-confidence`) |
| `3` | Missing permissions or invalid credentials |

**Note:** Invalid region names (AWS) or location names (Azure) trigger exit code `1` immediately, before attempting API calls.

CleanCloud never fails a build by accident.

### Stability guarantees

- CLI flags are backward-compatible within a major version
- Exit codes are stable and intentional
- JSON output schemas are versioned and documented

## Quick Start

### Installation

```bash
pip install cleancloud
```

### Validate Credentials

```bash
# AWS - validate credentials and permissions
# Defaults to us-east-1 if --region not specified
cleancloud doctor --provider aws
cleancloud doctor --provider aws --region us-west-2

# Azure - validate credentials and subscription access
# Note: --region parameter is not applicable for Azure doctor
cleancloud doctor --provider azure
```

### Run a Scan

```bash
# AWS - single region
cleancloud scan --provider aws --region us-east-1

# AWS - all active regions (auto-detects regions with resources)
cleancloud scan --provider aws --all-regions

# Azure - all subscriptions (default)
cleancloud scan --provider azure

# Azure - specific subscription
cleancloud scan --provider azure --subscription <subscription-id>

# Azure - multiple subscriptions
cleancloud scan --provider azure --subscription <sub-id-1> --subscription <sub-id-2>

# Azure - filter by location
cleancloud scan --provider azure --region eastus

# Azure - specific subscription and location
cleancloud scan --provider azure --subscription <subscription-id> --region eastus
```

### View Results

```bash
# Human-readable output (default)
cleancloud scan --provider aws --region us-east-1

# JSON output (AWS)
cleancloud scan --provider aws --region us-east-1 --output json --output-file results.json

# JSON output (Azure)
cleancloud scan --provider azure --output json --output-file results.json

# CSV output
cleancloud scan --provider aws --region us-east-1 --output csv --output-file results.csv
```

**JSON Output Schema:**

AWS and Azure have slightly different schema structures:
- **AWS**: `regions_scanned` contains AWS region names (e.g., `["us-east-1", "us-west-2"]`)
- **Azure**:
  - `regions_scanned` contains Azure location names (e.g., `["eastus", "westus2"]`)
  - `subscriptions_scanned` contains subscription IDs (e.g., `["29d91ee0-..."]`)

See [`docs/ci.md#json-output-machine-readable`](docs/ci.md#json-output-machine-readable) for complete schema examples.

---

## What CleanCloud Detects

CleanCloud intentionally starts with **a small number of high-signal rules**.

Each rule:
- Is read-only
- Uses multiple conservative signals
- Avoids false positives in IaC environments
- Includes explicit confidence levels

**See [`docs/rules.md`](docs/rules.md) for full details.**

---

### Policy Enforcement

Control pipeline behavior based on finding confidence levels:

**AWS Examples:**

```bash
# Fail only on HIGH confidence findings (recommended)
cleancloud scan --provider aws --region us-east-1 --fail-on-confidence HIGH

# Fail on MEDIUM or higher confidence
cleancloud scan --provider aws --region us-east-1 --fail-on-confidence MEDIUM

# Fail on any findings (strict mode, not recommended)
cleancloud scan --provider aws --region us-east-1 --fail-on-findings
```

**Azure Examples:**

```bash
# Fail only on HIGH confidence findings (recommended)
cleancloud scan --provider azure --fail-on-confidence HIGH

# Fail on MEDIUM or higher confidence
cleancloud scan --provider azure --fail-on-confidence MEDIUM

# Fail on any findings (strict mode, not recommended)
cleancloud scan --provider azure --fail-on-findings

# With specific subscription
cleancloud scan --provider azure --subscription <subscription-id> --fail-on-confidence HIGH
```

**Note:** Policy enforcement works identically for both AWS and Azure providers.

---

## CI/CD Examples

CleanCloud is designed for CI/CD pipelines with predictable exit codes and policy enforcement.

#### Recommended: GitHub Actions with AWS OIDC (No Secrets)

CleanCloud supports AWS IAM Roles assumed via **GitHub Actions OpenID Connect (OIDC)**.
This is the recommended approach for CI/CD usage.

**Benefits:**

* No long-lived AWS credentials
* No secrets stored in GitHub
* Short-lived, auditable credentials
* Read-only by design

**GitHub Actions Example (AWS)**

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  cleancloud:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::<ACCOUNT_ID>:role/CleanCloudCIReadOnly
          aws-region: us-east-1

      - name: Run CleanCloud hygiene scan
        run: |
          pip install cleancloud
          cleancloud scan \
            --provider aws \
            --region us-east-1 \
            --output json \
            --output-file scan.json \
            --fail-on-confidence HIGH

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: cleancloud-results
          path: scan.json

```
See [`docs/ci.md`](docs/ci.md) for complete CI/CD integration examples.


## Configuration

### AWS

CleanCloud supports three AWS authentication methods:

1. GitHub Actions OIDC (recommended for CI/CD)
2. AWS CLI profiles (local development)
3. Environment variables

**Local Development (AWS Profile)**

```bash
# Using AWS profile
aws configure --profile <profile-name>
cleancloud scan --provider aws --profile <profile-name> --region us-east-1
```

**Environment Variables**
```
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1

cleancloud scan --provider aws --region us-east-1
```


**AWS IAM Policy (Minimum Read-Only Permissions)**

Attach the identity-based IAM policy as shown in [`docs/aws.md`](docs/aws.md)  to the IAM role or user used by CleanCloud
(**including GitHub Actions OIDC roles**):


**Characteristics:**

* No Delete*, Create*, or Tag* permissions
* Safe for production accounts
* Compatible with security-reviewed pipelines

See [`docs/aws.md`](docs/aws.md) for:

* OIDC provider setup
* IAM role trust policies
* Permission troubleshooting

## Azure

CleanCloud supports **Azure Workload Identity Federation (OIDC)** as the
**default and recommended authentication method**.

This enables **secretless authentication** using GitHub Actions, with short-lived,
auditable credentials and no stored client secrets.

---

### GitHub Actions with Azure OIDC (Recommended)

CleanCloud integrates with **Microsoft Entra ID Workload Identity Federation**
to authenticate securely in CI/CD pipelines.

**Benefits:**

- No `AZURE_CLIENT_SECRET`
- No long-lived credentials
- Short-lived, auditable tokens
- Enterprise-approved security model
- Consistent with AWS OIDC usage

---

#### GitHub Actions Example (Azure OIDC)

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  cleancloud:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Run CleanCloud hygiene scan
        run: |
          pip install cleancloud
          cleancloud scan \
            --provider azure \
            --output json \
            --output-file scan.json \
            --fail-on-confidence HIGH
          # Note: Scans all accessible subscriptions by default
          # Use --subscription <id> to scan specific subscription(s)
          # Use --region <location> to filter by Azure location (e.g., eastus)

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: cleancloud-results
          path: scan.json
```


**Local Development (Azure CLI)**

For local runs, CleanCloud uses the active Azure CLI session:

```bash
az login

# Scan all accessible subscriptions (default)
cleancloud scan --provider azure

# Scan specific subscription
cleancloud scan --provider azure --subscription <subscription-id>

# Scan multiple subscriptions
cleancloud scan --provider azure \
  --subscription <sub-id-1> \
  --subscription <sub-id-2>
```

**Azure Permissions**

CleanCloud requires **read-only access only**.

**Minimum role required:**

* Reader role at subscription scope

No write, delete, or tag permissions are required.

See [`docs/azure.md`](docs/azure.md) for:
* App registration setup
* Federated identity credential configuration
* Multiple environment support
* Permission troubleshooting

**Azure Subscription Selection**

By default, CleanCloud scans all accessible subscriptions. You can filter to specific subscriptions:

```bash
# Default: scan all accessible subscriptions
cleancloud scan --provider azure

# Scan specific subscription
cleancloud scan --provider azure --subscription <sub-id>

# Scan multiple subscriptions
cleancloud scan --provider azure \
  --subscription <sub-id-1> \
  --subscription <sub-id-2>
```

**When to use subscription filtering:**
- **Enterprise scale**: Organizations with 50+ subscriptions
- **Team ownership**: Scan only subscriptions your team owns
- **CI/CD pipelines**: Different pipelines for different subscriptions
- **Testing**: Test on dev subscriptions before running on production
- **Performance**: Faster scans when targeting specific subscriptions

---

### Tag-Based Filtering (Ignore Only)

CleanCloud supports tag-based filtering to reduce noise by ignoring findings for resources you explicitly mark.

This is useful when certain environments, teams, or services should be out of scope for hygiene review (for example: production or shared platform resources).

> ⚠️ Tag filtering is **ignore-only**
>
> It does **not** disable rules, modify resources, or protect them from deletion.  
> CleanCloud remains **read-only and review-only**.

### Configuration File (cleancloud.yaml)

Create a `cleancloud.yaml` file in your project root (or specify a custom path with `--config`):

```yaml
version: 1

tag_filtering:
  enabled: true
  ignore:
    - key: env
      value: production
    - key: team
      value: platform
    - key: keep   # key-only match (any value)
```

**Usage:**

```bash
# With config file in repository root
cleancloud scan --provider aws --region us-east-1 --config cleancloud.yaml

# Or specify full path
cleancloud scan --provider aws --region us-east-1 --config /path/to/cleancloud.yaml
```

**Behavior:**
* If a resource has any matching tag, its finding is ignored
* Matching is exact (no regex, no partial matches)
* Multiple ignore rules are OR'ed (any match ignores)


### Command Line Overrides (Highest Priority)
You can pass ignore tags directly via CLI:
```
cleancloud scan \
  --provider aws \
  --region us-east-1 \
  --ignore-tag env:production \
  --ignore-tag team:platform

```

**Important:**
* CLI --ignore-tag replaces YAML configuration
* YAML and CLI tags are not merged
* This ensures CI/CD runs are explicit and predictable


#### Scan Output & Transparency

Ignored findings are:

❌ Not included in scan results

✅ Counted and reported in the summary

✅ Preserved internally for auditability

Example summary output:
```
Ignored by tag policy: 7 findings
```

#### Recommended Usage

Tag filtering works best with **broad ownership or scope tags**, such as:

* env: production
* team: platform
* service: core-infra

It is **not intended** for per-resource exceptions or lifecycle management.

---

## Safety & Read-Only Guarantees

CleanCloud implements **multi-layer safety regression tests** to ensure no cloud resources are ever modified during scans:

- **Static AST checks**: Detect forbidden SDK calls in AWS/Azure provider code.
- **Runtime SDK guards**: Intercept forbidden SDK calls during tests.
- **IAM/Role definition checks**: Ensure AWS IAM policies and Azure RBAC roles are read-only.

These tests run automatically in CI and are required for all PRs.

For full details, see [docs/safety.md](docs/safety.md).

---

## Privacy & Telemetry

**CleanCloud collects zero telemetry.**

- No analytics
- No usage tracking
- No phone-home
- No opt-out flags

This is intentional.

Security tools should not transmit metadata from production environments.

## How we improve:
- GitHub issues and discussions
- Direct user feedback
- Community contributions

If CleanCloud helped you:
- ⭐ [Star the repo](https://github.com/cleancloud-io/cleancloud)
- 💬 Share feedback in [discussions](https://github.com/cleancloud-io/cleancloud/discussions)
- 🐛 [Report issues](https://github.com/cleancloud-io/cleancloud/issues)

---

## Design Philosophy

CleanCloud is built on three core principles:

### 1. Conservative by Default
- Explicit, documented confidence logic ([docs/confidence.md](docs/confidence.md))
- Age-based confidence thresholds (e.g., disks > 14 days = HIGH confidence)
- Multiple signals required before flagging resources
- Explicit confidence levels: LOW, MEDIUM, HIGH

### 2. Read-Only Always
- No `Delete*` permissions required
- No `Tag*` permissions required
- No modification APIs called
- Safe for production accounts

### 3. Review-Only Recommendations
- Findings are candidates for human review, not automated action
- Clear reasoning provided for each finding
- Detailed metadata included for investigation

This makes CleanCloud safe for:
- ✅ Regulated environments
- ✅ Production accounts
- ✅ Security-reviewed pipelines
- ✅ Shared infrastructure

---

## Roadmap

> Roadmap items are added only after conservative signal design and safety review.

### Coming Soon
- GCP support (read-only, parity with existing trust guarantees)
- Additional AWS rules (unused Elastic IPs, old AMIs, empty security groups)
- Additional Azure rules (unused NICs, old images)
- Rule filtering (`--rules` flag)

### Not Planned
These are intentional non-goals to preserve safety and trust.

- Automated cleanup or deletion
- Cost optimization recommendations
- Rightsizing suggestions
- Billing data access

CleanCloud will remain focused on **safe hygiene detection**, not automation or cost management.

---

## Documentation

- [`docs/infosec-readiness.md`](docs/infosec-readiness.md) - Information security readiness guide for enterprise teams
- [`security/`](security/) - IAM Proof Pack (ready-to-use policies and verification scripts)
- [`docs/rules.md`](docs/rules.md) - Detailed rule behavior and signals
- [`docs/aws.md`](docs/aws.md) - AWS setup and IAM policy
- [`docs/azure.md`](docs/azure.md) - Azure setup and RBAC configuration
- [`docs/ci.md`](docs/ci.md) - CI/CD integration examples

---

## 💬 Questions or Feedback?

We'd love to hear from you:

- 🐛 **Found a bug?** [Open an issue](https://github.com/cleancloud-io/cleancloud/issues)
- 💡 **Have a feature request?** [Start a discussion](https://github.com/cleancloud-io/cleancloud/discussions)
- 📧 **Want to chat?** Email us at suresh@sure360.io
- 🌟 **Like CleanCloud?** [Star us on GitHub](https://github.com/cleancloud-io/cleancloud)

**Using CleanCloud in production?** We'd love to feature your story!

## Contributing

Contributions are welcome! Please ensure all PRs:
- Include tests for new rules
- Follow the conservative design philosophy
- Maintain read-only operation
- Include documentation updates

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

---

## Security

CleanCloud never requires you to commit cloud credentials.
All scans run using standard AWS/Azure SDK credential resolution
(AWS profiles, env vars, or workload identity).

⚠️ Never commit secrets into this repository.

---

## License

[MIT License](LICENSE)

---