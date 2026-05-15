# Website Passive Surface Scanner — Phase 5.5

The Web3Guard AI website scanner is designed as a legally safe, passive launch-readiness check for project-owned websites, landing pages, and dApp frontends.

## Positioning
This is a preliminary website surface review. It does not replace a full penetration test, source-code review, or manual audit.

## What it checks
- HTTPS-first URL usage
- HTTP to HTTPS redirect
- redirect chain length
- unsafe redirect target blocking
- homepage availability and HTTP status
- HSTS
- Content-Security-Policy
- weak CSP hints
- X-Frame-Options
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy
- Cache-Control review hint
- robots.txt
- sitemap.xml
- limited sensitive path hints using HEAD only
- external script count
- inline script count
- mixed-content script hints
- wallet/mint/claim script review hints
- basic form count evidence

## Sensitive path hints
The scanner checks a very small fixed list with HEAD only:

- `/.env`
- `/admin`
- `/api`
- `/swagger`
- `/graphql`
- `/.git`
- `/backup`
- `/config`
- `/debug`

These are not deep scans. A returned 200/401/403 is a review hint, not proof of a vulnerability.

## Safety controls
- Passive GET/HEAD only
- No exploit payloads
- No brute-force wordlists
- No login bypass
- No credential testing
- No destructive requests
- Private/internal IP blocking
- Redirect-chain validation
- Response timeout
- Max response body size
- Hourly MVP rate limit
- Authorization checkbox required

## Production notes
For production deployment, move the in-memory rate limiter to Redis/Upstash so limits work across multiple Render instances.

## Future upgrade
- DNS TXT ownership verification
- `/.well-known/web3guard-verify.txt` verification
- dApp source/repo scanner
- CSP policy quality grader
- screenshot/report export
- verified-owner deep scan mode
