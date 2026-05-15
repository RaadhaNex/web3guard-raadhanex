# Mega Phase G — Platform Security Hardening + Final Production Launch QA

This phase combines Phase 34 and Phase 35. It is the final hardening/QA layer before a controlled beta/public deployment.

## Added

- `/security-hardening` frontend page
- `/final-qa` frontend page
- `/security/status` production hardening checks
- `/security/headers-policy` recommended deployment headers
- `/security/data-retention` configured retention policy
- `/security/boundaries` real-only safety boundary matrix
- `/final-qa/status` final launch readiness summary
- `/final-qa/manual-accounts` manual account/env checklist
- `/final-qa/implementation-map` what is real now vs manual setup needed

## Real-only behavior

This phase does not fake production readiness. Missing Supabase, Razorpay, CORS, monitoring, backup, Sentry, or admin-token setup is shown as action required.

## Manual before public launch

1. Rotate `ADMIN_TOKEN`.
2. Set `APP_ENV=production`.
3. Set `FRONTEND_ORIGIN=https://your-domain`.
4. Apply Supabase migrations and enable RLS/JWT checks.
5. Configure Razorpay keys and webhook secret.
6. Configure backup/error/uptime monitoring.
7. Review Terms/Privacy/Refund with lawyer/CA.
8. Run local frontend `npm run build` and backend tests.
9. Confirm no fake audit/payment/AI wording appears in public pages.

## Still not automatic

- Final production approval is manual.
- Legal review is manual.
- Payment settlement/refunds are manual/admin verified unless Razorpay webhook confirms.
- Critical scanner findings still need human review.
