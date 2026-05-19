# Web3Guard AI — Scroll Animated UI Patch

## Goal
Make the Web3Guard AI UI behave closer to the uploaded reference video: cinematic dark 3D feel, centered hero orb, scroll-driven card reveals, sticky storytelling cards, glow/lift motion, and animated depth across existing UI cards.

## What changed
- Added a client-side `ScrollMotionController` using IntersectionObserver.
- Existing cards/panels now reveal on scroll with staggered lift, blur removal, scale, and depth.
- Added lightweight parallax for the Home hero orb and copy.
- Added a sticky "Scroll intelligence" Home section with animated stacked cards.
- Kept Home hero orb centered and cinematic.
- Preserved simplified top navigation: Home, Scan, Price, More.
- Preserved Settings inside the icon/account dropdown instead of a separate text button.
- Kept safety copy and no-certified-audit wording.

## What was not changed
- Backend API logic was not touched.
- Scanner engine was not touched.
- Payment/Razorpay logic was not touched.
- Env/secrets/database were not touched.
- No fake score, fake result, fake monitoring, fake audit claim, wallet signing, private key collection, or exploit automation was added.

## Validation run
```bash
cd frontend
npm run typecheck
```

Result: passed.

`npm run build` started the optimized production build but timed out in the sandbox before completion; no code error appeared before timeout.
