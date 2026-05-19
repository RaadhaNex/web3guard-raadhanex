# Launch Final QA + Public Release Guide

Phase 30 adds the final launch command center for Web3Guard AI by RAADHANEX.

## Purpose

The goal is to help RAADHANEX decide whether Web3Guard is safe to expose to private beta, controlled public beta, or wider launch traffic. It is not an automatic approval system and does not certify security.

## Route

Frontend:

- `/launch-final`

Backend:

- `GET /launch-final/status`
- `GET /launch-final/gates`
- `GET /launch-final/public-release-checklist`
- `GET /launch-final/deploy-verification`
- `GET /launch-final/release-notes`
- `GET /launch-final/remaining-work`
- `POST /launch-final/claim-check`

## What it checks

Phase 30 aggregates and presents:

- Production deployment QA posture
- Manual public launch approval status
- Supabase live auth/database readiness
- Payment safety gating
- Safe public wording
- Provider/tool truthfulness labels
- AI code-sharing privacy gate
- Public-release checklist
- Deploy verification commands
- Safe release notes
- Remaining work after Phase 30

## Claim checker

Use `/launch-final/claim-check` before publishing:

- Landing page hero text
- Product hunt / launch posts
- Client handoff copy
- Public trust pages
- Security passport pages
- Trust metrics summaries
- Agency proposals

Blocked examples include:

- `certified audit`
- `100% secure`
- `audited by Web3Guard`
- `discovered by Web3Guard`
- `guaranteed secure`
- `hack proof`

Safer wording:

- `pre-audit launch readiness review`
- `evidence snapshot`
- `manual QA status`
- `provider configured / not configured`
- `Not Assessed`
- `requires professional audit before high-value launch`

## Required commands

```bash
cd backend
python -m pytest -q
```

```bash
cd frontend
npm run typecheck
npm run build
```

## Public launch rules

Do not launch broadly until:

- Vercel frontend latest deploy is Ready
- Render backend `/health` works
- `/launch-final/status` works on live backend
- `/production-deployment-qa/status` has no critical/high blockers
- Supabase login/signup/redirects work on the final domain
- RLS and two-user object isolation are manually verified
- Razorpay test order/signature/webhook/idempotency are verified before live mode
- Manual UPI remains admin verified only
- Legal pages and support paths are reviewed
- Uptime/error monitoring exists before marketing push

## Still not claimed

Web3Guard AI is not claiming:

- certified audit status
- 100% security
- guaranteed safety
- wallet-signing capability
- private key/seed phrase handling
- exploit automation
- fake provider output
- fake monitoring
- fake enterprise/customer proof
