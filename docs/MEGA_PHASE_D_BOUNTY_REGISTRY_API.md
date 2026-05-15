# Mega Phase D — Bug Bounty, Registry, Developer API

## Phase 25 — Bug Bounty Readiness

The bounty module stores real scope, safe-harbor, reward-tier, contact, and submission records. It is not a real escrow or payout platform yet.

### Important wording

Use: `Bug bounty readiness program` or `Manual triage program`.

Do not use: `Escrow protected`, `automatic payout`, `validated bug bounty`, unless those systems are actually connected.

## Phase 26 — Public Registry + Badge

The registry publishes real report metadata and verifies a report hash. It generates a safe trust-badge payload with the label:

`Pre-audit readiness reviewed`

Do not call it a certified audit, audit certificate, guaranteed secure badge, or insurance badge.

## Phase 27 — Developer API

API keys are created once and stored only as SHA-256 hashes. `/api/v1/audit` currently supports rule-engine Solidity scans from supplied code. It does not fake Slither/Aderyn/AI/monitoring results.

### Header

```text
X-Web3Guard-API-Key: wg_...
```

### Create key

```http
POST /developer-api/keys
```

### Run audit

```http
POST /api/v1/audit
```

### Verify public registry record

```http
GET /api/v1/certificate/{public_id}?report_hash=<hash>
```

## Manual accounts/services needed later

- Production domain for badge URLs.
- Email provider for bounty notifications.
- Legal review for safe harbor/scope.
- Real payment/escrow provider before enabling escrow.
