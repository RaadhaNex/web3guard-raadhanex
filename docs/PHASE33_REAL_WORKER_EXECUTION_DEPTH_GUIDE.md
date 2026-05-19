# Phase 33 — Real Worker Execution Depth Guide

Phase 33 makes the worker layer more usable without pretending that missing tools have produced evidence.

## New endpoints

### `GET /worker-runs/status`

Returns the worker matrix, execution modes, and safety boundaries.

### `POST /worker-runs/manifest`

Creates a safe job manifest for Slither, Semgrep, Aderyn, Foundry, Echidna, and Mythril. This endpoint does not run tools.

### `POST /worker-runs/static`

Runs or plans static worker execution for Solidity input.

- `execute=false`: returns a manifest/plan only.
- `execute=true`: runs only configured and installed Slither/Aderyn/Semgrep tools.

Real findings are produced only from real tool output. Missing tools stay status-only.

### `POST /worker-runs/import-json`

Normalizes imported JSON from:

- Slither
- Semgrep
- Aderyn
- Mythril
- Echidna
- Foundry

Imported JSON is labeled `imported_worker_evidence` unless `generated_by_web3guard_worker=true` is explicitly sent by a trusted caller.

## Frontend

New page:

```text
/worker-runs
```

It includes:

- Worker readiness matrix
- Safe worker manifest
- Static worker execution/planning panel
- Imported deep worker JSON parser
- Findings list with evidence IDs and limitations

## Safety model

Phase 33 keeps the following hard boundaries:

- No private key / seed phrase / mnemonic input.
- No wallet signing.
- No exploit automation.
- No unauthorized active scanning.
- No fake scanner findings.
- No certified-audit wording.
- No 100% secure claim.

## Static worker execution

`/worker-runs/static` connects to the existing static-analysis engine. It will run tools only when:

- `execute=true`
- `STATIC_ANALYSIS_ENABLED=true`
- selected tool is enabled
- selected binary is installed or configured

If not, output remains status-only.

## Deep worker handling

Foundry, Echidna, and Mythril are not falsely executed by this patch. Their JSON can be imported and normalized if produced by an external safe worker. Mythril remains Docker/isolated-worker-first by default.

## Recommended next step

After Phase 33, the highest-impact next step is Phase 34:

- Render/Docker worker setup script
- Slither/Semgrep installation guide
- Mythril Docker image path
- Worker health check endpoint connected to deployment docs
- First real pilot scan workflow
