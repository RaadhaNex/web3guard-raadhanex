# Mega Phase C — Phase 23 + Phase 24

Project: **Web3Guard AI by RAADHANEX**

This consolidated phase adds real-only MVP foundations for:

- **Phase 23 — Monitoring Lite**
- **Phase 24 — Threat Intelligence Feed**

## Real-only rule

No fake live monitoring, no fake hack alerts, no fake threat feed, no fake notifications, no wallet signing, and no private key collection.

Any feature that requires external infrastructure stays clearly labeled as disabled/not configured until real env values are added.

---

## Phase 23 — Monitoring Lite

### New frontend page

```text
/monitoring
```

### New backend endpoints

```text
GET  /monitoring/status
GET  /monitoring/dashboard
POST /monitoring/configs
GET  /monitoring/configs
GET  /monitoring/alerts
POST /monitoring/alerts/ingest
POST /monitoring/check
```

### What is real now

- Real monitoring config records are saved locally.
- Manual/admin alert records are saved locally.
- Optional read-only RPC check can run when configured.
- RPC check uses `eth_blockNumber` + `eth_getLogs`.
- Supported event signatures:
  - OwnershipTransferred
  - RoleGranted
  - Paused
  - Unpaused
  - Upgraded
  - Transfer mint-from-zero hint

### What is not faked

- No fake live alerts.
- No fake transaction monitoring if RPC is not configured.
- No wallet connection.
- No signing.
- No private key or seed phrase collection.
- No automatic incident response.
- No guaranteed exploit/attack detection.
- No Telegram/Discord/email delivery yet; dashboard record only.

### Manual env for optional RPC checks

```env
MONITORING_ENABLED=true
MONITORING_RPC_ENABLED=true
ETHEREUM_RPC_URL=https://your-real-rpc-url
POLYGON_RPC_URL=
BSC_RPC_URL=
ARBITRUM_RPC_URL=
OPTIMISM_RPC_URL=
BASE_RPC_URL=
AVALANCHE_RPC_URL=
```

Default stays disabled:

```env
MONITORING_ENABLED=false
MONITORING_RPC_ENABLED=false
```

---

## Phase 24 — Threat Intelligence Feed

### New frontend page

```text
/threat-intel
```

### New backend endpoints

```text
GET  /threat-intel/status
GET  /threat-intel/feed
POST /threat-intel/query
POST /threat-intel/admin/entries
POST /threat-intel/relevance
```

### What is real now

- Local/manual curated threat intelligence storage.
- Local knowledge-base entries clearly labeled as educational/manual.
- Filter by project type, chain, and tags.
- Admin/manual entry creation.
- Relevance helper for report/finding tags.

### What is not faked

- No fake live news feed.
- No fake recent hack data.
- No fake RSS/API feed.
- No fake source citations.
- Live/current threat sources are not claimed unless real integration is enabled and cited.

### Manual env

```env
THREAT_INTEL_ENABLED=true
THREAT_INTEL_LIVE_SOURCES_ENABLED=false
THREAT_INTEL_FILE=app/data/db/threat_intel.jsonl
```

---

## Tests

Backend checks passed:

```text
102 passed
python -m compileall -q . passed
backend smoke test passed
```

Frontend checks:

```text
npm run typecheck passed
next build compiled successfully, then timed out during final lint/page-data collection in sandbox
```

Run local build on laptop:

```powershell
cd frontend
npm install
npm run typecheck
npm run build
```

---

## Next mega phase

**Mega Phase D — Phase 25 + 26 + 27**

- Bug Bounty Readiness + Marketplace MVP
- Public Registry + Trust Badge
- Developer API + API Keys
