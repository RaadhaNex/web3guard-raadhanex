# Phase 13 — Real Static Analysis Engine

## What is live

Phase 13 adds a real optional static-analysis runner for:

- Slither
- Aderyn
- Semgrep

The app does **not** fake findings. A tool contributes findings only when all conditions are true:

1. `STATIC_ANALYSIS_ENABLED=true`
2. Tool-specific env flag is enabled
3. Tool binary is installed or configured
4. The tool completes and emits parseable output

If a tool is missing/disabled, the scan returns an informational tool-status finding such as `Slither Not Run`.

## What it does not do

- No certified audit claim
- No fake Slither/Aderyn/Semgrep output
- No repo clone in this phase
- No dependency install
- No npm/pip install inside scans
- No contract execution
- No exploit automation
- No private key / seed phrase collection

## Backend endpoints

```text
GET  /scan/static-analysis/status
POST /scan/static-analysis
```

## Required backend env

Default is safe and disabled:

```env
STATIC_ANALYSIS_ENABLED=false
SLITHER_ENABLED=true
ADERYN_ENABLED=false
SEMGREP_ENABLED=true
SLITHER_BINARY=
ADERYN_BINARY=
SEMGREP_BINARY=
AUDIT_TOOL_TIMEOUT_SECONDS=45
```

To enable locally after installing tools:

```env
STATIC_ANALYSIS_ENABLED=true
SLITHER_ENABLED=true
SEMGREP_ENABLED=true
ADERYN_ENABLED=true
```

## Tool installation notes

Install tools manually on the machine/container running the backend. Do not place API keys, private keys, mnemonic phrases, or production secrets in scanner inputs.

Recommended production direction:

- Run these tools in a Docker/worker container
- Use a non-root user
- Use strict CPU/memory/time limits
- Delete temporary workspaces after each scan
- Keep network access blocked unless a specific verified dependency fetch mode is intentionally enabled

## Local test flow

1. Start backend.
2. Open `/scan/static-analysis/status`.
3. Confirm which tools are installed and will run.
4. Open frontend `/scanner/static-analysis`.
5. Paste Solidity and run scan.

If tools are disabled/missing, the scanner still responds honestly with status-only informational findings.
