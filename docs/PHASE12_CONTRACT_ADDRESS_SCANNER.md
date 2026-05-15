# Phase 12 — Contract Address Scanner

## What is live

Phase 12 adds a real verified-source contract address scanner for EVM chains.

Live flow:

1. User enters an EVM contract address and chain.
2. Backend validates the address and chain.
3. Backend calls the Etherscan API V2-compatible `contract/getsourcecode` endpoint using backend-only `ETHERSCAN_API_KEY`.
4. If verified source is returned, backend extracts Solidity source.
5. Backend runs the local Web3Guard AI Solidity rule engine on the fetched source.
6. Backend adds explorer metadata findings, including proxy/upgradeability hints, ABI admin-like functions, compiler metadata, optimizer metadata, and transparency notes.
7. Frontend shows score, metadata, source/ABI summary, and findings.

## What is not faked

- No private key collection.
- No wallet connection.
- No transaction signing.
- No bytecode decompilation.
- No Slither/Aderyn/Mythril output unless those tools are actually integrated later.
- No code score if verified source cannot be fetched.
- No certified audit wording.

## Required backend env

```env
ETHERSCAN_API_KEY=your_real_etherscan_api_key
ETHERSCAN_V2_API_BASE=https://api.etherscan.io/v2/api
EXPLORER_SCAN_TIMEOUT_SECONDS=15
MAX_CONTRACT_ADDRESS_SCAN_PER_HOUR=25
MAX_EXPLORER_SOURCE_CHARS=350000
```

Do not put the explorer API key in frontend env.

## Supported chain keys

- `ethereum` / chain `1`
- `sepolia` / chain `11155111`
- `bsc` / chain `56`
- `polygon` / chain `137`
- `arbitrum` / chain `42161`
- `optimism` / chain `10`
- `base` / chain `8453`
- `avalanche` / chain `43114`

Numeric chain IDs are also accepted.

## New endpoints

```txt
GET  /scan/contract-address/status
POST /scan/contract-address
```

POST body:

```json
{
  "address": "0x0000000000000000000000000000000000000000",
  "chain": "ethereum",
  "project_name": "Demo Project",
  "authorization_confirmed": true,
  "real_only_acknowledged": true
}
```

## Frontend page

```txt
/scanner/address
```

## Unified URL scanner integration

If the user supplies a contract address in `/scanner/unified-url`, Phase 12 attempts a verified explorer-source scan. If `ETHERSCAN_API_KEY` is missing or the source is not verified, the contract module is marked as input recorded/not source-scanned instead of fake-scored.

## Manual account needed

You need an Etherscan account/API key. Etherscan API V2 supports multichain access through a single API key with the `chainid` parameter.
