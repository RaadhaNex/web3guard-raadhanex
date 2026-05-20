# Phase 40 + 41 — Verified Authorized Web DAST + Admin Pentest Governance

## What this patch adds

This patch adds a safe, professional web-testing workflow without enabling abusive hacking automation.

### Phase 40 — Verified Authorized Web DAST Scanner

Added `/web-dast` and backend APIs:

- `GET /web-dast/status`
- `POST /web-dast/safe-url-check`
- `POST /web-dast/verify/start`
- `POST /web-dast/verify/check`
- `POST /web-dast/passive-baseline`
- `POST /web-dast/light-active`
- `POST /web-dast/claim-check`

The user-side flow is:

1. Enter target URL.
2. Lock exact allowed domains.
3. Confirm ownership or written permission.
4. Start ownership verification.
5. Verify DNS/HTML/meta/domain-email proof token.
6. Run passive baseline or light non-destructive checks.
7. Show evidence-first results.

### Phase 41 — Admin Pentest Governance Console

Added `/admin-pentest` and backend APIs:

- `GET /admin-pentest/status`
- `GET /admin-pentest/blocked-tests`
- `POST /admin-pentest/requests`
- `POST /admin-pentest/approve-scope`
- `POST /admin-pentest/import-report`
- `POST /admin-pentest/claim-check`

The admin-side flow is:

1. Review permission document.
2. Lock exact scope and scan window.
3. Approve safe non-destructive scope.
4. Import external/manual pentest evidence.
5. Triage findings and prepare auditor handoff.

## What is intentionally blocked

Web3Guard does not automate:

- brute force
- password spraying
- credential stuffing
- DoS/stress testing
- exploit chaining
- RCE exploitation
- file deletion/write attempts
- data extraction
- admin bypass automation
- real payment abuse testing
- private key/seed/mnemonic collection
- wallet signing
- unauthorized third-party scanning

These remain blocked even for admins. Admins can govern scope and import manual evidence, not run destructive automation.

## Safe wording

Use:

> Authorized passive and controlled non-destructive web security checks for verified owned or permitted scopes. Not a certified audit. No security guarantee.

Avoid:

- active hacking scan
- hack any website
- exploit scan
- 100% secure
- certified audit
- audited by Web3Guard

## Deployment notes

No new secrets are required. Existing Render/Vercel deployment works after applying the patch and redeploying.

If live passive HTTP checks are enabled, the backend performs a small, non-destructive GET request with a Web3Guard user agent and timeout.
