# Local QA Guide — Mega Final Patch H

## Backend compile

```bash
cd backend
python -m compileall app tests main.py
```

## Backend tests

```bash
cd backend
pytest
```

Patch H focused test:

```bash
cd backend
pytest tests/test_mega_final_patch_h.py -q
```

## Frontend typecheck

```bash
cd frontend
npm install
npm run typecheck
```

If `node_modules` is missing and internet is unavailable, typecheck cannot run. Install dependencies first.

## Auth manual QA

1. Create Supabase project.
2. Run migrations from `supabase/migrations`.
3. Backend `.env`:
   - `STORAGE_MODE=supabase`
   - `SUPABASE_URL=...`
   - `SUPABASE_ANON_KEY=...`
   - `SUPABASE_SERVICE_ROLE_KEY=...`
   - `SUPABASE_JWT_VERIFY_ENABLED=true`
   - `SUPABASE_AUTH_REQUIRED=true`
4. Frontend `.env.local`:
   - `NEXT_PUBLIC_SUPABASE_URL=...`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY=...`
5. Open `/auth/signup`, create a real account, then verify `/dashboard` loads only after login.
6. Click Logout and confirm `/dashboard` redirects to login.

## Razorpay manual QA

1. Backend `.env`:
   - `PAYMENT_MODE=razorpay_or_upi_manual`
   - `RAZORPAY_ENABLED=true`
   - `RAZORPAY_KEY_ID=...`
   - `RAZORPAY_KEY_SECRET=...`
   - `RAZORPAY_WEBHOOK_SECRET=...`
2. Open `/pricing`.
3. Select Razorpay Checkout.
4. Confirm order creation returns an `order_id`.
5. Do not treat order creation as success.
6. Complete payment and verify `POST /payments/razorpay/verify` updates status only with a valid signature.
7. Configure webhook endpoint and confirm raw-body verification.

## Monitoring QA

1. Create a monitoring config for an owned contract.
2. Keep `MONITORING_RPC_ENABLED=false` and confirm check returns “ran=false” without fake alerts.
3. Set `MONITORING_RPC_ENABLED=true` and a real RPC URL.
4. Run `/monitoring/check` and verify evidence shows real RPC log output or zero alerts.

## PDF QA

1. Generate or prepare a combined report object with `report_hash`.
2. Call `POST /report/export/pdf`.
3. Confirm response header starts with `application/pdf` and file opens as PDF.

## Cleanup QA

Remove the root duplicate folder before deployment:

```bash
# from project root
rm -rf app
```

On Windows PowerShell:

```powershell
Remove-Item -Recurse -Force .\app
```

Keep `backend/app`.
