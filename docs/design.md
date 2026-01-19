# CleanCloud Design & Positioning

CleanCloud is a **cost optimization tool** built for production and staging environments.

It exists to answer one question safely:

> What orphaned resources are costing us money — without risking production?

---

## Where CleanCloud Fits
```
                         ┌──────────────────────────────┐
                         │     Native Cloud Services    │
                         │   (Config / TA / Policies)   │
                         │                              │
                         │   • Binary alerts            │
                         │   • Service-specific         │
                         │   • Account / org scoped     │
                         └───────────────▲──────────────┘
                                         │
                                         │
          Noisy / Shallow                │               Automated / Risky
                                         │
─────────────────────────────────────────┼─────────────────────────────────────────
                                         │
                                         │
                         ┌───────────────┴──────────────┐
                         │          CleanCloud          │
                         │                              │
                         │   • Read-only                │
                         │   • Review-only findings     │
                         │   • Multiple conservative    │
                         │     signals                  │
                         │   • Explicit confidence      │
                         │     levels (H/M/L)           │
                         │   • IaC-aware                │
                         │   • CI-friendly              │
                         │                              │
                         │ "Safe to review, never act"  │
                         └───────────────▲──────────────┘
                                         │
                                         │
                         ┌───────────────┴──────────────┐
                         │    Cleanup / Automation Tools│
                         │                              │
                         │   • Auto-delete              │
                         │   • Rightsizing              │
                         │   • Cost-driven actions      │
                         │   • Mutation by default      │
                         └──────────────────────────────┘
```
---

**CleanCloud sits in the "trust zone":**
- Cost optimization through safe, read-only hygiene detection
- Unlike native cloud services (too noisy/shallow) or automation tools (too risky for production)

## Design Principles

### 1. Review-Only by Design
CleanCloud never modifies, deletes, or tags resources.
All findings are **candidates for human review**, not automated action.

### 2. Conservative Signals
Each rule combines multiple signals (state, age, attachment, usage metadata)
to avoid false positives in IaC-driven environments.

### 3. Explicit Confidence
Findings are classified as LOW / MEDIUM / HIGH confidence
to support safe decision-making in production.

### 4. IaC-Aware
CleanCloud assumes infrastructure is ephemeral, declarative,
and frequently recreated — not manually curated.

---

## What CleanCloud Is Not

- Not an automated cleanup engine (one-click account nuking)
- Not a rightsizing or instance optimization tool
- Not a spending analysis dashboard
- Not a replacement for Config, TA, or policies

CleanCloud is a **cost optimization tool** built on safe, read-only hygiene evaluation.
