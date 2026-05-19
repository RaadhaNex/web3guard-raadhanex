# Phase 38 — Real Scanner Depth Hardening Guide

Phase 38 raises Web3Guard toward an honest **90% pre-audit scanner coverage depth** target for a narrow assessed scope. It does **not** claim 90-99% security, 100% secure, certified audit, or audited by Web3Guard.

## What changed

- Added `/scanner-depth` backend APIs.
- Added `/scanner-depth` frontend page.
- Added a weighted scanner coverage model capped at 90%.
- Added worker readiness visibility for Slither, Aderyn, Semgrep, Foundry, Echidna, and Mythril.
- Added blocker caps so unresolved critical findings or missing core evidence keep coverage below 90%.
- Added claim checker to block unsafe wording like `99% secure`, `100% secure`, and `certified audit`.

## New backend APIs

```text
GET  /scanner-depth/status
GET  /scanner-depth/roadmap
POST /scanner-depth/coverage
POST /scanner-depth/claim-check
```

## Why the model caps at 90%

The 90% number is an evidence-coverage target, not a guarantee. Automated scanners cannot reliably catch every business-logic, economic, governance, oracle, integration, or protocol-design flaw. The system therefore caps automated pre-audit coverage at 90% and requires a disclaimer.

## Inputs counted toward coverage

| Module | Points |
|---|---:|
| Slither static analysis | 14 |
| Aderyn static analysis | 4 |
| Semgrep app/API scan | 14 |
| OSV dependency advisory lookup | 10 |
| CISA KEV matching | 6 |
| GitHub hygiene | 10 |
| Website surface | 4 |
| API surface | 4 |
| Wallet UX manual review | 4 |
| Admin OpSec manual review | 4 |
| Foundry tests | 8 |
| Echidna fuzz/invariant evidence | 6 |
| Mythril Docker symbolic analysis | 5 |
| Evidence/report completeness | 7 |

Raw module points can reach 100, but public automated coverage is capped at 90.

## Hard blockers

- Missing Slither caps depth at or below 76.
- Missing Semgrep caps depth at or below 82.
- Missing OSV caps depth at or below 80.
- Missing CISA KEV caps depth at or below 84.
- Any unresolved critical finding caps depth at or below 72.
- Three or more high findings cap depth at or below 78.

## Required safe wording

Allowed:

```text
Web3Guard provides high-depth pre-audit scanner coverage for assessed modules.
```

Blocked:

```text
99% secure
100% secure
certified audit
audited by Web3Guard
all vulnerabilities found
```

## Env direction for real 90-depth

```text
STATIC_ANALYSIS_ENABLED=true
SLITHER_ENABLED=true
SEMGREP_ENABLED=true
WORKER_EXECUTION_ENABLED=true
FOUNDRY_ENABLED=true
DEEP_ANALYSIS_ENABLED=true
ECHIDNA_ENABLED=true only with real config/properties
MYTHRIL_ENABLED=true
MYTHRIL_DOCKER_ENABLED=true
MYTHRIL_DOCKER_IMAGE=<real image>
LAUNCH_VALIDATION_NETWORK_ENABLED=true
```

Do not set these in production until the worker runtime is isolated and tested.
