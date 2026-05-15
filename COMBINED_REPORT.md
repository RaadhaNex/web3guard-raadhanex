# Phase 5.8 — Combined Launch Readiness Report

Web3Guard AI by RAADHANEX now combines all scanner module outputs into one final pre-audit launch readiness report.

## What this report does

- Combines Smart Contract, Website, dApp, API, Wallet Flow, and Founder/Admin OpSec scores.
- Uses the weighted launch readiness model:
  - Smart Contract: 35%
  - Website Surface: 15%
  - dApp Frontend: 15%
  - API Backend: 15%
  - Wallet Flow: 10%
  - Founder/Admin OpSec: 10%
- Produces either:
  - `overall_score` when all six modules are assessed
  - `available_score` when only some modules are assessed
- Shows coverage confidence so partial reports are not oversold.
- Generates a stable report hash for delivery tracking.
- Creates Markdown and JSON exports.
- Adds client-safe public wording.

## Report sections

1. Report ID and verification hash
2. Executive summary
3. Risk narrative
4. Weighted module matrix
5. Severity breakdown
6. Priority action plan
7. Before-launch checklist
8. Recommended paid package
9. Client delivery and public sharing note
10. Limitations
11. Disclaimer

## Important wording

Allowed wording:

> Pre-audit readiness reviewed by Web3Guard AI by RAADHANEX

Do not use:

- Certified audit
- 100% secure
- Insurance guaranteed
- Exploit-proof

## API

```http
POST /report/combined
```

Body:

```json
{
  "project_name": "My Token Launch",
  "reports": ["scan response objects"],
  "preferred_language": "Hinglish",
  "include_ai": true,
  "report_mode": "pre_audit"
}
```

The response includes `markdown_report` and `json_export`.

## Frontend

Run any scanner module and click **Generate Final Report**. The frontend report preview supports:

- Copy markdown
- Download Markdown
- Download JSON
- Print / Save PDF

## Safety note

This is still a preliminary launch readiness report. It does not replace a professional manual audit.
