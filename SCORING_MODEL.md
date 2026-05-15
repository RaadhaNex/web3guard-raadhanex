# Web3Guard AI Scoring Model — Phase 3

Every module starts at 100.

## Penalties

- Critical: -25
- High: -15
- Medium: -8
- Low: -3
- Info: -1

## Confidence multiplier

- High confidence: 1.0x
- Medium confidence: 0.7x
- Low confidence: 0.4x

## Category cap

Each category has a 40-point penalty cap. This prevents repeated versions of the same issue from destroying the score unfairly.

## Contract scanner categories

- metadata
- access_control
- reentrancy
- low_level_call
- randomness
- centralization
- upgradeability
- observability
- gas
- token_standard
- nft_metadata
- arithmetic
- encoding
- scope

## Score labels

- 90–100: Launch Ready with Minor Notes
- 75–89: Low Risk, Fix Recommended
- 60–74: Medium Risk, Fix Before Launch
- 40–59: High Risk, Manual Review Recommended
- 0–39: Critical Launch Risk

## Important note

The score is a **launch-readiness score**, not proof that the contract is safe. Critical and high findings require manual review.


## Phase 3 report layer

The combined report uses the module scores plus severity rollup to generate an executive summary, priority action plan, limitations, and package recommendation. Missing modules are clearly shown and reduce report confidence.


## Phase 5.8 final report scoring behavior

The combined report uses the existing module weights:

- Smart Contract: 35%
- Website Surface: 15%
- dApp Frontend: 15%
- API Backend: 15%
- Wallet Flow: 10%
- Founder/Admin OpSec: 10%

If all six modules are present, `overall_score` is returned.

If only some modules are present, `overall_score` is `null` and `available_score` is returned. This prevents a single clean module from being falsely shown as a full launch-readiness score.

Coverage confidence:

- `high`: all six modules assessed
- `medium`: most modules assessed
- `limited`: only part of launch surface assessed
- `low`: single-module or very low-coverage report

The UI must show missing modules clearly before the report is shared with clients.
