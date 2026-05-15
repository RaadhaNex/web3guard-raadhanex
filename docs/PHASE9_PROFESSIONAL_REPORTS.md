# Phase 9 — Professional PDF / Public Report System

## What is live

Phase 9 upgrades reports from browser-print-only delivery to a real backend report delivery system.

Live endpoints:

- `GET /report/delivery-policy`
- `POST /report/professional`
- `POST /report/artifacts`
- `POST /report/export/pdf`
- `POST /report/export/html`
- `POST /report/export/markdown`
- `POST /report/export/json`
- `POST /report/publication`
- `GET /report/public`
- `GET /report/public/{public_id}`
- `GET /report/public/{public_id}/verify?report_hash=...`
- `GET /report/public/{public_id}/html`
- `GET /report/public/{public_id}/pdf`

Frontend pages:

- `/report`
- `/report/professional`
- `/report/public`

## What changed

1. Branded professional HTML report generation.
2. Real server-side PDF bytes using ReportLab.
3. Markdown and JSON export endpoints.
4. Public/private report record storage.
5. Hash verification endpoint.
6. Public-safe wording policy.
7. Supabase migration for future `public_reports` table.

## Real-only boundary

This report system does not add fake audit claims. It only formats the report object generated from actual scanned/checklist/passive-scan data.

Allowed public wording:

> Pre-audit readiness reviewed by Web3Guard AI by RAADHANEX

Blocked wording:

- Certified audit
- 100% secure
- Insurance guaranteed
- Exploit-proof

## PDF status

PDF generation is now real backend output. It is not only browser print. The PDF is generated from the same combined report object and includes:

- report ID
- verification hash
- score/risk summary
- module matrix
- priority action plan
- top findings
- limitations
- disclaimer

## Public report status

Public records are real JSONL records in local mode and Supabase-ready via migration. Public links must be reviewed before sharing because findings can contain sensitive details.

## Testing

Backend tests added:

- delivery policy real-only status
- professional artifacts generation
- server PDF byte generation
- HTML export
- publication record creation
- hash verification pass/fail

Run:

```powershell
cd backend
PYTHONPATH=. pytest -q
```

## Limitations

- PDF visual design is professional MVP, not Big-4/enterprise final template yet.
- Public report frontend dynamic detail page is backend-ready, but full branded public detail UI can be expanded later.
- Supabase adapter for public reports is migration-ready; local JSONL remains default for easy testing.
