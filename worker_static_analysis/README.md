# Web3Guard Isolated Static Analysis Worker

This worker intentionally uses a tiny stdlib ASGI app instead of FastAPI/Starlette. Semgrep/Slither can pull dependency versions that conflict with FastAPI's Starlette expectations on Render. The worker only needs three JSON endpoints, so avoiding FastAPI removes the startup conflict while keeping the same API contract.

## Render settings

Root Directory:

```text
worker_static_analysis
```

Build Command:

```bash
python -V && python -m pip install --upgrade pip setuptools wheel && python -m pip install -r requirements.txt && python -m py_compile main.py && python -m pip show semgrep slither-analyzer
```

Start Command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Required env

```env
PYTHON_VERSION=3.12.8
APP_ENV=production
STATIC_ANALYSIS_ENABLED=true
STATIC_WORKER_TOKEN=<same strong token used by main backend>
PROFESSIONAL_WORKER_SERVICE_ROLE=isolated_worker
PROFESSIONAL_WORKER_ISOLATED_RUNTIME_CONFIRMED=true
PROFESSIONAL_WORKER_ALLOW_LOCAL_EXECUTION=true
PROFESSIONAL_WORKER_NETWORK_ENABLED=false
SLITHER_ENABLED=true
SEMGREP_ENABLED=true
ADERYN_ENABLED=false
```

## Test

```powershell
curl.exe https://web3guard-static-worker.onrender.com/health
$TOKEN="paste-token"
curl.exe -H "Authorization: Bearer $TOKEN" https://web3guard-static-worker.onrender.com/static-analysis/status
```

Expected after a successful deploy:

```json
"semgrep": { "installed": true, "will_run": true }
```

Slither may be installed but can still need Solidity compiler support for some contracts. Aderyn remains disabled until its binary is installed.
