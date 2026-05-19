# How to Apply This Patch

1. Extract this ZIP into the root of your existing Web3Guard project.
2. Allow files to replace existing files with the same paths.
3. Run validation:

```bash
cd frontend
npm run typecheck
npm run build
```

4. Push to GitHub:

```bash
git status
git add .
git commit -m "Restore brand header and simplify navigation"
git push origin main
```

## Pages to check

- `/`
- `/scanner/unified-url`
- `/pricing`
- `/results`
- `/report`
- `/docs`
- `/settings/language`
- Header More dropdown on desktop
- Mobile hamburger menu
