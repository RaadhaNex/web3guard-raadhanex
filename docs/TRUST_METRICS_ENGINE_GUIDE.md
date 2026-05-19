# Trust Metrics Engine Guide — Phase 29

The Trust Metrics Engine helps founders publish safer public transparency signals without pretending to be a certified audit company.

## What it does

It separates trust signals into clear buckets:

1. **External advisory mappings**
   - OSV, NVD, GitHub Advisory, CISA KEV, manual, or other records mapped to a project.
   - These are not claimed as discovered by Web3Guard.

2. **Web3Guard-generated findings**
   - Only counted when the owner records a real Web3Guard-generated finding.
   - Counted separately from public CVEs/advisories.

3. **Community review items**
   - Useful for the Phase 23 community review layer.
   - Not a verified auditor badge.

4. **Disclosure lifecycle records**
   - Draft, sent manually, acknowledged, triaged, fix in progress, resolved, closed, or not applicable.
   - Phase 29 does not auto-send disclosures.

## API routes

- `GET /trust-metrics/status`
- `POST /trust-metrics/wording-check`
- `POST /trust-metrics/snapshots`
- `GET /trust-metrics/snapshots`
- `POST /trust-metrics/advisory-mappings`
- `GET /trust-metrics/advisory-mappings`
- `POST /trust-metrics/disclosures`
- `GET /trust-metrics/disclosures`
- `GET /trust-metrics/public-summary`

## Safe wording rules

Blocked wording examples:

- `certified audit`
- `100% secure`
- `audited by Web3Guard`
- `discovered by Web3Guard`
- `guaranteed secure`
- `exploit proof`

Recommended wording:

> Public metrics are transparency indicators for launch readiness. They are not an audit score, not a certified audit, not a guarantee of safety, and not proof that every issue has been found.

## Recommended workflow

1. Use Phase 28 provider live integrations to fetch real advisory/provider information when configured.
2. Map only verified upstream advisories or real manual records into `/trust-metrics/advisory-mappings`.
3. Record Web3Guard-generated findings separately.
4. Track disclosure lifecycle manually.
5. Use `/trust-metrics/public-summary` for safe public-facing metrics.
6. Keep Security Passport and Public Trust Page wording aligned with the safe wording guard.

## What this phase does not do

- It does not create a fake trust score.
- It does not claim certified audit status.
- It does not claim Web3Guard discovered external CVEs/advisories.
- It does not auto-send disclosures.
- It does not perform exploit automation.
- It does not collect private keys, seed phrases, mnemonics, wallet signatures, or production credentials.
