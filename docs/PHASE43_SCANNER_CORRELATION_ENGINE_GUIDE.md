# Phase 43 — Scanner Correlation + Exploitability Prioritization Engine

## Goal

Phase 43 makes Web3Guard more advanced by adding a correlation layer above individual scanners.

It does not claim to find every bug. It takes evidence from configured scanners and project context, then prioritizes what is most dangerous before launch.

## New route

Frontend:

- `/scanner-correlation`

Backend:

- `GET /scanner-correlation/status`
- `GET /scanner-correlation/playbook`
- `POST /scanner-correlation/prioritize`
- `POST /scanner-correlation/attack-path`
- `POST /scanner-correlation/claim-check`

## What it correlates

- Slither / Aderyn / smart contract static findings
- Semgrep / app-layer findings
- OSV / NVD / CISA KEV / CVE evidence
- OpenZeppelin-style pattern intelligence
- Authorized Web DAST baseline evidence
- Manual project context such as internet exposure, funds/value, public PoC, known exploited status

## New scoring behavior

The engine produces:

- P0 / P1 / P2 / P3 priority
- 0–100 priority score
- correlation reasons
- attack-path templates
- future risk
- fix plan
- verification steps
- coverage gaps

This is not a fake security score. It is a launch-readiness priority score.

## Safe boundaries

Blocked:

- exploit execution
- brute force
- credential stuffing
- password spraying
- DoS/stress testing
- RCE exploitation
- file deletion/write
- data extraction
- wallet signing
- private key/seed collection
- all-bug guarantee
- certified audit claims

## Safe wording

Use:

> Web3Guard correlates configured scanner evidence, CVE/CWE context, and project exposure into prioritized pre-audit risks. It does not perform destructive exploitation, does not guarantee that all bugs are found, and does not replace a professional audit.

Do not use:

- Finds all bugs
- 100% secure
- Certified audit
- Audited by Web3Guard
- Exploit scanner
- Hack any website

## Why this makes the scanner more advanced

Before Phase 43, different modules could produce separate findings. Phase 43 connects them and answers:

1. Which finding should block launch?
2. Which finding can chain with other issues?
3. Which asset is internet-exposed?
4. Which issue affects money/payment/token/admin control?
5. Which issue is known exploited or CVE-linked?
6. Which modules were not assessed?
7. What should the founder fix first?

## Validation

Backend:

```bash
cd backend
python -m pytest -q
```

Frontend:

```bash
cd frontend
npm install
npm run typecheck
npm run build
```
