# Web3Guard AI — UI-3D Full Site Patch

## Goal
Convert the clean beta UI into a fuller video-inspired cinematic dark SaaS experience while preserving Web3Guard AI by RAADHANEX branding and the honest pre-audit product boundary.

## What changed
- Home now uses a full-screen cinematic hero instead of a small orb/card layout.
- Risk intelligence orb can render as hero, compact, or card variant.
- Core public pages are aligned to the same premium 3D/glass design language:
  - Home
  - Scanner
  - Results
  - Report
  - Pricing
  - Docs
  - More / Advanced
  - Risk Intelligence
- Header/nav state from previous branding patch is preserved:
  - Home
  - Scan
  - Price
  - More
  - Settings icon
  - Web3Guard AI by RAADHANEX branding
- Footer updated to match the new cinematic/glass visual language.
- Global CSS adds reusable cinematic panels/cards/backgrounds so older pages using card/glass/clean classes also look closer to the new theme.

## Safety/product rules preserved
- No fake result.
- No fake score.
- No fake payment success.
- No certified audit claim.
- No all-vulnerability-found claim.
- No private key, seed phrase, or mnemonic collection.
- No wallet signing.
- No exploit automation.
- Missing checks/tools/providers must remain visible as Not Assessed / Tool Not Installed / Needs API Key / Provider Not Configured / Manual Review Required.

## Backend impact
No backend, env, database, payment, scanner engine, or provider code was touched.
