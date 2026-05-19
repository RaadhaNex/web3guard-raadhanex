# Apply Patch

1. Take a backup or commit current state first.
2. Extract this ZIP at the project root.
3. Allow overwrite only for files included in this patch.
4. Do not overwrite `.env`, secrets, database credentials, Vercel variables, or Render variables.

## Validate frontend

```bash
cd frontend
npm ci --ignore-scripts
npm run typecheck
npm run build
```

## Validate backend if backend was applied

```bash
cd backend
python -m pytest tests/test_phase39_risk_intelligence.py -q
```

## Push

```bash
git status
git add .
git commit -m "Polish clean beta UI and add risk intelligence"
git push origin main
```

## After deployment check

- `/`
- `/scanner/unified-url`
- `/results`
- `/risk-intelligence`
- `/report`
- `/pricing`
- `/docs`
- `/advanced`
- Backend `/risk-intelligence/status`
- Backend `/risk-intelligence/taxonomy`
