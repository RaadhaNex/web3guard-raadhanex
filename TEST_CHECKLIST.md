# Phase 8 Update — Razorpay + UPI Subscription System

- Added real Razorpay order/signature/webhook architecture.
- Added UPI manual fallback without fake payment success.
- Added admin payments dashboard and billing status page.
- Added subscription records activated only after verified/admin-approved payment.
- Added Supabase migration `003_phase8_payments_subscriptions.sql`.

# Phase 3 Test Checklist

## Backend
- [ ] `py -3.12 -m venv .venv`
- [ ] `pip install -r requirements.txt`
- [ ] `copy .env.example .env`
- [ ] `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- [ ] Open `/health`
- [ ] Open `/ai/status`
- [ ] POST `/scan/contract`
- [ ] POST `/report/combined`

## Frontend
- [ ] `npm install`
- [ ] `copy .env.local.example .env.local`
- [ ] `npm run dev`
- [ ] Open `/scanner/contract`
- [ ] Load vulnerable sample
- [ ] Run scan
- [ ] Generate report
- [ ] Print/save as PDF
- [ ] Open `/report`

## Safety
- [ ] No certified audit claim
- [ ] AI fallback shown when AI disabled
- [ ] Report disclaimer visible
- [ ] Manual review recommendation visible for high/critical issues

## Automated tests
```powershell
cd backend
$env:PYTHONPATH="."
pytest -q
```

Expected:
```text
6 passed
```

## Phase 5.5 Website Scanner Tests

Backend:
```bash
cd backend
PYTHONPATH=. pytest -q
python -m compileall -q .
```

Manual website scanner checks:
1. Open `/scanner/website`.
2. Test `https://example.com`.
3. Confirm results show score, severity counts, header status, robots/sitemap, and passive evidence.
4. Test `http://localhost:8000` and confirm it is blocked.
5. Uncheck authorization checkbox and confirm scan button is disabled / backend rejects unauthorized request.
6. Confirm findings clearly say preliminary/passive review only.
7. Confirm no payment success is shown without manual UPI verification.


## Phase 5.6 dApp/API Scanner Tests

Backend:
```powershell
cd backend
$env:PYTHONPATH='.'
pytest -q
```

Expected:
```text
18 passed
```

Manual checks:
- Open `/scanner?module=dapp` or scanner UI route for dApp module.
- Paste frontend code containing `NEXT_PUBLIC_ADMIN_API_KEY`, hardcoded RPC URL, EVM address, `dangerouslySetInnerHTML`, and `MaxUint256`.
- Confirm findings are generated with severity breakdown and priority actions.
- Paste package.json with WalletConnect/web3modal v1 dependencies and confirm dependency review finding.
- Open API scanner.
- Use `http://localhost:8000` as API base URL and confirm it is blocked.
- Use a public URL and pasted config with wildcard CORS/debug/hardcoded secret and confirm API findings.
- Confirm UI states clearly say static hints only and no exploit/fuzzing.


## Phase 5.7 Wallet/Admin Scanner Tests

Backend:
```powershell
cd backend
$env:PYTHONPATH='.'
pytest -q
python -m compileall -q .
```

Expected:
```text
21 passed
```

Manual checks:
- Open `/scanner/wallet`.
- Confirm checklist has approval, Permit2, blind-signing, chain, spender, preview, and prompt items.
- Keep the sample notes containing `MaxUint256`, `Permit2`, prompt on page load, and chain mismatch; run scan.
- Confirm high/medium findings and Phase 5.7 evidence card appear.
- Open `/scanner/admin-opsec`.
- Keep sample notes containing single owner, no multisig, no timelock, private key in `.env`, Telegram, missing MFA, and upgradeable proxy; run scan.
- Confirm critical findings and readiness map appear.
- Confirm UI clearly states no wallet connection, no transaction signing, and no private-key/seed phrase collection.


## Phase 5.8 report test checklist

- [ ] Generate a report from only Smart Contract scan and confirm it says partial score.
- [ ] Confirm missing modules are listed.
- [ ] Generate a report with all six module responses via API and confirm `overall_score` exists.
- [ ] Confirm report has a 64-character verification hash.
- [ ] Confirm priority actions include cross-module critical/high findings.
- [ ] Confirm Markdown download works.
- [ ] Confirm JSON download works.
- [ ] Confirm Print / Save PDF opens browser print.
- [ ] Confirm public sharing wording says pre-audit readiness, not certified audit.
- [ ] Confirm forbidden phrases are visible in client delivery metadata.

---

## Phase 5.9 Tests

Backend:

- `GET /ownership/policy` returns blocked actions and consent text.
- `POST /ownership/challenge` rejects `localhost` and private/internal hosts.
- `POST /ownership/challenge` creates DNS TXT and `.well-known` challenges.
- `POST /ownership/verify` verifies a valid `.well-known` token.
- Scanner endpoints still reject `authorization_confirmed=false`.
- Rate limiter can reset in tests.

Frontend manual test:

1. Open `/ownership-verification`.
2. Enter a public URL.
3. Select `.well-known` verification.
4. Generate challenge.
5. Confirm instructions show token and URL.
6. Verify against a real hosted token when available.
7. Confirm failed verification shows evidence and safe next steps.


# Phase 6 Local QA Checklist

## Backend

- [ ] `pip install -r requirements.txt` works.
- [ ] `python -m compileall -q .` passes from backend folder.
- [ ] `PYTHONPATH=. pytest -q` passes.
- [ ] `python ../scripts/backend_smoke.py` passes with venv active.
- [ ] `/health` returns `ok: true`.
- [ ] `/health/readiness` returns zero failed checks.
- [ ] `/qa/runbook` lists routes/endpoints.

## Frontend

- [ ] `npm install` works.
- [ ] `.env.local` contains `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.
- [ ] `npm run dev` works.
- [ ] `/local-qa` loads backend readiness data.
- [ ] No horizontal overflow on scanner, pricing, report, and admin pages.

## Realness

- [ ] No fake certified audit wording.
- [ ] No fake AI result when AI is disabled.
- [ ] UPI says manual verification required.
- [ ] Contract address-only unified scan does not create fake contract score.
- [ ] Missing modules show `Not assessed` or manual input required.

## Admin/payment

- [ ] `/admin/leads` blocks unauthenticated access.
- [ ] `/admin/leads` works with `ADMIN_TOKEN`.
- [ ] `/admin/leads.csv` exports.
- [ ] Payment intent creates UPI deep link but does not mark payment verified automatically.


## Phase 9 professional report tests

- [ ] Generate a combined report via `/report/combined`.
- [ ] Paste the report JSON into `/report/professional`.
- [ ] Build artifacts and confirm HTML preview appears.
- [ ] Download PDF and confirm it opens.
- [ ] Download HTML/Markdown/JSON.
- [ ] Publish a private report record.
- [ ] Publish a public report record only after reviewing sensitive details.
- [ ] Verify report hash using `/report/public/{id}/verify?report_hash=...`.
- [ ] Confirm public wording does not say certified audit or 100% secure.


## Mega Phase G tests
- [ ] `GET /security-hardening/status` returns hardening checks.
- [ ] `GET /security-hardening/headers-preview` returns security headers.
- [ ] `GET /production-qa/status` returns final QA status.
- [ ] `GET /production-qa/account-setup` lists Supabase/Razorpay/UPI/legal/manual accounts.
- [ ] `/health` response contains `X-Request-ID` and security headers.
- [ ] Oversized request body returns 413.
- [ ] Frontend `/security-hardening` opens.
- [ ] Frontend `/production-qa` opens.
- [ ] No page says certified audit / 100% secure / fake payment success.
