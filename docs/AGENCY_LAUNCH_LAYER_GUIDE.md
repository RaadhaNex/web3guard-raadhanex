# Agency Launch Layer Guide

Phase 26 adds an agency/client workflow for Web3Guard AI by RAADHANEX.

## Purpose

The layer helps a founder, agency, or internal security team manage multiple client projects without pretending to be a certified audit company.

It supports:

- Client project portfolio.
- Intake requests.
- White-label report presentation settings.
- Team role playbook.
- Client handoff pack.
- Safe wording guardrails.

## Important boundaries

Web3Guard remains a pre-audit readiness command center.

Do not claim:

- “Certified audit”.
- “100% secure”.
- “Audited by Web3Guard”.
- “Verified auditor”.
- “Guaranteed secure”.

Do not collect:

- Private keys.
- Seed phrases.
- Mnemonics.
- Wallet signatures.
- Production credentials.

Do not perform unauthorized active scanning or exploit automation.

## Backend APIs

- `GET /agency-launch/status`
- `GET /agency-launch/portfolio?owner_user_id=...`
- `POST /agency-launch/clients`
- `GET /agency-launch/clients?owner_user_id=...`
- `POST /agency-launch/intake`
- `GET /agency-launch/intake?owner_user_id=...`
- `POST /agency-launch/white-label`
- `GET /agency-launch/white-label?owner_user_id=...`
- `POST /agency-launch/handoff-packs`
- `GET /agency-launch/handoff-packs?owner_user_id=...`

## Frontend route

```text
/agency-launch
```

## Production note

The current implementation is local-first JSONL like other existing workspace modules. For production, connect these records to Supabase tables and RLS policies before storing real agency/client operational data at scale.
