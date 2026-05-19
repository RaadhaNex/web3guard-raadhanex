# Patch File List

Only these files are included in this patch ZIP. No environment files, secrets, Supabase data rows, payment data, node_modules, or build output are included.

- `BUG_BOUNTY_READINESS_GUIDE.md`
- `COMPETITOR_FEATURE_MAP.md`
- `EXTERNAL_SETUP_GUIDE.md`
- `FREE_VALUE_FEATURES.md`
- `PATCH_FILE_LIST.md`
- `PHASE_SUMMARY.md`
- `PRE_AUDIT_PACK_GUIDE.md`
- `PUBLIC_BETA_LAUNCH_CHECKLIST.md`
- `backend/app/routers/public_beta.py`
- `backend/app/routers/scans.py`
- `backend/app/services/professional_report.py`
- `backend/app/services/public_beta_readiness.py`
- `backend/app/services/unified_url_scan.py`
- `backend/main.py`
- `frontend/app/changelog/page.tsx`
- `frontend/app/feature-status/page.tsx`
- `frontend/app/free-tools/page.tsx`
- `frontend/app/globals.css`
- `frontend/app/launch-readiness/page.tsx`
- `frontend/app/limitations/page.tsx`
- `frontend/app/methodology/page.tsx`
- `frontend/app/page.tsx`
- `frontend/app/privacy/page.tsx`
- `frontend/app/sample-reports/page.tsx`
- `frontend/app/security/page.tsx`
- `frontend/app/terms/page.tsx`
- `frontend/components/layout/Header.tsx`
- `frontend/components/scanner/UnifiedUrlScannerClient.tsx`
- `frontend/components/sections/Hero.tsx`
- `frontend/components/tools/FreeToolsClient.tsx`
- `frontend/components/ui/TrustPage.tsx`
- `frontend/lib/publicBetaContent.ts`
- `frontend/lib/types.ts`

## Notes
- Root markdown files are public beta documentation and apply/deploy guides.
- Backend changes add honest public beta readiness status and improve report score split/export structure.
- Frontend changes add trust pages, free tools, readiness pages, split-score display, and lightweight futuristic UI polish.
- Payment/Razorpay/UPI remains deferred and is not activated by this patch.
