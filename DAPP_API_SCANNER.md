# Phase 5.6 — dApp Frontend + API Risk Scanner

Web3Guard AI by RAADHANEX now includes preliminary dApp frontend and API backend risk scanners.

## Positioning
These modules are launch-readiness checks, not certified audits or penetration tests.

They help founders answer:
- Is my dApp frontend exposing secrets or confusing wallet users?
- Is my API missing obvious launch security controls?
- What should I fix before manual review or public launch?

## dApp Frontend Scanner

### Inputs
- Checklist answers
- Optional frontend code snippet
- Optional `package.json`
- Optional reviewer notes

### Checks
- Public frontend secret naming such as `NEXT_PUBLIC_*SECRET*`, `NEXT_PUBLIC_*KEY*`, `NEXT_PUBLIC_*TOKEN*`
- Hardcoded RPC provider URLs
- Hardcoded EVM addresses
- Missing chain ID checks
- Missing transaction preview hints
- Unsafe rendering / XSS patterns: `dangerouslySetInnerHTML`, `innerHTML`, `eval`, `new Function`
- Wallet auto-connect hints
- Unlimited approval / `setApprovalForAll` hints
- Blind signing/signature clarity hints
- Older wallet dependency review hints
- Client-side seed/key management package hints

### Output
- dApp Frontend Score
- Severity findings
- Business impact
- Developer explanation
- Fix direction
- Priority actions
- Metadata showing static-hints-only safety controls

## API Backend Scanner

### Inputs
- Checklist answers
- Optional public API base URL
- Optional API/config code snippet
- Optional architecture notes

### Checks
- Public URL validation with private/internal target blocking
- Wildcard CORS patterns
- Debug mode patterns
- Hardcoded backend secrets
- Docs/OpenAPI/GraphQL exposure review
- Missing rate-limit hint
- Missing auth/authorization hint
- Missing webhook signature hint
- BOLA/IDOR review hint
- Error masking/input validation/audit log checklist gaps

### Safety boundaries
The API scanner does not:
- fuzz endpoints
- bypass auth
- test credentials
- run exploit payloads
- brute force routes
- mutate server state

Phase 5.6 keeps docs endpoint hints as manual owner review. Deep API scanning should only come later after ownership verification and explicit written scope.

## Recommended paid workflow
If dApp/API score is high risk:
1. Ask founder for repo snippets, architecture diagram, and API route list.
2. Run checklist + code/config hint scan.
3. Deliver priority fix list.
4. Upsell Fix Suggestion Pack or Manual Pre-Audit Review.

## Honest disclaimer
This module catches common launch readiness mistakes. It does not prove that a dApp frontend or backend API is secure.
