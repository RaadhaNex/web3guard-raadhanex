# Pre-Audit Pack Guide

A strong pre-audit pack reduces auditor confusion and improves review quality. This guide prepares artifacts before a manual audit, contest, grant review, or investor diligence.

## 1. Scope
Include:

- Repository URL
- Commit hash
- Contracts/files in scope
- Contracts/files out of scope
- Networks and deployed addresses
- External dependencies

## 2. Architecture and trust assumptions
Include:

- System diagram
- User roles
- Admin roles
- Upgrade authority
- Oracle/bridge/router dependencies
- Treasury/funds flow
- Pausing/emergency controls

## 3. Privileged roles
Document:

- Owner/admin addresses
- Multisig/timelock usage
- Upgrade permissions
- Mint/burn/withdraw roles
- Emergency pause roles
- Key rotation process

## 4. Known issues and accepted risks
List known limitations honestly. Do not hide issues from auditors. Mark whether each issue is accepted, mitigated, or pending.

## 5. Test evidence
Include:

- Unit test command and result
- Integration test command and result
- Fuzz/invariant test command and result
- Coverage summary
- CI workflow link
- Static-analysis output if real tool ran

## 6. Deployment plan
Include:

- Deployment scripts
- Verification steps
- Initializer parameters
- Upgrade plan
- Rollback/emergency process

## 7. Frontend/API/wallet scope
For dApps, include:

- Production frontend URL
- API endpoints
- Wallet actions and transaction types
- Approval/spender addresses
- Admin panel protections
- Authentication/session flow

## 8. Disclosure and triage
Include:

- Security contact
- Expected response time
- Severity examples
- Out-of-scope testing
- Safe-harbor language

## Reminder
A pre-audit pack is preparation, not an audit certificate.
