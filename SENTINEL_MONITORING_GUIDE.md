# Web3Guard Sentinel Monitoring Guide

## Purpose
Web3Guard Sentinel adds monitoring and vulnerability intelligence without pretending to be a certified audit or real-time exploit platform.

Sentinel has three separate surfaces:

1. **User Project Monitoring**
   - Shows alerts only for the logged-in user's stored projects, scans, and reports.
   - Does not generate fake alerts when no records exist.

2. **Admin Intelligence Monitoring**
   - Shows source readiness, public advisory counts, project alert counts, and blocked wording.
   - Intended for platform operators and future Supabase role-based admin access.

3. **Public Intelligence**
   - Shows indexed/tracked public advisories and educational risk patterns.
   - Must not claim those advisories were discovered by Web3Guard.

## Safe wording
Use:
- public vulnerabilities indexed
- advisories tracked
- risk mappings generated
- project-specific findings generated from stored scans
- responsible disclosure drafts prepared

Do not use:
- vulnerabilities discovered by Web3Guard, unless original and verified
- certified audit
- 100% secure
- hacked / compromised unless independently confirmed

## Routes
Backend:
- `GET /sentinel/status`
- `GET /sentinel/sources`
- `GET /sentinel/intelligence`
- `POST /sentinel/intelligence/ingest`
- `GET /sentinel/project-alerts?user_id=...`
- `GET /sentinel/admin/overview`
- `POST /sentinel/disclosure/draft`

Frontend:
- `/sentinel`
- `/sentinel/intelligence`
- `/sentinel/admin`
- `/sentinel/disclosure`
- `/sentinel/project/[id]`

## Storage
Local JSONL fallback files are created only when the API is used:
- `backend/app/data/db/sentinel_vulnerability_index.jsonl`
- `backend/app/data/db/sentinel_matches.jsonl`
- `backend/app/data/db/sentinel_alerts.jsonl`
- `backend/app/data/db/sentinel_disclosures.jsonl`

Do not commit production data files.
