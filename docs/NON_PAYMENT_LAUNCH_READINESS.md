# Web3Guard AI v3.7 — Non-Payment Launch Readiness

Payment features are intentionally deferred to the final phase.

## Current rule

- Do not activate paid access from frontend-only state.
- Do not show `Paid`, `Payment successful`, `Subscription active`, or `Premium unlocked` until UPI manual verification or Razorpay webhook/signature verification exists and is tested.
- Razorpay and UPI payment collection should remain pending for now.

## What remains active

- Free URL scanner
- Saved scan/report export
- Direct PDF/HTML/Markdown/JSON export
- Solidity rule scanner and rule-based fix hints
- Dashboard scan history and project flow
- Real-only provider status

## Must verify before beta

1. Two-user BOLA/IDOR test.
2. Report export PDF/HTML/Markdown/JSON test.
3. Supabase Auth redirect URLs.
4. Supabase SMTP setup.
5. Custom domain + CSP/CORS update.
6. Feature Status page must show missing providers honestly.

## Payment final phase later

1. UPI QR + UTR/manual verification.
2. Admin verify/reject payment panel.
3. Razorpay test checkout.
4. Razorpay webhook/signature verification.
5. Payment audit log.
6. Subscription activation only after real verification.
