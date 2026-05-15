# Phase 11 — GitHub Repo Scanner

## What is live

Phase 11 adds a real, read-only public GitHub repository scanner.

Live features:

- Public GitHub repo URL parsing
- GitHub repository metadata fetch
- Recursive GitHub tree scan with file limits
- Solidity file discovery
- Limited Solidity rule-engine scan for fetched `.sol` files
- `package.json` dependency hints
- frontend Web3/wallet/dangerous-rendering hints
- backend/API CORS/debug/secret/rate-limit/auth hints
- config/deployment script discovery
- `.env` and secret-like path/content detection
- dashboard save support
- unified URL scanner can now run GitHub scanning when repo URL is provided

## Real-only boundaries

The repo scanner does **not**:

- clone repositories
- execute code
- install dependencies
- run `npm audit`
- run tests
- connect wallets
- collect private keys
- scan private repos unless a real GitHub token is configured and authorized
- run Slither/Aderyn/Mythril yet
- claim certified audit results

## Environment

`GITHUB_API_TOKEN` is optional for public repositories but recommended to reduce GitHub rate-limit issues.

```env
GITHUB_API_BASE=https://api.github.com
GITHUB_API_TOKEN=
GITHUB_SCAN_TIMEOUT_SECONDS=12
MAX_GITHUB_SCAN_PER_HOUR=20
MAX_GITHUB_FILES=1200
MAX_GITHUB_FILE_BYTES=180000
MAX_GITHUB_TOTAL_BYTES=900000
MAX_GITHUB_SOLIDITY_FILES=8
```

## API

```http
GET /scan/github/status
POST /scan/github-repo
```

Payload:

```json
{
  "repo_url": "https://github.com/owner/repo",
  "project_name": "My Web3 Project",
  "branch": "main",
  "authorization_confirmed": true,
  "real_only_acknowledged": true
}
```

## Frontend

Open:

```text
/scanner/github
```

## How to test locally

```powershell
cd backend
PYTHONPATH=. pytest -q
python ../scripts/backend_smoke.py
```

```powershell
cd frontend
npm install
npm run typecheck
npm run dev
```

Then open:

```text
http://localhost:3000/scanner/github
```

## What remains for later real phases

- private GitHub repo OAuth/app integration
- Slither/Aderyn/Mithril worker execution
- dependency vulnerability database integration
- repo PR comments / GitHub Action
- source-to-report diff workflow
- auto-generated patch suggestions after user approval
