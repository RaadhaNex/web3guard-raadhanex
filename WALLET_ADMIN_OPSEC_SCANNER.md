# Phase 5.7 — Wallet Flow + Admin OpSec Scanner

This phase upgrades Wallet Flow and Founder/Admin OpSec from simple checklist modules into real preliminary launch-readiness scanners.

## What the wallet scanner checks

The wallet scanner combines checklist answers with optional owner-provided notes. It does **not** connect to wallets, request signatures, simulate transactions, or collect private keys.

Coverage:
- WalletConnect/domain verification readiness
- chain ID / network mismatch handling
- spender/operator address display
- token/amount/recipient/contract preview
- unlimited approval warnings
- `setApprovalForAll` / NFT operator approval warnings
- Permit / Permit2 explanation
- blind signing / raw signature review
- typed-data / human-readable signature preference
- session disconnect guidance
- verified contract/explorer link display
- wallet prompts only after explicit user action
- mint/claim flow clarity

## What the Admin OpSec scanner checks

Coverage:
- multisig for critical owner/admin actions
- timelock for critical changes
- role separation: owner, pauser, minter, upgrader, deployer, treasury
- emergency pause / recovery process
- proxy/upgrade admin controls
- treasury wallet separation
- hardware wallet / custody policy
- private key and seed phrase storage policy
- MFA for GitHub, hosting, registrar, email, dashboards, payment tools
- admin/payment/security audit logs
- signer rotation and offboarding
- incident response plan
- safe backup admin recovery

## Notes hint engine

The scanner detects high-risk phrases in owner-provided notes, for example:

- `MaxUint256`, `unlimited approval`, `setApprovalForAll`
- `Permit2`, `permit signature`, `personal_sign`, `eth_sign`, `blind signing`
- `auto-connect`, `prompt on load`, `chain mismatch`
- `single owner`, `EOA owner`, `no multisig`, `no timelock`
- `private key in .env`, `seed phrase shared in Telegram`, `hot wallet deployer`
- `treasury same wallet`, `MFA missing`, `no incident response`
- `upgradeable proxy`, `proxy admin`

## Safety boundaries

- No exploit automation.
- No wallet connection.
- No transaction signing.
- No private-key or seed phrase collection.
- No scraping of wallet balances.
- No claim of certified audit.
- Results are preliminary and should be manually reviewed before launch.

## API endpoints

```text
GET  /scan/checklist/wallet
GET  /scan/checklist/admin_opsec
POST /scan/wallet-checklist
POST /scan/admin-opsec
```

## Example wallet request

```json
{
  "project_name": "Demo Mint",
  "authorization_confirmed": true,
  "checklist": [
    {"key":"allowance_warning","label":"Allowance warning","answer":"no"},
    {"key":"spender_display","label":"Spender display","answer":"unknown"}
  ],
  "notes": "Mint page asks for MaxUint256 unlimited approval and Permit2 may be used later."
}
```

## Example admin request

```json
{
  "project_name": "Demo Token",
  "authorization_confirmed": true,
  "checklist": [
    {"key":"multisig","label":"Multisig","answer":"no"},
    {"key":"timelock","label":"Timelock","answer":"unknown"}
  ],
  "notes": "Owner is a single EOA owner. Private key was stored in .env during testing. No multisig yet."
}
```
