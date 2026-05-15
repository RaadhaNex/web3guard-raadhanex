# Mega Phase A — Phase 17 + 18 + 19

Project: **Web3Guard AI by RAADHANEX**

This consolidated phase implements three real MVP modules without fake/dummy output:

1. **Phase 17 — Token/NFT/Launch Transparency Scanner**
2. **Phase 18 — Contract Diff + Audit History Scanner**
3. **Phase 19 — Upgrade Safety Analyzer**

## Real-only rules preserved

- No certified audit wording.
- No rug-pull accusation.
- No fake liquidity lock, multisig, timelock, metadata freeze, or role-holder evidence.
- No auto-fix.
- No wallet connection, private key, seed phrase, signing, or transaction execution.
- Missing proof stays missing.
- Final upgrade safety still requires compiler storage layout + manual review.

## New frontend pages

- `/scanner/launch-transparency`
- `/scanner/contract-diff`
- `/scanner/upgrade-safety`

## New backend endpoints

- `GET /scan/launch-transparency/status`
- `POST /scan/launch-transparency`
- `GET /scan/contract-diff/status`
- `POST /scan/contract-diff`
- `GET /scan/upgrade-safety/status`
- `POST /scan/upgrade-safety`

## Phase 17 — Launch Transparency

Inputs:

- Project name
- Project type: ERC20, NFT, staking, DAO, presale, airdrop/claim, marketplace
- Solidity source optional
- Website/landing copy optional
- Tokenomics notes optional
- Liquidity lock evidence optional
- Metadata freeze evidence optional
- Owner/admin power notes optional
- Multisig/timelock evidence fields

Detects:

- Mint/supply authority
- Pause/freeze/blacklist powers
- Fee/tax change powers
- Treasury/withdraw controls
- Upgradeability disclosure need
- NFT metadata mutability
- Allowlist/claim mechanics
- Privileged controls without multisig/timelock evidence

Output:

- Launch transparency score
- Findings
- Project-type checklist
- Detected controls
- Required disclosure summary

## Phase 18 — Contract Diff

Inputs:

- Old Solidity source
- New Solidity source

Detects:

- Added risky lines
- New mint/supply control
- New upgrade-control surface
- New fee/tax control
- New pause/freeze/blacklist control
- New external-call surface
- Old vs new rule-engine score delta
- Fixed/open/new finding keys from real rule-engine scans

Output:

- Diff score
- Old score, new score, delta
- Unified diff preview
- Added/removed line count
- Findings for newly introduced risky patterns

## Phase 19 — Upgrade Safety

Inputs:

- Current Solidity source
- Previous Solidity source optional
- Proxy/admin notes optional
- Ownership verified checkbox

Detects:

- UUPS proxy hints
- Transparent proxy hints
- Beacon proxy hints
- Minimal proxy hints
- Missing initialize function for proxy-style code
- initialize() without initializer guard evidence
- Missing `_disableInitializers()` evidence
- Missing upgrade authorization evidence
- Proxy admin hot wallet/single EOA risk notes
- Old/new storage variable order changes

Output:

- Upgrade safety score
- Proxy pattern list
- Initializer evidence summary
- Storage layout hint
- Findings and next steps

## Manual work required from user

No new external accounts are required for this phase.

For better results, user should manually provide:

- Actual old and new source code for diff
- Actual current/previous upgradeable source
- Actual proxy admin/governance notes
- Real multisig/timelock/liquidity/metadata evidence

## Validation results

Backend:

```bash
PYTHONPATH=. pytest -q
# 92 passed

python -m compileall -q .
# passed

python ../scripts/backend_smoke.py
# passed
```

Frontend:

```bash
npm install --package-lock=false --no-audit --no-fund
npm run typecheck
# passed
npm run build
# compiled successfully, then sandbox timed out during final Next.js page-data collection
```

Run locally to fully confirm production build.
