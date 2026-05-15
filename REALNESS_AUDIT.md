# Web3Guard AI by RAADHANEX — Realness Audit

Patch: **Mega Final Patch H — Critical Real Integration + Cleanup**

## Non-negotiable rules

- No certified-audit claim.
- No “100% secure” claim.
- No fake scanner/tool/provider result.
- No private key, seed phrase, or mnemonic collection.
- No wallet signing.
- No exploit automation.
- Missing providers/tools must display an honest state: `Tool Not Installed`, `Provider Not Configured`, `Needs API Key`, `Manual`, or `Not Assessed`.

## Feature truth table

| Area | Patch H state | Honest fallback |
|---|---|---|
| Slither | Real optional execution when `STATIC_ANALYSIS_ENABLED=true`, `SLITHER_ENABLED=true`, and binary is installed/configured. | `Tool Not Installed` / env disabled informational finding. |
| Aderyn | Real optional execution when enabled and installed/configured. | `Tool Not Installed` / env disabled informational finding. |
| Semgrep | Real optional execution through local Solidity Semgrep rules if installed/enabled. | `Tool Not Installed` / env disabled informational finding. |
| Mythril | Docker/isolated-worker gated by default. Local execution is blocked unless explicitly allowed for a dedicated worker. | `Manual`, `Provider Not Configured`, or `Tool Not Installed`; no fake Mythril finding. |
| Supabase Auth | Real client auth + SSR/middleware session protection when Supabase env keys exist. | `Provider Not Configured`; no fake account/session. |
| Protected dashboard | `/dashboard/*` protected when Supabase frontend keys are configured; backend can require JWT with `SUPABASE_AUTH_REQUIRED=true`. | Provider setup message if frontend keys are missing. |
| Razorpay | Real order creation, Checkout, signature verification, and raw-body webhook verification. | `Provider Not Configured` / UPI manual admin verification. |
| PDF export | Server-side ReportLab endpoint returns `application/pdf`. | Requires a real report object; no report is fabricated. |
| Monitoring | Read-only `eth_blockNumber` + `eth_getLogs` mode when RPC env is configured/enabled. | `Provider Not Configured` or disabled note; manual admin alerts only. |
| Homepage | Hero, launch surface, sample scanner demo, clearly labelled score preview, pricing, trust/disclaimer. | No fake counters/testimonials. |
| Duplicate root `app/` | Marked for removal. `backend/app` is the only backend source of truth. | Use `DELETE_PATHS.txt` or cleanup script before deployment. |

## Production readiness reminders

1. Set backend Supabase env:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_JWT_VERIFY_ENABLED=true`
   - `SUPABASE_AUTH_REQUIRED=true`
   - `STORAGE_MODE=supabase`
2. Set frontend Supabase env:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. Run Supabase migrations in order.
4. Set Razorpay env only on backend:
   - `RAZORPAY_ENABLED=true`
   - `PAYMENT_MODE=razorpay` or `razorpay_or_upi_manual`
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `RAZORPAY_WEBHOOK_SECRET`
5. Set RPC env only for chains you monitor:
   - `MONITORING_ENABLED=true`
   - `MONITORING_RPC_ENABLED=true`
   - `ETHEREUM_RPC_URL`, `POLYGON_RPC_URL`, etc.
6. Tool execution should run only on safe developer machines or isolated workers. Do not run deep tools on a server containing secrets.
