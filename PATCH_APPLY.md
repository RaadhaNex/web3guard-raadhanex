# How to Apply

From project root, extract this ZIP over your existing project so these files replace the same paths.

## Validate frontend

```bash
cd frontend
npm run typecheck
npm run build
```

## Backend

Backend was not touched. Backend tests are not required for this UI-only patch.

## Push

```bash
git status
git add .
git commit -m "Apply full cinematic UI polish"
git push origin main
```

## Pages to check

- /
- /scanner
- /scanner/unified-url
- /results
- /report
- /pricing
- /docs
- /advanced
- /risk-intelligence
- /settings/language
