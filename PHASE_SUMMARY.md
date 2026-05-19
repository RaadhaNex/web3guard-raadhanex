# Web3Guard Home Entry UI Patch

## Goal
Add a cleaner Home entry experience so new visitors land on a Web3-focused overview before scanning.

## What changed
- Added an explicit Home link to the main navigation.
- Removed the “Web3Guard AI by RAADHANEX” text block from the header brand area.
- Kept the header logo clickable and routed to `/` for Home.
- Moved the Web3Guard AI by RAADHANEX identity into the Home hero section.
- Added Web3-specific information blocks for website/dApp, smart contracts, API/admin, and dependencies.
- Added a Home auth prompt that shows “Login to save reports” only when the visitor is not logged in.
- If the visitor is already logged in, the Home login prompt does not render.

## Backend impact
No backend files changed.

## Env impact
No env, secrets, database, payment, or scanner configuration changed.

## Safety preserved
- Pre-audit readiness wording remains visible.
- No certified audit claim added.
- No fake score/result/payment/monitoring added.
- No private key, seed phrase, mnemonic, wallet signing, exploit automation, or unauthorized active scanning flow added.
