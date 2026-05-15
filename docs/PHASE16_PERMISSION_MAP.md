# Phase 16 — Contract Permission Map + Centralization Risk Report

Phase 16 adds a real-only permission intelligence layer for Web3Guard AI by RAADHANEX.

## What is live

- `/scanner/permission-map` frontend page
- `GET /scan/permission-map/status`
- `POST /scan/permission-map`
- Solidity source capability detection
- ABI function capability detection
- Manual owner/treasury/multisig/timelock facts
- Centralization score
- Founder transparency checklist
- Dashboard save support

## Capabilities detected

- Owner / primary admin
- Role administrator
- Minter / supply controller
- Pauser / emergency controller
- Upgrader / proxy controller
- Treasury / withdrawal controller
- Blacklist / freeze controller
- Fee / tax controller
- Oracle / price-feed controller

## Real-only boundaries

This phase does **not**:

- collect private keys
- collect seed phrases
- connect to wallets
- sign transactions
- mutate contracts
- prove live role holders without explorer/on-chain data
- certify governance safety
- replace manual audit/legal disclosure review

Unknown controllers remain unknown until source/ABI/manual/on-chain evidence is provided.

## Example API payload

```json
{
  "project_name": "Token Launch",
  "solidity_code": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20; contract T { ... }",
  "abi_json": "[{\"type\":\"function\",\"name\":\"mint\"}]",
  "contract_address": "0x0000000000000000000000000000000000000000",
  "chain": "ethereum",
  "owner_address": "0x1111111111111111111111111111111111111111",
  "treasury_address": "0x2222222222222222222222222222222222222222",
  "multisig_enabled": false,
  "timelock_enabled": false,
  "governance_notes": "Owner will be moved to multisig before launch.",
  "authorization_confirmed": true,
  "real_only_acknowledged": true
}
```

## Output sections

- `module_score`
- `findings`
- `scan_metadata.permission_map.capabilities`
- `scan_metadata.centralization_report`
- `scan_metadata.founder_transparency_report`
- `scan_metadata.coverage`

## Manual work needed from founder

Before public launch, the founder must manually provide or verify:

- live owner/admin address
- multisig address and signer policy
- timelock address/configuration
- treasury wallet
- proxy admin / implementation address if upgradeable
- role holders for minter/pauser/upgrader/admin roles
- public disclosure wording for mint/freeze/fee/upgrade powers

## Next phase link

Phase 17 should extend this into token/NFT/project-type transparency modules.
