# PATCH APPLY GUIDE

Apply this ZIP on top of your current project root.

## Option A — Windows Explorer

1. Extract this patch ZIP.
2. Copy the extracted `frontend/` folder into your project root.
3. Allow Windows to replace the existing files.
4. Do not delete any other files.

## Option B — PowerShell

From the folder where you extracted this patch:

```powershell
Copy-Item -Path .\frontend -Destination C:\web\web3guard -Recurse -Force
```

Change `C:\web\web3guard` to your actual project path.

## Validate frontend

```bash
cd frontend
npm run typecheck
npm run build
```

## Backend validation

Backend was not changed. Run only if you want a full sanity check:

```bash
cd backend
python -m pytest -q
```

## GitHub push commands

```bash
git status
git add .
git commit -m "Polish Web3Guard clean beta UI"
git push origin main
```

## After deploy, check these live pages

- `/`
- `/scanner`
- `/scanner/unified-url`
- `/results`
- `/report`
- `/pricing`
- `/docs`
- `/advanced`
- `/payment-validation`

## Deployment/env changes

No new env variable is required by this patch.
