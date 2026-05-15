# Phase 6.1 + 6.2 Consolidated — UI/UX Pro Polish + Deploy Launch Pack

## What this phase does

This is a larger consolidation patch, built because the chat was getting long. It combines:

1. UI/UX pro polish
2. Mobile navigation improvement
3. Real-only status visibility
4. Launch/deployment pack
5. Render/Vercel config files
6. Local run helper scripts
7. Sales launch playbook
8. Updated QA/deployment docs

## Real-only rule preserved

No future feature is presented as live.

| Area | Status |
|---|---|
| Unified URL scan | Live, real-only partial scoring |
| Smart contract scanner | Live local rule engine |
| Website scanner | Live passive scanner |
| dApp/API/Wallet/Admin | Live limited checklist/static hint scanners |
| UPI payment | Manual verification |
| Razorpay webhook | Not enabled |
| GitHub/Etherscan/Slither | Not enabled |
| Certified audit | Not offered |

## New frontend pages

```text
/launch-pack
```

## New backend endpoint

```text
GET /launch/pack
```

## New deploy files

```text
render.yaml
frontend/vercel.json
scripts/run_all_windows.ps1
scripts/run_all_linux_mac.sh
```

## What to test

1. Backend health:

```text
http://localhost:8000/health
```

2. Backend launch pack:

```text
http://localhost:8000/launch/pack
```

3. Frontend launch page:

```text
http://localhost:3000/launch-pack
```

4. Local QA page:

```text
http://localhost:3000/local-qa
```

5. Unified URL scanner:

```text
http://localhost:3000/scanner/unified-url
```

## Still not completed in this phase

These are still real MVP backlog items and must not be shown as live:

- Supabase auth/database
- Razorpay Checkout/webhook auto verification
- Server-side PDF generation
- GitHub repo scanner
- Explorer contract address scanner
- Slither/Aderyn/Semgrep integration
- Real AI provider unless backend env key is configured
- Monitoring, public registry, bug bounty, developer API

## Recommended next phase

Phase 7 should start the real SaaS base:

- Supabase Auth
- PostgreSQL tables
- scan history
- saved reports
- user dashboard
- admin roles

If payment is more urgent than auth, Phase 8 can be pulled forward for Razorpay Checkout + webhook verification.
