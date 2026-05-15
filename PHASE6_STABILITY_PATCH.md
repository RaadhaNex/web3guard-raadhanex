# Phase 6 — Full Local QA + Stability Patch

## What changed

- Added `/health/readiness` backend readiness endpoint.
- Added `/qa/status`, `/qa/runbook`, `/qa/frontend-routes`, `/qa/backend-endpoints`.
- Added frontend `/local-qa` console.
- Added backend smoke script: `scripts/backend_smoke.py`.
- Added Windows/Linux local QA helper scripts.
- Updated env examples with `BACKEND_URL` and `NEXT_PUBLIC_API_BASE_URL`.
- Updated README and test checklist.

## What this phase does not do

- Does not add Razorpay auto verification.
- Does not add Supabase auth/database.
- Does not add Slither/Mythril/Aderyn.
- Does not claim certified audit.
- Does not add fake monitoring or fake AI.

## QA status

Backend tests and compile checks should pass locally. Frontend package install/build must be run on your laptop because dependencies are installed through npm.
