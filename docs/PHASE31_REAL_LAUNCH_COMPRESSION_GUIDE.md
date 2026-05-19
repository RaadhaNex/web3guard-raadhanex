# Phase 31 — Real Launch Compression + Revenue Validation Sprint

This phase stops the feature-sprawl loop and focuses Web3Guard AI on the shortest usable path to real validation.

## What changed

- Main navigation is compressed to seven visible paths:
  1. Scanner
  2. Results
  3. Fix Plan
  4. Report
  5. Pricing
  6. Dashboard
  7. Docs
- Advanced modules are preserved, but moved out of the visible navigation and into Docs / command palette search.
- Added `/launch-validation` as an internal sprint page for:
  - Slither Render readiness
  - Razorpay test-mode readiness
  - OSV + CISA KEV dependency intelligence starter
  - 30-day launch validation priorities
- Added backend endpoints under `/launch-validation`.
- Updated `render.yaml` build command to install `slither-analyzer` before backend requirements.

## Real-only rules preserved

- No fake Slither findings.
- No fake OSV/CISA vulnerabilities.
- No fake payment/subscription state.
- No private key, seed phrase, or mnemonic collection.
- No wallet signing.
- No exploit automation.
- No certified audit claim.
- Missing tools/providers remain visible as `Tool Not Installed`, `Needs API Key`, `Provider Not Configured`, `Manual review required`, or `Not assessed yet`.

## Render Slither activation

The patch updates `render.yaml`:

```bash
python -m pip install --upgrade pip setuptools wheel && pip install slither-analyzer && pip install -r requirements.txt
```

Recommended Render env:

```env
STATIC_ANALYSIS_ENABLED=true
SLITHER_ENABLED=true
AUDIT_TOOL_TIMEOUT_SECONDS=45
```

After deployment, verify:

```bash
curl https://YOUR_RENDER_BACKEND/launch-validation/slither-readiness
curl https://YOUR_RENDER_BACKEND/scan/static-analysis/status
```

## Razorpay test validation

Required backend-only env:

```env
RAZORPAY_ENABLED=true
PAYMENT_MODE=razorpay_or_upi_manual
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxx
RAZORPAY_WEBHOOK_SECRET=xxxxx
```

Then verify:

```bash
curl https://YOUR_RENDER_BACKEND/launch-validation/razorpay-readiness
```

Do not mark a user paid until backend signature/webhook verification succeeds.

## OSV + CISA KEV dependency intelligence

Default is safe/offline parsing only. To allow live lookups:

```env
LAUNCH_VALIDATION_NETWORK_ENABLED=true
PROVIDER_LIVE_NETWORK_ENABLED=true
```

Endpoint:

```bash
POST /launch-validation/dependency-intel
```

Input:

```json
{
  "package_json": "{\"dependencies\":{\"lodash\":\"4.17.20\"}}",
  "live_lookup": true,
  "real_only_acknowledged": true
}
```

If live network is disabled, the endpoint returns `Provider Not Configured` and no fake records.

## Next priority after this patch

1. Deploy backend to Render and verify Slither readiness.
2. Configure Razorpay test keys and verify one test payment lifecycle.
3. Enable OSV/CISA lookup after rate-limit/privacy review.
4. Start 10 founder outreach conversations and use feedback before adding new dashboards.
