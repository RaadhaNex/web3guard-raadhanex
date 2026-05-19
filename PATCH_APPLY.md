# Apply Phase 15 Sentinel Patch

## Apply
```powershell
cd C:\web\web3guard
Expand-Archive -Path "C:\path\to\web3guard_phase15_sentinel_patch.zip" -DestinationPath . -Force
```

## Test
```powershell
cd C:\web\web3guard\backend
python -m pytest -q

cd ..\frontend
npm run typecheck
npm run build
```

## Push
```powershell
cd C:\web\web3guard
git status
git add .
git commit -m "Add Sentinel monitoring intelligence core"
git push origin main
```

## Do not commit data
Do not commit generated local files such as:
- `backend/app/data/db/sentinel_vulnerability_index.jsonl`
- `backend/app/data/db/sentinel_alerts.jsonl`
- `backend/app/data/db/sentinel_matches.jsonl`
- `backend/app/data/db/sentinel_disclosures.jsonl`
