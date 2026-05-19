# Phase 35 — UI Cleanup + Pilot User Experience Polish Guide

## Why this phase exists

Web3Guard has many advanced security pages. That is useful for power users, but confusing for first-time founders. Phase 35 keeps features intact while making the public journey simpler.

## First-user path

1. Scanner
2. Results
3. Fix Plan
4. Report
5. Pricing
6. Dashboard
7. Docs

Advanced pages remain accessible through Docs, direct links, and operator flows.

## New endpoint map

- `GET /pilot-experience/status`
- `GET /pilot-experience/journey`
- `GET /pilot-experience/state-copy`
- `GET /pilot-experience/conversion-checklist`
- `POST /pilot-experience/feedback`
- `POST /pilot-experience/claim-check`

## Status wording model

Use these states consistently:

- `Assessed` — real evidence was produced.
- `Not assessed yet` — no evidence or lookup was provided.
- `Needs API Key` — provider exists but backend key is missing.
- `Tool Not Installed` — worker/runtime does not have the required tool.
- `Provider Not Configured` — live provider cannot run yet.
- `Manual review required` — automation should not decide this alone.

A setup gap is not a finding and not a pass.

## Feedback safety

The pilot feedback endpoint is not a support channel for secrets. It rejects likely:

- private keys
- seed phrases
- mnemonics
- secret-like raw key values

## Claim safety

The claim checker blocks unsafe launch copy such as:

- `100% secure`
- `certified audit`
- `audited by Web3Guard`
- `audit passed`
- `guaranteed secure`
- `discovered by Web3Guard`
- fake payment success wording

Safe wording example:

> Pre-audit readiness review with visible limitations and Not Assessed states.

## Next manual business step

Run 5–10 founder pilot sessions and record where users get stuck. Do not add more product pages until real feedback shows repeated need.
