# Web3Guard AI by RAADHANEX — Implementation Handoff

Latest patch: **Mega Final Patch H — Critical Real Integration + Cleanup**

## Source of truth

- Backend source: `backend/app`
- Frontend source: `frontend`
- Supabase migrations: `supabase/migrations`
- Do not deploy root `/app`. It was a confusing duplicate data folder and should be removed from the final project checkout.

## Backend run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend run

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

## Real Supabase Auth flow

Frontend now uses Supabase client auth and SSR/middleware protection.

Routes:

- `/auth/signup` — real Supabase signup
- `/auth/login` — real Supabase login
- header logout button — real Supabase logout
- `/dashboard/*` — protected by middleware/layout when frontend Supabase keys are configured

Backend auth status:

- `GET /auth/status`

Backend dashboard APIs accept local dev mode unless you set:

```env
SUPABASE_JWT_VERIFY_ENABLED=true
SUPABASE_AUTH_REQUIRED=true
```

For production/private data, both flags must be true and frontend calls must send the Supabase bearer token.

## Real Razorpay flow

Routes:

- `POST /payment-intent` — creates a PaymentIntent; creates real Razorpay order when configured and selected.
- `POST /payments/razorpay/order` — explicit Patch H Razorpay-order alias.
- `POST /payments/razorpay/verify` — verifies Checkout signature server-side.
- `POST /payments/webhook/razorpay` — verifies raw request body with `X-Razorpay-Signature`.

Never mark payment success from frontend alone. Order creation is not payment success.

## Real PDF export

Routes:

- `POST /report/export/pdf` — returns `application/pdf` via ReportLab.
- `GET /report/public/{public_id}/pdf` — returns public/private report PDF if record exists and access is allowed.

PDF export requires an existing report object with `report_hash`. It does not create fake scan data.

## Tool execution

Static tools:

```env
STATIC_ANALYSIS_ENABLED=true
SLITHER_ENABLED=true
ADERYN_ENABLED=true
SEMGREP_ENABLED=true
```

Missing binaries return honest tool-status findings.

Mythril is Docker/worker-gated by default:

```env
DEEP_ANALYSIS_ENABLED=true
MYTHRIL_ENABLED=true
MYTHRIL_WORKER_REQUIRED=true
MYTHRIL_DOCKER_ENABLED=true
MYTHRIL_DOCKER_IMAGE=<preinstalled-mythril-image>
```

Do not enable local Mythril execution on a server holding secrets.

## Monitoring RPC mode

```env
MONITORING_ENABLED=true
MONITORING_RPC_ENABLED=true
ETHEREUM_RPC_URL=https://...
```

Patch H records real checks from `eth_blockNumber` and `eth_getLogs`. Manual alert ingest accepts `manual_admin` and `rpc_check`; unverified webhook-source alerts are rejected.
