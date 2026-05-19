# Provider Live Integration Guide — Phase 28

Phase 28 adds a real-only provider integration hub. It is designed for provider truth, not marketing claims.

## New route

Frontend:

```text
/provider-live
```

Backend:

```text
GET  /provider-live/status
POST /provider-live/explorer/source
GET  /provider-live/goplus/status
POST /provider-live/github/repo-check
POST /provider-live/advisory/search
```

## Provider rules

- Missing Etherscan key returns `Needs API Key`.
- Disabled GoPlus returns `Provider Not Configured`.
- Disabled advisory sources return `Provider Not Configured` with zero records.
- Provider request failures return `Not Assessed` with a provider error summary.
- No fake advisory, repository, source-code, monitoring, score, or trust-badge data is generated.

## Explorer source fetch

`POST /provider-live/explorer/source`

```json
{
  "chain": "ethereum",
  "address": "0x0000000000000000000000000000000000000000",
  "include_abi": false,
  "real_only_acknowledged": true
}
```

Use this for verified-source evidence snapshots. For deeper contract findings, continue to use the existing `/scan/contract-address` scanner.

## GitHub metadata check

`POST /provider-live/github/repo-check`

```json
{
  "repo_url": "https://github.com/openzeppelin/openzeppelin-contracts",
  "branch": null,
  "authorization_confirmed": true,
  "real_only_acknowledged": true
}
```

This is read-only metadata. For deeper repository checks, use `/scan/github`.

## Advisory search

`POST /provider-live/advisory/search`

```json
{
  "source": "osv",
  "query": "CVE-2024-3094",
  "ecosystem": "npm",
  "package_name": null,
  "real_only_acknowledged": true
}
```

Supported source keys:

- `osv`
- `nvd`
- `github_advisory`
- `cisa_kev`

Keep `PROVIDER_LIVE_ADVISORY_SOURCES_ENABLED=false` until you accept each source's usage terms, rate limits, and production reliability constraints.

## Safe environment variables

```env
PROVIDER_LIVE_ENABLED=true
PROVIDER_LIVE_NETWORK_ENABLED=true
PROVIDER_LIVE_ADVISORY_SOURCES_ENABLED=false
OSV_API_BASE=https://api.osv.dev
NVD_API_BASE=https://services.nvd.nist.gov/rest/json/cves/2.0
NVD_API_KEY=
GITHUB_ADVISORY_API_BASE=https://api.github.com
CISA_KEV_CATALOG_URL=https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
```

## Boundaries preserved

- Not a certified audit.
- No `100% secure` claim.
- No `audited by Web3Guard` claim.
- No wallet signing.
- No seed phrase, mnemonic, or private key collection.
- No exploit automation.
- No fake monitoring or fake trust score.
