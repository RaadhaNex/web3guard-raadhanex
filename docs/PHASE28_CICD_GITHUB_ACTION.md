# Phase 28 — CI/CD GitHub Action

The GitHub Action helper calls the real `/api/v1/audit` endpoint using a real Developer API key. It does not execute contracts, install dependencies, collect private keys, or fake PR status.

Required GitHub secrets:

```text
WEB3GUARD_API_BASE_URL=https://your-backend-url
WEB3GUARD_API_KEY=wg_live_...
```

Copy these files into the repo to protect:

```text
.github/workflows/web3guard-preaudit.yml
.github/web3guard/scan.py
```

The helper writes `web3guard-report.json` locally in CI.
