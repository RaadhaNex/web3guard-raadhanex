# External Setup Guide — Non-Payment Public Beta

This guide lists optional integrations. Do not fake a provider/tool status. If anything is missing, the UI/API must continue showing honest status.

## Vercel frontend
Required public variables:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-render-backend.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

Payment variables should remain disabled during this patch:

```bash
NEXT_PUBLIC_RAZORPAY_ENABLED=false
```

## Render backend
Core variables depend on the existing project setup. Keep secrets server-side only.

Recommended review:

```bash
FRONTEND_ORIGIN=https://your-vercel-domain.vercel.app
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=server-only-key
AI_ENABLED=false
PAYMENTS_ENABLED=false
```

## Etherscan / explorer readiness
Use only backend env:

```bash
ETHERSCAN_API_KEY=your-key
```

Rules:
- Do not claim verified-source analysis unless source fetch succeeds.
- If source is unavailable, show Needs API Key / Not Assessed / Manual.

## GitHub scanner/status
Optional token for better rate limits:

```bash
GITHUB_API_TOKEN=github-token-with-minimum-needed-scope
```

Rules:
- Public repo scanning can be read-only.
- Do not scan private repos without explicit authorization.
- Do not install or execute repository code on the web server.

## Slither / Aderyn / Semgrep
Only enable if real binaries exist in a controlled environment:

```bash
STATIC_ANALYSIS_ENABLED=true
SLITHER_ENABLED=true
ADERYN_ENABLED=true
SEMGREP_ENABLED=true
```

Rules:
- Missing binary = Tool Not Installed.
- Timeout/error = Not Assessed with error evidence.
- Never fabricate tool findings.

## Mythril / Manticore / Echidna
Use an isolated worker, Docker job, or separate locked-down host.

Rules:
- Keep OFF on the main web server unless resource isolation is complete.
- No exploit automation.
- No untrusted dependency installation by default.
- No network access unless explicitly required and safe.

## AI provider
Keep OFF until privacy and cost controls are ready:

```bash
AI_ENABLED=false
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

Rules:
- No fake AI summaries.
- Never send private keys, seed phrases, mnemonics, or secrets to any provider.
- Clearly label AI provider as Provider Not Configured until enabled.

## GoPlus/token/wallet risk
Enable only after terms/privacy review:

```bash
GOPLUS_ENABLED=false
GOPLUS_API_KEY=
```

Rules:
- Read-only risk checks only.
- No wallet signing.
- No seed/private-key collection.

## Payment deferred
Razorpay/UPI remains final phase work. Before enabling payment, complete:

- Order creation
- Checkout
- Webhook signature verification
- Subscription/payment state in database
- Audit logs
- Failure/refund/manual-review states
- Server-side entitlement checks
