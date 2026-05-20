# Web3Guard AI — Scanner Screen Cleanup Patch

This patch updates the unified scanner screen only.

## Changed
- Removed the large `Unified scanner / Launch evidence console` intro block.
- Removed the old `Projects & history` workspace block and replaced it with a compact recent-scan history panel.
- Removed the visible `Project name` input from the scanner form.
- Scanner now derives a safe project name from the submitted URL when needed.
- Removed the `Required setup` wording.
- Removed the visible `3 item(s) needed` style count and replaced it with a simpler `Needs input / Ready` state.
- Removed the passive-check explanatory line beside the run button.
- Kept optional evidence inputs for contract address, API base URL, GitHub repo URL, and Solidity source.
- Preserved login requirement, scan saving, result export, and all backend API calls.

## Safety
- Backend untouched.
- Scanner API endpoint untouched.
- Payment/env/database untouched.
- No fake result, fake score, wallet signing, or certified-audit claim added.

## Validation
- `cd frontend && npm run typecheck` passed.
