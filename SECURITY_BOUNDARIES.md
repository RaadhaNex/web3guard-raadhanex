# Security Boundaries

Web3Guard AI by RAADHANEX must stay legally safe and abuse-resistant.

## Allowed in MVP

- User-submitted smart contract code scanning
- Passive public website checks
- Checklist-based dApp/API/wallet/admin review
- Founder-friendly risk explanations
- Paid manual review funnel

## Not allowed

- Exploit automation
- Brute force
- Credential testing
- Bypass attempts
- Destructive tests
- Unauthorized deep scans
- Scanning internal/private IPs
- Aggressive crawling

## Website scan rules

- Only `http` and `https`
- Block localhost/internal/private IP ranges
- HEAD/GET only
- Timeout all requests
- No brute-force wordlists
- Limited public path hints only
- Require authorization checkbox

## Future ownership verification

- DNS TXT: `web3guard-verify=<token>`
- File: `/.well-known/web3guard-verify.txt`
- Wallet signature verification
- GitHub repo ownership check

## Phase 5.5 Website Scanner Boundaries

The website scanner must remain passive by default.

Allowed:
- GET homepage
- HEAD robots/sitemap and limited fixed path hints
- Read public response headers
- Read limited public homepage HTML up to configured max body size
- Validate redirects before following
- Block private/internal IP ranges

Not allowed:
- Exploit payloads
- SQLi/XSS payload testing
- Credential stuffing
- Password guessing
- Directory brute-force wordlists
- Auth bypass
- Writing data to target
- High-frequency crawling
- Scanning localhost/private/internal networks

Deep scan is future-only and must require ownership verification.


## Phase 5.6 dApp/API Scanner Boundaries

The dApp frontend scanner is static-hints-only. It may parse pasted code snippets and package.json text, but it does not install packages, execute frontend code, connect wallets, sign messages, or simulate live transactions.

The API backend scanner is checklist + static-hints-only. It validates public API base URL safety and blocks localhost/private/internal targets. It does not fuzz endpoints, bypass authentication, send exploit payloads, test credentials, brute force routes, or mutate backend state.

Deep API/dApp testing must require verified ownership, written scope, rate limits, and a separate manual review process.


## Phase 5.7 Wallet/Admin Safety

Wallet Flow and Admin OpSec scanners are static/checklist-only readiness modules. They do not connect to wallets, request signatures, collect private keys, collect seed phrases, query user balances, or execute transactions. Admin notes are used only to generate preliminary launch-readiness findings. Any critical wallet/key-management issue should be manually reviewed before launch.

---

## Phase 5.9 Ownership Verification Boundary

Phase 5.9 adds domain-control verification for future owner-approved scans. Verification can be done with:

1. DNS TXT: `_web3guard.<domain>` with the generated token.
2. Well-known file: `/.well-known/web3guard-verify.txt` containing the generated token.

Verification is not a security certificate. It only proves that the requester can control a domain or place a token.

Even after verification, MVP behavior remains passive/checklist/code-submitted only. Future deep scan must require:

- verified ownership
- written scope
- clear testing window
- rate limit
- non-destructive rules
- no credential testing unless explicitly contracted and legally scoped

Additional Phase 5.9 safety controls:

- private/internal host blocking remains active
- redirects to unsafe/internal targets are blocked
- scanner endpoints require authorization confirmation
- rate limits cover all scanner modules, not only website scans
