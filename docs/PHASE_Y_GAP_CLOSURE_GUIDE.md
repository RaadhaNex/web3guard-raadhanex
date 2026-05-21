# Phase Y — Result Report Polish + Gap Closure Guide

## What this phase improves

This phase makes the unified scanner easier for non-technical founders and first-time users:

- Simple form mode stays beginner-first.
- Developer/Expert evidence stays available but hidden until selected.
- Result output now includes a founder-friendly report view.
- Findings are translated into plain language tasks.
- Static-analysis tool gaps are shown honestly.
- Human-review gap is shown as a real handoff path, not as a fake marketplace/team claim.

## Static-analysis gap: Slither / Semgrep / Aderyn

Current real-only rule:

- Web3Guard must not fake Slither, Semgrep, or Aderyn results.
- URL-only scans do not execute these tools.
- GitHub read-only scans do not clone, install dependencies, or run local binaries.
- Live tool execution must happen only inside a separate isolated worker service.

Safe ways to cover this gap:

1. Paste real Slither JSON in Expert Evidence.
2. Paste real Semgrep JSON in Expert Evidence.
3. Paste real Aderyn JSON in Expert Evidence.
4. Provide Solidity source or verified contract/source evidence.
5. Build a separate isolated worker service for Foundry/Echidna/static tools.
6. Keep worker execution disabled in the main backend.

Do not enable these in the main backend unless the isolated worker safety plan is completed.

## Human-review gap

Current real-only rule:

- Web3Guard can prepare reviewer handoff reports.
- Web3Guard can route users to manual-review workflow.
- Web3Guard must not claim a verified reviewer marketplace/team unless real reviewers are onboarded, verified, assigned, and logged.

Safe ways to cover this gap:

1. Use the manual-review route to triage findings.
2. Assign real reviewer/admin accounts.
3. Require reviewer notes for confirmed, false-positive, accepted-risk, or out-of-scope decisions.
4. Keep public report wording limited to “reviewed” only after real reviewer action.
5. Never use “certified audit”, “verified auditor”, or “100% secure” wording from scanner-only output.

## Files changed

- frontend/components/scanner/UnifiedUrlScannerClient.tsx

## Validation

Run:

```powershell
cd C:\web\web3guard\frontend
npm install
npm run typecheck
npm run build
```
