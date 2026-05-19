# Web3Guard AI — UI-3D Home Patch

## Goal
Create a premium, video-inspired Web3Guard Home experience without touching backend, scanner execution, payments, env files, secrets, or database logic.

## What changed
- Rebuilt `/` Home into a cinematic dark SaaS landing page inspired by the uploaded video style.
- Added a lightweight animated risk-intelligence orb using only React markup + CSS, no heavy 3D dependency.
- Kept Web3Guard AI by RAADHANEX branding visible and premium.
- Kept top nav simple: Home, Scan, Price, More.
- Kept Results, Report, Docs, Dashboard, Advanced, payment validation, feature status, and risk intelligence under More.
- Added top-right animated Settings icon from the earlier brand/nav patch.
- Preserved login behavior on Home: Login CTA shows when the user is signed out or Supabase browser auth is not configured; it hides when already signed in.
- Preserved safety wording: pre-audit readiness only, not a certified audit, no security guarantee, no private key/seed phrase, no wallet signing, no exploit automation.

## Files touched
Frontend only. No backend files changed.

## Validation performed
```bash
cd frontend
npm run typecheck
```
Result: passed.

```bash
cd frontend
npm run build
```
Result: production build started and reached the optimized build phase, but the sandbox hit the 5-minute timeout. No TypeScript error was produced before timeout.

## Notes
This patch is intentionally CSS/lightweight for performance. It gives the premium 3D/glow feel without adding Three.js or other heavy animation libraries.
