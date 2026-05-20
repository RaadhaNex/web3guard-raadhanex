# Phase 42 — OpenZeppelin Pattern Intelligence Engine

## Goal

Add a safe, evidence-first module that compares supplied Solidity/source/import evidence against common OpenZeppelin-style secure contract patterns.

This phase does **not** claim OpenZeppelin certification, an official OpenZeppelin scanner, or a certified audit.

## What it checks

- ERC20 / ERC721 / ERC1155 standard pattern signals
- Ownable / Ownable2Step / AccessControl access-control signals
- ReentrancyGuard / nonReentrant signals
- Pausable / emergency stop controls
- SafeERC20 wrapper usage
- Upgradeable / Initializable / UUPS signals
- TimelockController governance signals

## Output per finding

Each finding includes:

- rule id
- title
- family
- status
- severity
- priority
- confidence
- CWE mapping where applicable
- evidence
- impact
- future risk
- fix plan
- verification steps
- human review requirement
- limitation

## Safe status rules

If source/evidence is missing, the module returns `Not assessed yet` instead of fake security approval.

If OpenZeppelin imports are detected, the module says `OpenZeppelin pattern detected`, not `audited` or `certified`.

If custom token/admin/fund-flow signals are found without standard patterns, the module explains the risk and asks for manual review.

## Blocked claims

The claim checker blocks wording such as:

- OpenZeppelin certified
- audited by OpenZeppelin
- official OpenZeppelin scanner
- OpenZeppelin partner
- OpenZeppelin-level audit
- guaranteed OpenZeppelin safe
- 100% secure
- finds all bugs
- all vulnerabilities found

## New backend endpoints

```text
GET  /openzeppelin-pattern/status
GET  /openzeppelin-pattern/rules
POST /openzeppelin-pattern/analyze
POST /openzeppelin-pattern/claim-check
```

## New frontend page

```text
/openzeppelin-pattern
```

## Safe public wording

```text
Web3Guard checks supplied contracts against common OpenZeppelin-style secure patterns and reports evidence, gaps, impact, future risk, and fix guidance. It is not an official OpenZeppelin scanner, not OpenZeppelin-certified, and not a certified audit.
```

## Validation

```bash
cd backend
python -m pytest -q

cd frontend
npm run typecheck
npm run build
```
