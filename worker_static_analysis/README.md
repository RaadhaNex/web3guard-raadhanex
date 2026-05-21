# Web3Guard Isolated Static Analysis Worker

This is a separate worker service for real Slither / Semgrep / Aderyn execution.

It must be deployed separately from the public FastAPI backend. The main backend only sends safe Solidity source files to this worker when explicitly configured.

## Main backend env

Keep code execution disabled in the main backend. Add only the bridge values:

```env
STATIC_WORKER_ENABLED=true
STATIC_WORKER_AUTO_DISPATCH_ENABLED=true
STATIC_WORKER_URL=https://your-worker-service.onrender.com
STATIC_WORKER_TOKEN=<same strong secret as worker>
STATIC_WORKER_TIMEOUT_SECONDS=75
```

## Worker service env

```env
APP_ENV=production
STATIC_ANALYSIS_ENABLED=true
STATIC_WORKER_TOKEN=<same strong secret as main backend>
PROFESSIONAL_WORKER_SERVICE_ROLE=isolated_worker
PROFESSIONAL_WORKER_ISOLATED_RUNTIME_CONFIRMED=true
PROFESSIONAL_WORKER_ALLOW_LOCAL_EXECUTION=true
PROFESSIONAL_WORKER_NETWORK_ENABLED=false
SLITHER_ENABLED=true
SLITHER_BINARY=slither
SEMGREP_ENABLED=true
SEMGREP_BINARY=semgrep
ADERYN_ENABLED=false
ADERYN_BINARY=aderyn
```

## Render build command example

```bash
python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && pip install slither-analyzer semgrep
```

Aderyn is disabled by default until you install it in the isolated worker image.

## Start command

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Safety rules

- No private key / seed phrase collection.
- No dependency install during scan.
- No repo clone by worker.
- No wallet signing.
- No exploit automation.
- No certified audit or 100% secure claim.
- Missing tools return Not Assessed / Tool Not Installed / Provider Not Configured.


## Render Python version hotfix

If deploy logs show `pydantic-core` trying to build from source with Rust/maturin, the worker is running on an incompatible/new Python version and pip cannot find a compatible wheel. Keep the worker on Python 3.12.8.

This folder includes `.python-version` with `3.12.8`. For manually created Render services, also add this Environment Variable in the Render Dashboard:

```env
PYTHON_VERSION=3.12.8
```

Then clear the failed deploy and redeploy. The build log should print `Python 3.12.8` near the start.
