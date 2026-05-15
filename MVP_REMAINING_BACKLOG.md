# Full MVP v1 Remaining Backlog

This chat's full MVP is bigger than the preliminary scanner foundation. The following items are still part of MVP backlog and must be built as real features, not fake placeholders.

## Phase 7 — Supabase Auth + Database
- Signup/login
- profiles
- organizations
- scan history
- reports
- leads
- payments
- RLS policies

## Phase 7.1 — Dashboard + Scan History
- user dashboard
- saved reports
- recent scans
- priority action list
- project list

## Phase 8 — Razorpay + UPI Subscription
- Razorpay Checkout
- UPI via Razorpay
- webhook signature verification
- payment history
- subscription access control
- invoices/GST fields

## Phase 9 — Professional Report System
- server-side PDF
- public/private report links
- report verification QR/hash
- Markdown/JSON/PDF export

## Phase 10 — SecureScore Pro Dashboard
- score ring
- severity charts
- finding status workflow
- false positive/accepted risk

## Phase 11 — GitHub Repo Scanner
- public repo scan
- Solidity/dApp/API file discovery
- package/deploy config scan

## Phase 12 — Explorer Contract Address Scanner
- Etherscan/BscScan/PolygonScan source fetch
- proxy detection
- ABI/owner/admin hints

## Phase 13 — Real Static Analysis Engine
- Slither
- Aderyn
- Semgrep
- Solhint
- result parser
- Docker worker

## Phase 14+ — Advanced MVP Modules
- AI Fix Assistant
- Permission Map
- Launch transparency modules
- Contract diff/history
- Upgrade safety
- Advanced website/API scanner
- Wallet security API integration
- Monitoring Lite
- Threat intel
- Bug bounty readiness
- Public registry/badge
- Developer API
- Learning Center
- Admin v2
- Notifications
- Compliance scanner
- Cross-chain support
- Platform security hardening


## Phase 14 deep analysis status

Deep-analysis architecture is now present. Real tool execution still requires installing Mythril/Manticore/Echidna and enabling env flags; production should use isolated workers.


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
