# Phase 14 — Deep Analysis Layer / Isolated Audit Worker Architecture

Phase 14 adds a real-only deep-analysis layer for **Mythril**, **Manticore**, and **Echidna**.

## Real-only rule

The platform does **not** fake symbolic execution, fuzzing, or deep-analysis findings.

A finding is treated as deep-analysis evidence only when:

1. `DEEP_ANALYSIS_ENABLED=true`
2. the specific tool flag is enabled
3. the tool binary is installed or configured
4. the tool actually runs
5. output is parsed from that real run

Missing tools generate informational `Not Run` findings only.

## New API endpoints

- `GET /scan/deep-analysis/status`
- `POST /scan/deep-analysis`

## Frontend

- `/scanner/deep-analysis`

## Tools

- Mythril: symbolic security analysis
- Manticore: symbolic execution architecture
- Echidna: property/fuzz testing architecture

## Safe defaults

```env
DEEP_ANALYSIS_ENABLED=false
MYTHRIL_ENABLED=false
MANTICORE_ENABLED=false
ECHIDNA_ENABLED=false
DEEP_ANALYSIS_NETWORK_ENABLED=false
DEEP_ANALYSIS_ALLOW_DEPENDENCY_INSTALL=false
```

## Recommended production architecture

For production, do not run deep tools inside the public API process.
Use a separate locked worker:

- Docker container per job
- no secrets mounted
- no private key access
- no mainnet transaction signing
- non-root user
- read-only filesystem where possible
- CPU/memory/time limits
- network disabled by default
- strict upload/file size limits
- job queue and status tracking
- cleanup workspace after job

## Depth policy

- `quick`: can run enabled tools with strict timeout
- `standard`: requires ownership verification
- `deep`: requires ownership verification and should use a dedicated worker

## What Phase 14 does not do

- Does not clone repositories
- Does not install dependencies
- Does not run deployment scripts
- Does not collect private keys or seed phrases
- Does not sign transactions
- Does not touch mainnet
- Does not replace a manual audit
