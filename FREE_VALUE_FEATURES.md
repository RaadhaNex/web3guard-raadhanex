# Free Value Features

The public beta includes free tools that help founders, developers, and security teams prepare before manual audit or launch.

## Included tools

### Launch checklist generator
Creates a project-specific checklist for HTTPS, security headers, verified source, wallet copy, admin controls, security contact, and disclosure readiness.

### Founder/Admin OpSec checklist
Covers multisig, hardware wallets, MFA, deployer separation, emergency runbooks, and secret handling.

### Wallet UX safety checklist
Covers chain display, spender address, approval warnings, transaction explanation, rejected transaction handling, and no seed/private-key requests.

### GitHub security checklist
Covers branch protection, least-privilege CI, secrets hygiene, dependency alerts, and SECURITY.md.

### security.txt generator
Generates a safe responsible-disclosure starting file for `/.well-known/security.txt`.

### robots.txt / sitemap guidance
Provides basic crawl guidance while warning that robots.txt is not access control.

### Foundry/Echidna starter templates
Provides starter invariant/property examples for developer readiness. It does not claim formal verification or audit coverage.

### Pre-audit pack guidance
Helps teams prepare scope, architecture, roles, known risks, tests, deployment plan, and dependencies.

### Bug bounty readiness template
Helps define scope, severity examples, safe harbor, and triage expectations.

### CI security workflow generator
Generates a read-only GitHub Actions starter that avoids printing secrets and does not fake missing scanner tools.

## Boundaries
These tools are generators/checklists. They do not execute external scanners, connect wallets, sign transactions, process payments, or use AI unless later configured explicitly.
