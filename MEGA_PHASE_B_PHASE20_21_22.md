# Web3Guard AI by RAADHANEX — Mega Phase B

Covers Phase 20 + Phase 21 + Phase 22 in one real-only patch.

## Phase 20 — Advanced Website URL Launch Scanner

Added safe passive launch intelligence beyond header checks:

- homepage HTML intelligence
- Web3 keyword detection: connect wallet, mint, claim, swap, stake, approve, permit, bridge, presale
- visible EVM contract address hints
- external script/domain inventory
- inline script surface warning
- API endpoint hints in public HTML
- policy/trust page link detection
- social link inventory
- homepage-only default mode
- limited same-domain checks only when ownership is verified

No exploit payloads, no form submissions, no auth bypass, and no aggressive crawl.

## Phase 21 — API Backend Deep Readiness Scanner

Added safe API readiness scanner:

- optional API base URL passive HEAD/GET checks
- OpenAPI JSON parsing
- auth/securitySchemes evidence check
- sensitive route hints: admin, withdraw, webhook, allowlist, rewards, mint
- webhook signature evidence check
- CORS evidence
- debug-mode hints
- secret-like code hints
- rate-limit and audit-log evidence checks

No fuzzing, no exploit payloads, no credential testing, no auth bypass.

## Phase 22 — Wallet Risk API Integration

Added optional read-only wallet risk integration layer:

- token address context
- spender address context
- wallet address read-only context
- approval contract context
- optional GoPlus Token Security API integration when enabled
- optional GoPlus Approval Security API integration when enabled
- disabled provider produces an explicit Not Enabled finding, never fake provider data

No wallet connection, no private key collection, no transaction signing.

## New backend endpoints

```text
GET  /scan/website-advanced/status
POST /scan/website-advanced
GET  /scan/api-deep/status
POST /scan/api-deep
GET  /scan/wallet-risk/status
POST /scan/wallet-risk
```

## New frontend pages

```text
/scanner/website-advanced
/scanner/api-deep
/scanner/wallet-risk
```

## New backend services

```text
backend/app/services/advanced_website_scan.py
backend/app/services/api_deep_readiness.py
backend/app/services/wallet_risk_integrations.py
```

## Env additions

```env
ADVANCED_WEBSITE_EXTERNAL_DOMAIN_WARNING_THRESHOLD=10
ADVANCED_WEBSITE_INLINE_SCRIPT_WARNING_THRESHOLD=8
MAX_ADVANCED_WEBSITE_SCAN_PER_HOUR=15
API_DEEP_SCAN_TIMEOUT_SECONDS=8
MAX_API_DEEP_SCAN_PER_HOUR=20
MAX_API_DEEP_OPENAPI_CHARS=220000
GOPLUS_ENABLED=false
GOPLUS_API_BASE=https://api.gopluslabs.io
GOPLUS_ACCESS_TOKEN=
WALLET_RISK_API_TIMEOUT_SECONDS=10
MAX_WALLET_RISK_API_SCAN_PER_HOUR=25
```

## Real-only status

- Missing GoPlus provider does not produce fake wallet risk data.
- Missing API URL/OpenAPI/code does not produce fake API evidence.
- Website advanced scanner only uses fetched public HTML and safe passive checks.
- Deep crawling remains locked behind ownership verification.

## Checks run

```text
Backend tests: 95 passed
Backend compile: passed
Backend smoke test: passed
Frontend typecheck: passed after npm install
Next.js build: compiled successfully, then timed out during final lint/page-data/static collection in sandbox
```
