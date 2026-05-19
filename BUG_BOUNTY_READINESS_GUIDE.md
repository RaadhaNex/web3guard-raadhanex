# Bug Bounty Readiness Guide

This guide helps prepare a responsible disclosure or bounty-style program. It does not mean a bounty is live or funded.

## 1. Define scope
Example in-scope areas:

- Production smart contracts
- dApp frontend
- API backend
- Wallet transaction flow
- Admin panel authorization
- Authentication/session handling

Example out-of-scope areas:

- Social engineering
- Physical attacks
- Spam or DDoS
- Publicly known vulnerable dependencies without exploit path
- Attacks requiring leaked keys not caused by project code
- Destructive testing against users or funds

## 2. Severity examples
Critical:

- Direct theft or permanent lock of user/project funds
- Ownership/admin takeover
- Unauthorized mint or withdrawal

High:

- Privilege escalation
- Bypass of critical access control
- Severe wallet transaction deception

Medium:

- Limited authorization bypass
- Sensitive metadata leak without direct fund loss
- Broken security headers with practical impact

Low/informational:

- Minor UX confusion
- Missing best-practice header without exploit path
- Documentation ambiguity

## 3. Safe harbor
Researchers should:

- Avoid user harm
- Avoid destructive testing
- Avoid private key/seed phrase collection
- Avoid public disclosure before triage window
- Use minimal proof-of-concept needed to demonstrate risk

## 4. Submission template
Ask researchers to include:

- Summary
- Affected URL/contract/file
- Steps to reproduce
- Impact
- Suggested fix
- Wallet/address used for testing if relevant
- Evidence screenshots/logs without secrets

## 5. Triage workflow
- Confirm receipt.
- Reproduce safely.
- Assign severity.
- Decide fix owner.
- Patch and verify.
- Credit/pay if a live bounty policy exists.
- Publish postmortem only when safe.

## 6. Web3Guard AI usage
Use Web3Guard reports as preparation/evidence organization, not as final proof of exploitability or bounty severity.
