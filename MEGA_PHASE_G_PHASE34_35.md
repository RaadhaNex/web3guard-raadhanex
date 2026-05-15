# Mega Phase G — Phase 34 + 35

Web3Guard AI by RAADHANEX final MVP consolidation patch.

## Included

### Phase 34 — Platform Security Hardening
- API security headers middleware.
- Request ID header on every response.
- MVP request body size guard.
- Security hardening status endpoint.
- Data retention plan endpoint.
- Security headers preview endpoint.
- Vercel frontend security headers.
- Production caveats for Redis/Upstash, Supabase, isolated audit workers, and legal review.

### Phase 35 — Final Production Launch QA
- Production QA status endpoint.
- Final launch checklist endpoint.
- Manual account/env setup matrix.
- Frontend pages:
  - `/security-hardening`
  - `/production-qa`

## Real-only rule
This phase does **not** claim production certification, SOC2, ISO, penetration-test completion, or certified smart-contract audit. It gives a real checklist/status layer for what is configured and what still requires manual setup.

## New backend endpoints
- `GET /security-hardening/status`
- `GET /security-hardening/headers-preview`
- `GET /security-hardening/data-retention-plan`
- `GET /production-qa/status`
- `GET /production-qa/final-checklist`
- `GET /production-qa/account-setup`

## Manual work before public launch
- Replace `ADMIN_TOKEN`.
- Use exact production `FRONTEND_ORIGIN`.
- Set real UPI ID.
- Configure Razorpay key + secret + webhook secret.
- Apply Supabase migrations and verify RLS.
- Review Terms/Privacy/Refund/Responsible Use with lawyer/CA.
- Move audit tool execution to isolated worker/container before public untrusted deep scans.
- Use Redis/Upstash for multi-instance rate limiting.
- Configure Sentry/Uptime monitoring if going public.

## Local test
```powershell
cd backend
python -m compileall -q .
pytest -q
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

```powershell
cd frontend
npm install
npm run typecheck
npm run build
```
