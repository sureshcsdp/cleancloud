# CleanCloud Versioning and Stability Policy

**Version:** 1.0.0
**Effective Date:** 2026-01-23

---

## Overview

CleanCloud follows [Semantic Versioning 2.0.0](https://semver.org/) for releases and maintains a versioned JSON output schema for programmatic consumption.

This document defines our stability guarantees, breaking change policy, and migration expectations.

---

## Semantic Versioning

CleanCloud version numbers follow the format: `MAJOR.MINOR.PATCH`

### Version Components

- **MAJOR** (e.g., 1.0.0 → 2.0.0): Breaking changes that require user action
- **MINOR** (e.g., 1.0.0 → 1.1.0): New features, backward-compatible additions
- **PATCH** (e.g., 1.0.0 → 1.0.1): Bug fixes, no API changes

---

## What is Stable (1.0.0+)

Starting with version 1.0.0, CleanCloud commits to the following stability guarantees:

### ✅ Stable: CLI Interface

**Command structure, options, and exit codes are stable.**

```bash
cleancloud scan --provider aws --region us-east-1 --output json --output-file results.json
cleancloud doctor aws --region us-east-1
```

**Exit codes:**
- `0` - Success (no policy violations)
- `1` - Error (authentication, permissions, invalid arguments)
- `2` - Policy violation (findings exceed threshold)
- `3` - Permission error (insufficient cloud permissions)

**Stability promise:**
- Existing commands won't be renamed or removed
- Existing options won't change meaning or type
- Exit codes remain consistent
- New commands/options may be added (non-breaking)

---

### ✅ Stable: JSON Output Schema

**The JSON output schema is versioned and stable.**

**Schema version field:**
```json
{
  "schema_version": "1.0.0",
  "summary": {...},
  "findings": [...]
}
```

**Stability promise:**
- Field names won't change
- Field types won't change
- Required fields won't be removed
- Enum values won't change (e.g., `"low"`, `"medium"`, `"high"`)
- New optional fields may be added (non-breaking)
- Schema version increments for breaking changes

**Schema definition:** [`schemas/output-v1.0.0.json`](../schemas/output-v1.0.0.json)

---

### ✅ Stable: CSV Output Format

**The CSV output format is stable.**

**11 columns (in order):**
1. provider
2. rule_id
3. resource_type
4. resource_id
5. region
6. title
7. summary
8. reason
9. risk
10. confidence
11. detected_at

**Stability promise:**
- Column order won't change
- Column names won't change
- Existing columns won't be removed
- New columns may be added at the end (non-breaking)

**Note:** CSV is a simplified format. Use JSON for complete data including `details` and `evidence` fields.

---

## What May Change (Minor/Patch Versions)

The following changes are **non-breaking** and may occur in minor or patch releases:

### ✅ Non-Breaking: Adding New Features

- New cloud providers (e.g., GCP support in 1.1.0)
- New detection rules (e.g., `aws.s3.public-bucket` in 1.2.0)
- New optional CLI flags (e.g., `--max-age` in 1.3.0)
- New optional JSON fields (e.g., `scan_duration_seconds` in 1.4.0)
- New CSV columns at the end (e.g., `detected_by_rule_version` in 1.5.0)

### ✅ Non-Breaking: Bug Fixes

- Fixing incorrect confidence levels
- Fixing false positives/negatives in detection
- Correcting output formatting issues
- Fixing authentication bugs

### ✅ Non-Breaking: Documentation

- Clarifying existing behavior
- Adding examples
- Improving error messages

---

## What is a Breaking Change (Major Version)

The following changes require a **major version bump** (e.g., 1.x.x → 2.0.0):

### ❌ Breaking: CLI Changes

- Renaming commands (e.g., `scan` → `analyze`)
- Removing commands or options
- Changing option types (e.g., `--region` from string to choice)
- Changing exit code meanings
- Making optional flags required

### ❌ Breaking: JSON Schema Changes

- Renaming fields (e.g., `resource_id` → `id`)
- Removing fields
- Changing field types (e.g., `confidence` from string to integer)
- Changing enum values (e.g., `"high"` → `"HIGH"`)
- Restructuring nested objects

**Schema version will increment:** `"schema_version": "2.0.0"`

### ❌ Breaking: CSV Format Changes

- Changing column order
- Renaming columns
- Removing columns
- Changing data formats (e.g., dates from ISO to Unix timestamps)

---

## Deprecation Policy

When breaking changes are necessary, CleanCloud follows this deprecation timeline:

### Phase 1: Deprecation Notice (N.x.x)

- Feature marked as deprecated in documentation
- CLI shows deprecation warnings
- Feature continues to work normally
- Recommended migration path provided

**Example:**
```bash
$ cleancloud scan --old-flag value
⚠️  Warning: --old-flag is deprecated and will be removed in v2.0.0
    Use --new-flag instead: cleancloud scan --new-flag value
```

### Phase 2: Removal (N+1.0.0)

- Deprecated feature removed in next major version
- Documentation updated
- Migration guide provided

**Timeline:**
- Minimum deprecation period: **3 months** or **2 minor releases** (whichever is longer)

---

## Backward Compatibility Guarantee

### JSON Schema Compatibility

CleanCloud guarantees that:

1. **Parsers written for schema v1.0.0 will work with future 1.x.x releases**
   - New optional fields may appear but can be safely ignored
   - Existing required fields will remain present with same types

2. **Schema version increments signal breaking changes**
   - `"schema_version": "1.x"` → Compatible with v1.0.0 parsers
   - `"schema_version": "2.0.0"` → Breaking changes, update parser

### CLI Compatibility

CleanCloud guarantees that:

1. **Scripts written for v1.0.0 will work with future 1.x.x releases**
   - Existing commands and options work unchanged
   - New optional flags can be ignored

2. **Exit codes remain consistent**
   - CI/CD pipelines relying on exit codes won't break

---

## Migration Guides

When breaking changes occur, CleanCloud provides:

1. **Detailed migration guide** in `docs/migrations/`
2. **Changelog entry** explaining what changed and why
3. **Deprecation warnings** in prior minor releases
4. **Examples** of before/after usage

---

## Version Support Policy

### Active Support

- **Latest major version** (e.g., 2.x.x): Full support, all bug fixes, new features
- **Previous major version** (e.g., 1.x.x): Security fixes only for **6 months** after new major release

### End of Life

After 6 months, previous major versions reach end-of-life (EOL):
- No security fixes
- No bug fixes
- Documentation archived

**Example timeline:**
- 2026-01-23: v1.0.0 released
- 2026-08-01: v2.0.0 released → v1.x.x enters maintenance mode (security fixes only)
- 2027-02-01: v1.x.x reaches EOL → no further updates

---

## Schema Version History

### v1.0.0 (Current)

**Released:** 2026-01-23

**Schema features:**
- All 13 Finding fields (provider, rule_id, resource_type, resource_id, region, title, summary, reason, risk, confidence, detected_at, details, evidence)
- AWS-specific fields: `region_selection_mode`
- Azure-specific fields: `subscription_selection_mode`, `subscriptions_scanned`
- Enum values: lowercase strings (`"low"`, `"medium"`, `"high"`)

**Schema file:** [`schemas/output-v1.0.0.json`](../schemas/output-v1.0.0.json)

---

## Questions?

For questions about versioning policy or compatibility:

- **Email:** suresh@getcleancloud.com
- **GitHub Issues:** https://github.com/cleancloud-io/cleancloud/issues
- **Documentation:** https://docs.cleancloud.io

---

## Changes to This Policy

This versioning policy itself follows semantic versioning:
- **Clarifications** (non-breaking): Updated in-place
- **New guarantees** (stricter rules): Added via minor policy version
- **Reduced guarantees** (breaking): Require major policy version + 6-month notice
