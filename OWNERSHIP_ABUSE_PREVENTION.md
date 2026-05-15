# Phase 5.9 — Ownership + Abuse Prevention

Web3Guard AI by RAADHANEX is a defensive pre-audit launch readiness platform. Phase 5.9 adds a clear ownership-verification architecture and abuse-prevention boundary so future deeper scans can require proof of authorization.

## What is real in Phase 5.9

- `GET /ownership/policy` returns the allowed scan modes and blocked abuse actions.
- `GET /ownership/methods` explains DNS TXT and `.well-known` verification.
- `POST /ownership/challenge` creates a verification challenge for a public website domain.
- `POST /ownership/verify` verifies the token by DNS TXT or `.well-known/web3guard-verify.txt`.
- Private/internal hosts remain blocked by backend URL validation.
- Contract/checklist/website scan endpoints require authorization confirmation.
- Rate limits now cover contract, website, dApp, API, wallet, and admin OpSec modules.

## Verification methods

### 1. Well-known file verification

The user creates this public file:

```text
/.well-known/web3guard-verify.txt
```

The file must contain the exact generated token.

Best for:
- staging sites
- fast MVP owner proof
- small teams with hosting access

### 2. DNS TXT verification

The user creates this DNS TXT record:

```text
_web3guard.example.com TXT web3guard-raadhanex-verify-<token>
```

Best for:
- production domain ownership proof
- larger teams
- future paid review workflows

DNS TXT verification uses optional runtime resolver support. If local DNS TXT verification is not available, use `.well-known` file verification first.

## What ownership verification does NOT mean

Ownership verification does not mean:

- Web3Guard AI certified the project
- the project is fully secure
- the project has passed a professional audit
- deep scanning is automatically enabled in MVP
- RAADHANEX guarantees safety

It only proves the requester controls the domain or can place a verification token.

## Blocked actions

Web3Guard AI must not perform:

- exploit automation
- credential testing
- login bypass attempts
- brute force crawling or wordlists
- destructive testing
- payload spraying
- internal/private network scans
- seed phrase/private key collection
- attacks against third-party projects

## Current scan modes

MVP allowed modes are:

1. user-submitted Solidity/code scanning
2. safe passive website `GET`/`HEAD` checks
3. checklist-based dApp/API/wallet/admin review
4. owner verification challenge generation

Deep website/API scans remain future-only until verified authorization and written scope exist.

## Production upgrade path

For production, move these items from MVP/simple mode to robust infra:

- move in-memory rate limits to Redis/Upstash
- store ownership challenges in Supabase/PostgreSQL
- add signed verification tokens with expiry
- add admin evidence review
- add audit log for all verification attempts
- add per-user/IP/org scan limits
- require auth before deep scan
- add terms acceptance timestamp
