# Web3Guard Phase 27 — Real Worker Execution Guide

Phase 27 adds a worker execution readiness layer for real security tools.

## Purpose

This layer prepares Web3Guard for real worker-based execution while preserving the real-only rule:

- Use real installed binaries only.
- Return real stdout/stderr/return code/timing metadata only.
- Never invent vulnerabilities when a tool is missing.
- Never claim certified audit status.

## Covered tools

| Tool | Phase 27 status scope | Default behavior |
| --- | --- | --- |
| Slither | Static worker readiness | Status-only until static analysis is enabled and binary exists |
| Aderyn | Static worker readiness | Status-only until enabled and binary exists |
| Semgrep | Real rules worker | Status-only until enabled and binary exists |
| Foundry | Test runner readiness | Status-only until worker execution + Foundry flags are enabled |
| Echidna | Fuzz/property worker readiness | Status-only until deep analysis + Echidna flags are enabled |
| Mythril | Docker/worker readiness | Docker/worker-gated by default |

## Endpoints

### `GET /worker-execution/status`

Returns tool readiness matrix and safety boundaries.

### `POST /worker-execution/plan`

Builds an execution plan for selected tools. This endpoint does not execute source code.

Example payload:

```json
{
  "project_type": "Founder-owned Solidity workspace",
  "tools": ["slither", "semgrep", "foundry"],
  "real_only_acknowledged": true
}
```

### `POST /worker-execution/probe`

Runs version probes only for ready tools. Missing or disabled tools return status-only evidence.

Example payload:

```json
{
  "tools": ["slither", "aderyn", "semgrep", "foundry", "echidna", "mythril"],
  "real_only_acknowledged": true
}
```

## Production recommendation

Do not run long scanner jobs in:

- Vercel frontend runtime
- a request-response route with no queue
- any runtime that contains secrets unrelated to the job

Recommended architecture:

1. FastAPI receives request and validates authorization + real-only acknowledgement.
2. API creates a worker job with size limits and input hash.
3. Isolated worker runs one tool with a strict timeout.
4. Worker stores raw evidence, return code, parser version, and timestamps.
5. Parser creates findings only from real tool output.
6. Missing tools stay `Tool Not Installed / Provider Not Configured / Manual / Not Assessed`.

## Blocked actions

- No private key / seed phrase / mnemonic collection.
- No wallet signing.
- No exploit automation.
- No automatic dependency install by default.
- No repo clone by default.
- No unauthorized active scanning.
- No fake results, fake score, fake monitoring, or fake trust badge.
