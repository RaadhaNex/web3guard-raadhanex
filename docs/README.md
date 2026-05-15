# Web3Guard AI by RAADHANEX

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


## Phase 15 — Real AI Fix Assistant

New page: `/ai-fix-assistant`

New APIs:

- `GET /ai/fix-assistant/status`
- `POST /ai/fix-assistant/suggest`

The assistant gives safe patch guidance, snippets/diffs, tests, and validation steps. It never auto-applies code and never claims guaranteed fixes. If provider keys are not configured, it returns local fallback guidance and clearly reports fallback mode.

Manual setup for real provider mode is documented in `docs/PHASE15_AI_FIX_ASSISTANT.md`.


## Mega Phase C added

- Monitoring Lite: `/monitoring`, `/monitoring/status`, `/monitoring/configs`, `/monitoring/alerts`, `/monitoring/check`.
- Threat Intel Feed: `/threat-intel`, `/threat-intel/status`, `/threat-intel/feed`, `/threat-intel/admin/entries`.
- Real-only rule preserved: no fake live alerts, no fake current threat feed, no wallet signing, no private key collection.
- Optional RPC monitoring requires `MONITORING_ENABLED=true`, `MONITORING_RPC_ENABLED=true`, and chain RPC URL env values.
