# Security Copilot Workspace Guide

Phase 22 adds a defensive Security Copilot workspace for Web3Guard AI by RAADHANEX.

## What it does

The workspace combines existing stored evidence from EON, Sentinel, Launch Trust Readiness, India Launch Pack, and report/evidence data into a founder-friendly guidance console:

- next-step assistant
- fix task explanation
- safe local command snippets
- report wording assistant
- evidence digest
- local fallback guidance when AI provider is not configured

## What it does not do

Security Copilot is **not** an AI auditor and must not be marketed as one.

It does not:

- claim certified audit
- claim 100% security
- auto-apply fixes
- run exploit automation
- sign wallets
- collect private keys, seed phrases, or mnemonics
- invent AI/provider output when provider is missing

## Provider behavior

If AI provider is OFF or missing API keys, the workspace shows:

- `Provider Not Configured / Needs API Key`
- deterministic local checklist guidance
- safe commands only

If an AI provider is configured later, the same safety boundaries must remain visible.

## Safe command policy

Generated commands are local defensive verification helpers only. They should be run only inside the user's own authorized repository, local fork, testnet, or explicitly authorized environment.

## Public wording

Allowed:

- Security Copilot guidance
- Defensive fix-plan assistant
- Pre-audit readiness coach
- Local checklist fallback

Blocked:

- AI auditor
- certified by AI
- guaranteed secure
- exploit-free
- 100% secure
- autonomous audit completed
