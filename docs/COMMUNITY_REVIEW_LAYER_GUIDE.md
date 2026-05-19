# Web3Guard Phase 23 — Community Review Layer

## Purpose
Community Review adds a safe manual-review workflow on top of Web3Guard's scanner, Sentinel, EON, trust readiness, and Security Copilot layers.

It is designed for:
- scoped review requests from project owners
- moderation-first community feedback
- manual triage states
- responsible review templates
- admin oversight

## What it is not
Community Review is **not**:
- a certified audit
- a bounty marketplace
- a verified auditor network
- a guarantee that a project is safe
- exploit automation
- permission to test live systems without written authorization

## Core safety boundaries
Reviewers and founders must not share or request:
- private keys
- seed phrases
- mnemonics
- wallet signatures
- production secrets
- sensitive customer data

## Public wording
Safe wording:
- "Community review requested"
- "Pre-audit readiness feedback queued"
- "Manual triage in progress"
- "Feedback requires validation"

Blocked wording:
- "audited by Web3Guard"
- "certified secure"
- "verified auditor badge"
- "bounty marketplace guarantee"
- "100% secure"

## Backend endpoints
- `GET /community-review/status`
- `POST /community-review/requests`
- `GET /community-review/requests`
- `POST /community-review/feedback`
- `GET /community-review/feedback`
- `POST /community-review/triage`
- `GET /community-review/triage`
- `GET /community-review/project-board`
- `GET /community-review/admin/overview`
- `POST /community-review/templates/responsible-review`

## Frontend pages
- `/community-review`
- `/community-review/admin`
- `/community-review/project/[id]`

## Storage model
The Phase 23 implementation is local-first JSONL compatible and append-only for triage events. This avoids rewriting historical triage state in local mode.

Future Supabase migration can map these records into:
- community_review_requests
- community_review_feedback
- community_review_triage

## Recommended launch posture
Keep the feature behind safe language until a real reviewer process exists. The page can be public, but any reviewer credential or badge should remain disabled unless verified manually.
