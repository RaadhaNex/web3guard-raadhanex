# Phase 34 — Payment Validation + First Paid Flow Guide

Phase 34 converts Web3Guard's payment layer into a first-revenue validation workflow.

## Goal

Validate a real paid flow without misleading users:

```text
Free scan → pilot report preview → ₹999 Quick Risk Scan Report → backend verified payment → manual/paid deliverable
```

## New frontend route

- `/payment-validation`

This page shows:

- Razorpay detected mode: test/live/not configured
- backend key readiness without exposing secrets
- webhook readiness
- manual UPI fallback
- first paid flow steps
- checkout dry run for the ₹999 report
- payment/audit wording checker

## New backend endpoints

- `GET /payment-validation/status`
- `GET /payment-validation/first-paid-flow`
- `GET /payment-validation/revenue-readiness`
- `POST /payment-validation/checkout-dry-run`
- `POST /payment-validation/access-preview`
- `POST /payment-validation/claim-check`

## What this phase does not do

- It does not create fake payment records.
- It does not create Razorpay orders from dry-run endpoints.
- It does not unlock paid features on frontend callback alone.
- It does not claim certified audit, 100% secure, or Web3Guard-audited status.
- It does not expose `RAZORPAY_KEY_SECRET` or `RAZORPAY_WEBHOOK_SECRET` to frontend.

## Real payment source of truth

A payment can become verified only by existing real endpoints:

- backend checkout signature verification
- signed Razorpay webhook verification
- manual admin approval for UPI/manual fallback

## Recommended first paid offer

Use the package already present in `backend/app/data/packages.json`:

- Package: `quick-risk-report`
- Price: `₹999`
- Positioning: preliminary quick risk scan report
- Wording: not a certified audit

## Safe outreach wording

```text
₹999 Quick Risk Scan Report for first 10 Indian Web3 founders. Preliminary readiness only; not a certified audit.
```

## Blocked wording

Do not use:

- `100% secure`
- `certified audit`
- `audited by Web3Guard`
- `payment successful` without backend verification
- `subscription active` without verified payment or manual approval
- fake invoices, GST, refunds, or compliance states

## Why this matters

The next business goal is first real validation. A single verified ₹999 payment is more valuable than another disconnected dashboard because it proves the product flow, pricing, trust wording, and payment ops can work with real users.
