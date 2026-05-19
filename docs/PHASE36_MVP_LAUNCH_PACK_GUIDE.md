# Phase 36 — MVP Launch Pack + First 10 Users Sprint Guide

## Purpose

Phase 36 closes the current build roadmap. The product already has scanner, results, worker, provider, payment validation, and pilot UX layers. The next risk is not missing pages; the next risk is shipping without users. This phase creates the operating pack for first public beta validation.

## New route

Frontend:

```text
/launch-pack
```

Backend:

```text
/mvp-launch/status
/mvp-launch/launch-checklist
/mvp-launch/outreach-kit
/mvp-launch/sample-report
/mvp-launch/public-beta-checklist
/mvp-launch/claim-guidance
/mvp-launch/claim-check
/mvp-launch/first-10
```

## First 10 user tracker

The tracker stores local JSONL records in:

```text
backend/app/data/first_10_pilot_users.jsonl
```

Do not store secrets here. The API rejects obvious private keys, seed phrases, mnemonics, API keys, access tokens, and secret-like values.

This local JSONL tracker is for MVP validation only. Move it to Supabase after the workflow is proven.

## Safe public positioning

Say:

```text
Web3Guard AI is a pre-audit launch readiness scanner for Web3 founders.
```

Do not say:

```text
100% secure
certified audit
audited by Web3Guard
audit passed
guaranteed secure
payment successful without verification
discovered by Web3Guard
bug bounty marketplace
```

## First paid flow

Use the ₹999 Quick Risk Scan Report as a validation anchor only after Razorpay backend verification is configured and tested.

No payment success UI should be shown without backend verification.

## Public beta checklist

Before public beta:

- Apply Phase 31–36 patches in order.
- Run backend tests.
- Run frontend typecheck.
- Run frontend build locally or on Vercel.
- Verify `/health`, `/launch-validation/status`, `/scanner-results/status`, `/worker-runs/status`, `/payment-validation/status`, and `/mvp-launch/status`.
- Generate one pilot report from permitted scope.
- Verify missing providers/tools show truthful states.
- Verify the claim checker blocks unsafe marketing copy.

## After Phase 36

Stop adding features until real pilot feedback exists.

Priority:

1. Apply all patches.
2. Test locally.
3. Deploy to Vercel/Render.
4. Verify Supabase, Razorpay, worker, and provider states.
5. Contact 10 Indian Web3 founders/teams.
6. Save friction in the First 10 tracker.
7. Fix only issues that block real users.
