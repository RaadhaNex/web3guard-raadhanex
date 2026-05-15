# Phase 7.1 — Dashboard + Scan History Auto-Save + Project Detail

## Goal

Make the dashboard workflow real instead of static. Phase 7 created the auth/database foundation. Phase 7.1 connects saved projects, scans, and reports into a practical working dashboard flow.

## Added

### Backend

- `GET /projects/{project_id}` — project detail with scans, reports, activity, totals.
- `PATCH /projects/{project_id}` — update project notes/contact/details.
- `GET /scan-history/{scan_id}` — view saved scan payload.
- `PATCH /scan-history/{scan_id}` — update saved scan workflow status/notes.
- `GET /saved-reports/{saved_report_id}` — view saved report payload.
- `PATCH /saved-reports/{saved_report_id}` — update report status/visibility metadata.
- Project-level scan/report filtering.
- Dashboard activity feed.
- Project detail totals: scans, reports, findings, critical/high count, average score.
- Phase 7.1 migration-safe Supabase columns.

### Frontend

- Real `/dashboard/projects` project list and create form.
- Real `/dashboard/projects/[id]` project detail page.
- Real `/dashboard/scans` scan history list.
- Real `/dashboard/scans/[id]` scan detail payload/workflow page.
- Real `/dashboard/reports/[id]` saved report detail page.
- Scanner pages now include real “Save Scan” / “Save Report” dashboard actions.
- Unified URL scanner now includes “Save to Dashboard”.
- Dashboard homepage now links to project/scan/report detail pages.

## Real-only rule

- No fake project data.
- No fake scan history.
- No fake report records.
- No fake subscription status.
- No “certified audit” status.
- Saving a scan/report stores the actual result payload returned by the backend.
- Public report registry is not claimed live; report visibility is only metadata until the registry phase.

## Local storage mode

Default mode stays local JSONL files so the app can run without cloud setup:

- `backend/app/data/db/profiles.jsonl`
- `backend/app/data/db/projects.jsonl`
- `backend/app/data/db/scan_history.jsonl`
- `backend/app/data/db/saved_reports.jsonl`

## Supabase mode

The migration was updated with Phase 7.1 columns:

- `projects.description`
- `projects.owner_contact`
- `scan_history.status`
- `scan_history.notes`
- `saved_reports.scan_id`
- `saved_reports.visibility`
- `saved_reports.status`

RLS remains owner-only.

## Test commands

Backend:

```powershell
cd backend
PYTHONPATH=. pytest -q
PYTHONPATH=. python ../scripts/backend_smoke.py
python -m compileall -q .
```

Frontend:

```powershell
cd frontend
npm install --package-lock=false --no-audit --no-fund
npm run typecheck
npm run build
```

Note: In the sandbox, `npm run build` compiled successfully but timed out during the final Next.js build-trace/linting stage. Re-run locally.

## Manual QA flow

1. Start backend and frontend.
2. Open `/dashboard`.
3. Create a project.
4. Open `/scanner/unified-url`.
5. Run a URL scan.
6. Click “Save to Dashboard”.
7. Open `/dashboard/projects` and click the saved project.
8. Open `/dashboard/scans` and verify saved scan detail/payload.
9. Run a module scanner, generate report, click “Save Scan” and “Save Report”.
10. Open `/dashboard/reports/[id]` and verify report payload.
