# Public Beta Launch Checklist — Web3Guard AI by RAADHANEX

## Product truth and claims
- [ ] Site never claims certified audit, 100% secure, exploit-proof, or AI-audited unless backed by a real certified/manual audit.
- [ ] Every missing provider/tool shows honest status: Tool Not Installed, Provider Not Configured, Needs API Key, Manual, or Not Assessed.
- [ ] Payment pages do not unlock premium features until Razorpay/UPI verification and webhook audit trail are complete.
- [ ] Reports clearly separate readiness scoring from full audit scoring.

## Scanner readiness
- [ ] URL scanner works for Website / Landing Page, dApp Frontend, API Backend, Wallet Connect Flow, Admin Panel, and Smart Contract inputs.
- [ ] Required field validation is visible and readable.
- [ ] Reports include evidence, limitations, fix hints, Not Assessed modules, and split launch-confidence scores.
- [ ] PDF, HTML, Markdown, and JSON export buttons still work.

## Backend readiness
- [ ] `python -m pytest -q` passes before deployment.
- [ ] Render environment variables are reviewed without exposing secrets.
- [ ] CORS origin matches the production Vercel domain.
- [ ] `/health`, `/scan/feature-status`, and `/public-beta/readiness` return honest live status.

## Frontend readiness
- [ ] `npm ci`, `npm run typecheck`, and `npm run build` pass locally or on Vercel.
- [ ] Mobile layout is readable.
- [ ] Reduced-motion mode is respected.
- [ ] Trust pages are linked from header/footer.

## Supabase readiness
- [ ] Auth signup/login/logout/session verified.
- [ ] RLS policies reviewed.
- [ ] Heartbeat workflow uses safe secrets only.
- [ ] No service-role key is exposed to frontend.

## External readiness
- [ ] Etherscan API key added only on backend when ready.
- [ ] GitHub token added only for rate limits, not private repo scanning without authorization.
- [ ] Slither/Aderyn/Mythril/Echidna run only in a controlled worker.
- [ ] AI provider remains OFF until pricing, privacy, and code-sharing policy are ready.

## Launch comms
- [ ] Public beta announcement describes the product as launch-readiness/pre-audit support.
- [ ] Security contact and responsible disclosure guidance are visible.
- [ ] Sample reports are clearly marked as samples.
