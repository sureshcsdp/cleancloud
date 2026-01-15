# CleanCloud

**Trust-first cloud hygiene engine for production environments**

![PyPI](https://img.shields.io/pypi/v/cleancloud)
![Python Versions](https://img.shields.io/pypi/pyversions/cleancloud)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![GitHub stars](https://img.shields.io/github/stars/cleancloud-io/cleancloud?style=social)

CleanCloud provides **read-only, confidence-scored hygiene signals** for AWS and Azure that are safe to run in production and CI/CD pipelines. Designed for SRE and platform teams to safely identify review candidates for orphaned, untagged, or inactive cloud resources — without mutations, deletions, or optimization recommendations.

* ⚠️ **Read-only by design** - No deletions, no tag modifications, no resource changes
* ⚠️ **Policy-safe** - Conservative signals with explicit confidence levels
* ⚠️ **Privacy-first** - Zero telemetry, no phone-home, no data collection
---

## Table of Contents

- [Security & Trust](#security--trust)
- [Who This Is For](#who-cleancloud-is-and-is-not-for)
- [Enterprise & Production Use](#built-for-production--enterprise-use)
- [Quick Start](#quick-start)
- [What CleanCloud Detects](#what-cleancloud-detects)
- [Policy Enforcement](#policy-enforcement)
- [Configuration](#configuration)
- [Why Teams Choose CleanCloud](#why-teams-choose-cleancloud)
- [Design Philosophy](#design-philosophy)
- [Documentation](#documentation)

---

## Security & Trust

CleanCloud is designed for enterprise environments where security review and approval are required.

### Read-Only by Design

**No destructive permissions required:**
- ✅ Only `List*`, `Describe*`, `Get*` operations
- ❌ No `Delete*`, `Modify*`, or `Tag*` permissions
- ❌ No resource mutations or state changes
- ✅ Safe for production accounts and regulated environments

**IAM Proof Pack:** [Ready-to-use policies and verification scripts](security/) with automated safety tests

### OIDC-First Authentication

**No long-lived credentials:**
- ✅ AWS IAM Roles with GitHub Actions OIDC (recommended)
- ✅ Azure Workload Identity Federation (recommended)
- ✅ Short-lived tokens only
- ❌ No stored credentials in CI/CD

### Privacy Guarantees

**Zero telemetry, zero outbound calls:**
- ❌ No analytics or usage tracking
- ❌ No phone-home or update checks
- ❌ No data collection of any kind
- ✅ Only AWS/Azure API calls (read-only)

### Safety Regression Tests

**Multi-layer verification:**
- 🧪 Static AST analysis blocks forbidden SDK calls
- 🧪 Runtime SDK guards prevent mutations in tests
- 🧪 IAM policy validation ensures read-only access
- ✅ Runs automatically in CI for all PRs

**For InfoSec Teams:**
- 📋 [Information Security Readiness Guide](docs/infosec-readiness.md)
- 🔐 [IAM Proof Pack Documentation](docs/infosec-readiness.md#iam-proof-pack)
- 🛡️ [Threat Model & Mitigations](docs/infosec-readiness.md#threat-model)
- ✅ [Safety Test Documentation](docs/safety.md)

---

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


## Built for Production & Enterprise Use

CleanCloud is designed to be approved by security teams, not bypassed.

### Enterprise Features
- ✅ **Read-only by design** - No Delete*, Modify*, or Tag* permissions required
- ✅ **OIDC-first authentication** - AWS IAM Roles & Azure Workload Identity
- ✅ **Parallel, multi-region scanning** - Fast execution across all regions
- ✅ **CI/CD native** - Stable exit codes, JSON/CSV output, policy enforcement
- ✅ **Audit-friendly** - Deterministic output, no side effects, versioned schemas

### Stability Guarantees
- 🔒 **CLI backward compatibility** within major versions
- 🔒 **Exit codes are stable and intentional** - Never fails builds by accident
- 🔒 **JSON schemas are versioned** - Safe to parse programmatically
- 🔒 **Read-only always** - Safety regression tests in CI

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Scan completed successfully, no blocking findings |
| `1` | Configuration error, invalid region/location, or unexpected error |
| `2` | Policy violation (findings detected with `--fail-on-findings` or `--fail-on-confidence`) |
| `3` | Missing permissions or invalid credentials |

**Example:** Enforce policy on high-confidence findings only
```bash
cleancloud scan --provider aws --region us-east-1 --fail-on-confidence HIGH
```

## Quick Start

### Requirements

**Python:** 3.9 or later

**Cloud Access:**
- **AWS**: AWS CLI configured, or IAM role (for CI/CD), or environment variables
- **Azure**: Azure CLI authenticated, or Workload Identity (for CI/CD)

---

## Running Locally

Use CleanCloud locally for development, testing, and ad-hoc hygiene reviews.

### 1. Installation

```bash
pip install cleancloud
```

### 2. Set Up Credentials

**AWS:**
```bash
export AWS_ACCESS_KEY_ID=<your-access-key>
export AWS_SECRET_ACCESS_KEY=<your-secret-key>
export AWS_DEFAULT_REGION=us-east-1
```

**Azure:**
```bash
export AZURE_CLIENT_ID=<your-client-id>
export AZURE_TENANT_ID=<your-tenant-id>
export AZURE_CLIENT_SECRET=<your-client-secret>
export AZURE_SUBSCRIPTION_ID=<your-subscription-id>
```

> **Alternative methods:** AWS CLI profiles and Azure CLI are also supported. See [Configuration](#configuration) for details.

### 3. Validate Credentials

```bash
# AWS - validate credentials and permissions
# Defaults to us-east-1 if --region not specified
cleancloud doctor --provider aws
cleancloud doctor --provider aws --region us-west-2

# Azure - validate credentials and subscription access
# Note: --region parameter is not applicable for Azure doctor
cleancloud doctor --provider azure
```

### 4. Run a Scan

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

### 5. View Results

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

## Running in CI/CD Pipelines

CleanCloud is designed for CI/CD environments with OIDC authentication (no secrets required).

### Requirements for CI/CD

**Python:** 3.9 or later (usually pre-installed in GitHub Actions runners)

**Authentication:**
- **AWS**: IAM Role with OIDC trust relationship (GitHub Actions recommended)
- **Azure**: Workload Identity Federation (Microsoft Entra ID recommended)

**Key Differences from Local Usage:**
- Uses OIDC (OpenID Connect) instead of CLI credentials
- No long-lived secrets stored in CI
- Designed for policy enforcement via exit codes (`--fail-on-confidence`)

### Quick Example: GitHub Actions with AWS

```yaml
permissions:
  id-token: write  # Required for OIDC
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

      - name: Run CleanCloud scan
        run: |
          pip install cleancloud
          cleancloud scan \
            --provider aws \
            --region us-east-1 \
            --output json \
            --output-file scan.json \
            --fail-on-confidence HIGH
```

### Quick Example: GitHub Actions with Azure

```yaml
permissions:
  id-token: write  # Required for OIDC
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

      - name: Run CleanCloud scan
        run: |
          pip install cleancloud
          cleancloud scan \
            --provider azure \
            --output json \
            --output-file scan.json \
            --fail-on-confidence HIGH
```

**Complete CI/CD documentation:** See [`docs/ci.md`](docs/ci.md) for detailed setup instructions.

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

## Configuration

### AWS Authentication

**Local Development:**
```bash
export AWS_ACCESS_KEY_ID=<your-access-key>
export AWS_SECRET_ACCESS_KEY=<your-secret-key>
export AWS_DEFAULT_REGION=us-east-1

cleancloud scan --provider aws --region us-east-1
```

**CI/CD:**
- Use GitHub Actions OIDC (see [Running in CI/CD Pipelines](#running-in-cicd-pipelines))
- Requires IAM role with read-only permissions

**IAM Permissions:**
- Only `List*`, `Describe*`, `Get*` operations required
- No `Delete*`, `Modify*`, or `Tag*` permissions
- Full policy and alternative auth methods: [`docs/aws.md`](docs/aws.md)

---

### Azure Authentication

**Local Development:**
```bash
export AZURE_CLIENT_ID=<your-client-id>
export AZURE_TENANT_ID=<your-tenant-id>
export AZURE_CLIENT_SECRET=<your-client-secret>
export AZURE_SUBSCRIPTION_ID=<your-subscription-id>

cleancloud scan --provider azure
```

**CI/CD:**
- Use Azure Workload Identity Federation (see [Running in CI/CD Pipelines](#running-in-cicd-pipelines))
- Requires `Reader` role at subscription scope

**Permissions:**
- Only read-only access required
- No write, delete, or tag permissions
- Full setup guide and alternative auth methods: [`docs/azure.md`](docs/azure.md)

**Subscription Filtering:**
```bash
# Default: scan all accessible subscriptions
cleancloud scan --provider azure

# Scan specific subscriptions
cleancloud scan --provider azure --subscription <sub-id-1> --subscription <sub-id-2>
```

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

## Why Teams Choose CleanCloud

### Automation Over Manual Reviews

**Cloud portals** provide visibility into resource state - what exists, what's untagged, what's unattached.

**CleanCloud** provides **evaluation and automation** - applying judgement, confidence scoring, and enabling policy enforcement in CI/CD pipelines.

| Need | Cloud Portal | CleanCloud |
|------|--------------|------------|
| **Inventory & dashboards** | ✅ Excellent | ➖ Not a goal |
| **Hygiene evaluation** | ❌ Manual only | ✅ Automated |
| **CI/CD integration** | ❌ Not designed for it | ✅ Purpose-built |
| **Confidence scoring** | ❌ Binary yes/no | ✅ LOW/MEDIUM/HIGH |
| **Deterministic output** | ❌ UI-driven | ✅ Versioned schemas |

### CleanCloud Complements Your Cloud Portal

- Use **cloud portals** to explore and investigate resources
- Use **CleanCloud** to evaluate hygiene risks, automate checks, and enforce policy

> **The portal shows you what exists.**
> **CleanCloud tells you what matters.**

**Learn more:** [Where CleanCloud Fits (design diagram)](docs/design.md#where-cleancloud-fits)

---

## Design Philosophy

CleanCloud is built on three core principles:

**1. Conservative by Default** - Multiple signals with explicit confidence levels (LOW/MEDIUM/HIGH) reduce false positives

**2. Read-Only Always** - No Delete*, Tag*, or Modify* permissions; safe for production

**3. Review-Only Recommendations** - Findings are candidates for review, not automated action

**Learn more:** [Confidence logic documentation](docs/confidence.md)

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
- 📧 **Want to chat?** Email us at suresh@getcleancloud.com
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

## License

[MIT License](LICENSE)

---