# Latest: Mega Phase A — Phase 17 + 18 + 19

This build adds three real-only MVP modules:

- `/scanner/launch-transparency` — Token/NFT/launch disclosure scanner
- `/scanner/contract-diff` — Old vs new Solidity diff scanner
- `/scanner/upgrade-safety` — Proxy/initializer/storage-order upgrade safety hints

No fake audit claims, no automatic fixes, no private-key collection, no wallet signing, and no certified audit wording.

See `MEGA_PHASE_A_PHASE17_18_19.md` for details.

---

# Web3Guard AI by RAADHANEX

**Latest ZIP:** Mega Phase G — Security Hardening + Final Production Launch QA.

Open after running locally:
- `http://localhost:3000/security-hardening`
- `http://localhost:3000/production-qa`


AI-assisted Web3 launch security review platform for early-stage Web3 builders.

> Web3Guard AI is a preliminary pre-audit launch readiness tool. It does not replace a full manual audit and does not claim certified security.

## Current phase

Phase 10 — SecureScore Pro Dashboard + Findings Workflow

## What is included

- Smart Contract Scanner Engine
- Website Passive Surface Scanner
- dApp Frontend Risk Scanner
- API Backend Risk Scanner
- Wallet Flow Checklist
- Founder/Admin OpSec Checklist
- Unified URL Launch Scanner
- Combined Launch Readiness Report
- Professional report exports: PDF, HTML, Markdown, JSON
- Public/private report records with hash verification
- Pricing packages + UPI manual fallback
- Razorpay order/signature/webhook foundation
- Lead capture + admin CRM
- Supabase Auth/database foundation
- Dashboard projects/scans/reports
- Organization/workspace foundation
- SecureScore Pro dashboard
- Findings workflow status tracking

## Real-only rule

- No fake audit/certified claim.
- No fake payment success.
- No fake AI output.
- No fake scan history.
- No fake finding fixes.
- No automatic production code mutation.

## Backend run

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend URL:

```text
http://localhost:8000
```

Useful Phase 10 endpoints:

```text
GET   /securescore/status
GET   /securescore/overview?user_id=local-demo-user
GET   /securescore/project/{project_id}?user_id=local-demo-user
GET   /securescore/scan/{scan_id}?user_id=local-demo-user
GET   /findings?user_id=local-demo-user
PATCH /findings/{finding_id}/workflow?user_id=local-demo-user
```

## Frontend run

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

Useful pages:

```text
/scanner/unified-url
/dashboard
/dashboard/securescore
/dashboard/findings
/dashboard/scans
/report/professional
/billing
/admin/payments
/local-qa
```

## Manual configuration

Read:

```text
docs/IMPLEMENTATION_HANDOFF.md
```

That file explains which accounts/API keys you must create and where to paste them.

## Phase 11 — GitHub Repo Scanner

Open the GitHub scanner at:

```text
http://localhost:3000/scanner/github
```

Backend endpoints:

```text
GET  /scan/github/status
POST /scan/github-repo
```

Optional backend env:

```env
GITHUB_API_TOKEN=
```

The GitHub scanner is real read-only static analysis. It does not clone, execute, install dependencies, or fake Slither/Aderyn/Mythril output.

## Phase 12 added

Contract address scanner is now available at:

```txt
/scanner/address
```

Backend endpoint:

```txt
POST /scan/contract-address
```

To enable real verified-source fetching, add backend-only:

```env
ETHERSCAN_API_KEY=your_real_etherscan_api_key
```

No private key collection, wallet signing, bytecode decompilation, or fake scan is performed.


## Phase 13 — Real Static Analysis Engine

Added optional real Slither/Aderyn/Semgrep static-analysis runner. It is disabled by default and never fakes findings. Enable with `STATIC_ANALYSIS_ENABLED=true` only after installing/configuring the tools on the backend or an isolated worker. New page: `/scanner/static-analysis`. New APIs: `GET /scan/static-analysis/status`, `POST /scan/static-analysis`.


## Phase 14 Deep Analysis

Phase 14 adds `/scanner/deep-analysis` and backend APIs for real-only Mythril/Manticore/Echidna execution. Tools are disabled by default. Install/configure tools and enable env flags before expecting real deep-analysis output. Missing tools are shown as Not Run, not fake vulnerabilities.


## Phase 15 — Real AI Fix Assistant

New page: `/ai-fix-assistant`

New APIs:

- `GET /ai/fix-assistant/status`
- `POST /ai/fix-assistant/suggest`

The assistant gives safe patch guidance, snippets/diffs, tests, and validation steps. It never auto-applies code and never claims guaranteed fixes. If provider keys are not configured, it returns local fallback guidance and clearly reports fallback mode.

Manual setup for real provider mode is documented in `docs/PHASE15_AI_FIX_ASSISTANT.md`.

## Phase 16 — Permission Map Scanner

New page:

```text
/scanner/permission-map
```

New backend endpoints:

```text
GET  /scan/permission-map/status
POST /scan/permission-map
```

This scanner maps privileged permissions from real Solidity source, ABI JSON, and manual owner/treasury/multisig/timelock facts. It does not invent role holders and never asks for private keys or seed phrases.

## Mega Phase B added

- Advanced website URL launch intelligence: `/scanner/website-advanced`
- API backend deep readiness scanner: `/scanner/api-deep`
- Optional wallet risk API integration: `/scanner/wallet-risk`

Real-only rule stays enforced: missing inputs/providers are marked as not run or not assessed; fake security data is not generated.


## Mega Phase C added

- Monitoring Lite: `/monitoring`, `/monitoring/status`, `/monitoring/configs`, `/monitoring/alerts`, `/monitoring/check`.
- Threat Intel Feed: `/threat-intel`, `/threat-intel/status`, `/threat-intel/feed`, `/threat-intel/admin/entries`.
- Real-only rule preserved: no fake live alerts, no fake current threat feed, no wallet signing, no private key collection.
- Optional RPC monitoring requires `MONITORING_ENABLED=true`, `MONITORING_RPC_ENABLED=true`, and chain RPC URL env values.


## Mega Phase D — Phase 25/26/27 Added

- Bug bounty readiness + manual triage records: `/bug-bounty`
- Public registry + hash verification + safe trust badge: `/registry`
- Developer API + hashed API keys: `/developer-api`
- API endpoint: `POST /api/v1/audit` with `X-Web3Guard-API-Key`
- Real-only rule preserved: no fake escrow, no fake certified audit badge, no fake SDK/webhook, no fake on-chain certificate.

---

## Mega Phase E — Phase 28 + 29 + 30

This ZIP adds:

- CI/CD GitHub Action templates and validator (`/cicd`)
- Learning Center + Hinglish knowledge base (`/learning`)
- Admin Super Panel v2 (`/admin/super`)

Real-only rule remains active:

- No fake CI run
- No fake certification
- No fake MRR/revenue/system uptime
- No fake queue metrics
- No fake audit/payment/AI/monitoring claims

Admin Super Panel requires backend `ADMIN_TOKEN`.

GitHub Action setup requires target repo secrets:

```text
WEB3GUARD_API_BASE_URL
WEB3GUARD_API_KEY
```


## Mega Phase F — Phase 31/32/33

Added real-only Notifications, Compliance Scanner, and Cross-chain Support.

New frontend pages:
- `/notifications`
- `/compliance`
- `/scanner/cross-chain`

New backend APIs:
- `GET /notifications/status`
- `POST /notifications/preferences`
- `POST /notifications/send`
- `GET /notifications/events`
- `GET /compliance/status`
- `POST /compliance/scan`
- `GET /compliance/scans`
- `GET /cross-chain/status`
- `POST /cross-chain/scan`
- `GET /cross-chain/scans`

Real-only note: notification providers, legal compliance conclusions, and cross-chain audit coverage are not faked. Provider delivery, legal advice, and full chain-specific audit require real external setup/manual professional review.


## Mega Phase G — Phase 34/35 Security Hardening + Final QA

Added `/security-hardening` and `/final-qa` pages plus backend readiness APIs. This phase verifies production readiness honestly: admin token rotation, CORS, Supabase/RLS/JWT, Razorpay webhook, AI privacy, deep-tool sandboxing, retention, backups, error monitoring, and final manual accounts. Missing production services are shown as action required; no fake launch approval is generated.

## Latest: Mega Final Patch H

This release is the cleaned real-only MVP package after the critical gap review.

Key points:
- Backend source of truth is `backend/app`; the old duplicate root `/app` folder is intentionally removed.
- Runtime JSONL records are emptied in this release so no old test payment/alert/scan record looks like live data.
- Check real integration readiness at `GET /final-patch-h/status`.
- Razorpay webhook aliases now include `/webhooks/razorpay`.
- Supabase login/signup are real only when `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are configured.
- Slither/Aderyn/Semgrep/Mythril/Manticore/Echidna do not fake results. They run only when installed/enabled, otherwise the UI/API must show Tool Not Installed / Not Run.

Do not claim certified audit or 100% secure. Web3Guard AI by RAADHANEX remains a preliminary launch readiness review platform.
