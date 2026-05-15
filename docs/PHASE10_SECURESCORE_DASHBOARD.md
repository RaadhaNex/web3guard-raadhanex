# Phase 10 — SecureScore Pro Dashboard + Findings Workflow

## What is live in this phase

Phase 10 adds a real SecureScore workflow layer on top of saved scans. It does not invent fake audit results.

Live backend APIs:

- `GET /securescore/status`
- `GET /securescore/overview?user_id=...`
- `GET /securescore/project/{project_id}?user_id=...`
- `GET /securescore/scan/{scan_id}?user_id=...`
- `GET /findings?user_id=...`
- `PATCH /findings/{finding_id}/workflow?user_id=...`

Live frontend pages:

- `/dashboard/securescore`
- `/dashboard/findings`

Live workflow:

1. Run a real scanner.
2. Save the scan to dashboard.
3. Open SecureScore dashboard.
4. Review score, severity breakdown, module cards, and top open findings.
5. Open findings workflow.
6. Change finding status manually: `open`, `in_progress`, `fixed`, `false_positive`, `accepted_risk`, or `needs_manual_review`.

## Real-only boundary

- No fake findings are created.
- No fake score trend is created.
- No fake remediation status is created.
- No source code is automatically changed.
- A finding is marked fixed only when the user/reviewer changes the workflow status.
- Automatic code patching is reserved for a later AI Fix Assistant phase and must require user approval.

## Current storage

Default mode stores finding workflow statuses in:

```text
backend/app/data/db/finding_workflow.jsonl
```

Supabase-ready migration:

```text
supabase/migrations/005_phase10_securescore_workflow.sql
```

## Manual work required from user

For local test:

- Nothing extra required.
- Run backend and frontend normally.
- Save scans from scanner pages first.

For production/Supabase:

- Run migration `005_phase10_securescore_workflow.sql` after previous migrations.
- Set Supabase environment variables.
- Keep `SUPABASE_JWT_VERIFY_ENABLED=true` only after real Supabase Auth is configured.

## Not included yet

- AI automatic patch generation.
- Direct GitHub PR patching.
- Slither/Aderyn real tool findings.
- Live contract-address explorer findings.

These are separate real integration phases.
