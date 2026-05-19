# Phase 15 — Web3Guard Sentinel: Monitoring + Vulnerability Intelligence Core

## Added
- Sentinel backend service and router.
- Sentinel status/source/intelligence endpoints.
- Manual/admin-protected advisory ingestion endpoint.
- Project alert generation from real stored projects, scans, reports, and indexed advisories.
- Admin intelligence overview.
- Responsible disclosure draft generator.
- Frontend Sentinel pages.
- Command palette Sentinel links.
- Dashboard Sentinel link.
- Backend tests.

## Safety preserved
- No unauthorized active scanning.
- No exploit automation.
- No wallet signing.
- No private key / seed phrase collection.
- No fake vulnerability counts.
- Public advisories are counted separately from Web3Guard findings.
- No certified audit or 100% secure claim.

## Tests run
Backend:
- `python -m pytest -q` → `163 passed, 1 warning`

Frontend:
- `npm run typecheck` → passed
- `npm run build` → compiled successfully, TypeScript completed, static pages generated; sandbox timed out at Next.js trace collection.

## Notes
`POST /sentinel/intelligence/ingest` requires `x-admin-token` matching `ADMIN_TOKEN`.
