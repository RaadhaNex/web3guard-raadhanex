export type ReadinessTone = "live" | "warning" | "blocked" | "manual" | "planned";

export type ReadinessItem = {
  title: string;
  status: string;
  tone: ReadinessTone;
  evidence: string;
  nextStep: string;
};

export type FreeTool = {
  title: string;
  outputTitle: string;
  description: string;
  template: (project: string, domain?: string) => string;
};

export const blockedClaims = [
  "certified audit",
  "100% secure",
  "AI verified/audited",
  "payment successful without verified payment flow",
  "subscription active without real backend/webhook verification",
  "wallet approved/signed",
  "exploit-proof",
];

export const trustPages = [
  { href: "/methodology", title: "Methodology", text: "How module scoring, evidence, and Not Assessed states work." },
  { href: "/limitations", title: "Limitations", text: "Clear boundaries for scanners, reports, AI, external tools, and manual review." },
  { href: "/sample-reports", title: "Sample Reports", text: "Public-safe report examples with no certified audit wording." },
  { href: "/changelog", title: "Changelog", text: "Public beta changes, real integrations, and deferred modules." },
  { href: "/security", title: "Security", text: "Responsible use, data handling, no-secrets rule, and incident contact guidance." },
  { href: "/privacy", title: "Privacy", text: "What is processed, what should never be pasted, and retention guidance." },
  { href: "/terms", title: "Terms", text: "Usage rules, safe claims, authorization, and report limitations." },
];

export const integrationReadiness: ReadinessItem[] = [
  {
    title: "Etherscan / explorer verified-source readiness",
    status: "Needs API Key unless configured",
    tone: "warning",
    evidence: "Backend has explorer source-fetch architecture and status endpoints. It must not produce source-based contract results when API key/source verification is missing.",
    nextStep: "Set ETHERSCAN_API_KEY and verify a known contract address through /scan/contract-address/status and /scanner/address.",
  },
  {
    title: "GitHub public repo scanner/status",
    status: "Live for public repos; token optional",
    tone: "live",
    evidence: "Read-only GitHub scanner is present. It uses public repo/API data and does not clone, install dependencies, execute code, or scan private repos without authorization.",
    nextStep: "Add GITHUB_API_TOKEN for better rate limits, then test one public repository from /scanner/github.",
  },
  {
    title: "Slither / Aderyn / Semgrep static tools",
    status: "Tool Not Installed / disabled until real binary exists",
    tone: "manual",
    evidence: "Static-analysis runner only executes real subprocess output when STATIC_ANALYSIS_ENABLED plus tool binary settings are available.",
    nextStep: "Install Slither/Aderyn/Semgrep on an isolated worker, set env flags, and keep missing tools marked Tool Not Installed.",
  },
  {
    title: "Mythril / Manticore / Echidna deep tools",
    status: "Worker required / Not Assessed by default",
    tone: "manual",
    evidence: "Deep analysis is gated by ownership checks and worker controls. Mythril stays Docker/worker-gated unless explicitly enabled.",
    nextStep: "Use an isolated worker with strict timeout, no dependency install by default, no network by default, and no fake symbolic/fuzz output.",
  },
  {
    title: "AI provider",
    status: "Provider Not Configured / Needs API Key",
    tone: "warning",
    evidence: "AI provider is intentionally OFF. Local rule/fix guidance remains available; no fake AI conclusion is generated.",
    nextStep: "Enable AI only with backend env, explicit provider key, safe code-sharing policy, and clear UI status.",
  },
  {
    title: "GoPlus token/wallet risk readiness",
    status: "Needs provider enablement/token for external calls",
    tone: "warning",
    evidence: "Wallet risk layer is read-only: no wallet connect, no signing, no seed/private-key collection. Provider data appears only when GOPLUS_ENABLED is true.",
    nextStep: "Enable GOPLUS only after terms/privacy review; otherwise show local wallet UX checklist and Provider Not Configured.",
  },
  {
    title: "Payment / UPI / Razorpay",
    status: "Deferred to final payment phase",
    tone: "blocked",
    evidence: "Pricing can be shown as request-only, but no paid/subscription success must be displayed until verification/webhook/audit logs are complete.",
    nextStep: "Do not unlock paid UI from frontend-only state. Finish Razorpay order + checkout + webhook + audit trail later.",
  },
];

export const freeTools: FreeTool[] = [
  {
    title: "Launch checklist generator",
    outputTitle: "Public beta launch checklist",
    description: "Founder-facing launch controls before public marketing, token launch, NFT mint, or dApp release.",
    template: (project: string) => `# ${project} — Launch Checklist\n\n- [ ] Domain uses HTTPS and stable production URL.\n- [ ] Security headers reviewed: CSP, HSTS, X-Frame-Options/frame-ancestors, referrer policy.\n- [ ] Smart contract source verified or Solidity source available for review.\n- [ ] Wallet transaction copy clearly explains chain, address, amount, and spender.\n- [ ] Admin roles use multisig/timelock where funds or upgrades are involved.\n- [ ] Incident contact and security.txt published.\n- [ ] Bug bounty / responsible disclosure scope prepared.\n- [ ] No private keys, seed phrases, mnemonics, or production secrets pasted into tools.`,
  },
  {
    title: "Founder/Admin OpSec checklist",
    outputTitle: "Admin OpSec checklist",
    description: "Checklist for owner keys, treasury, deployer wallets, admin dashboards, and emergency process.",
    template: (project: string) => `# ${project} — Founder/Admin OpSec\n\n- [ ] Treasury controlled by multisig, not a single hot wallet.\n- [ ] Upgrade admin separated from day-to-day deployer.\n- [ ] Hardware wallets used for production signers.\n- [ ] MFA enabled for GitHub, Vercel, Render, Supabase, email, and domain registrar.\n- [ ] Emergency pause/incident runbook documented.\n- [ ] Admin panel protected by role checks and audit logs.\n- [ ] No secrets in chat apps, screenshots, public repos, or shared drives.`,
  },
  {
    title: "Wallet UX safety checklist",
    outputTitle: "Wallet UX safety checklist",
    description: "User-protection checks for connect wallet, approve, mint, claim, bridge, swap, and Permit2 flows.",
    template: (project: string) => `# ${project} — Wallet UX Safety\n\n- [ ] Never ask for private key, seed phrase, or mnemonic.\n- [ ] Show chain/network before transaction.\n- [ ] Show verified contract/spender address with explorer link.\n- [ ] Explain approve/mint/claim/swap action before wallet opens.\n- [ ] Warn on unlimited approvals or high-value transfers.\n- [ ] Handle chain mismatch and rejected transactions clearly.\n- [ ] Avoid auto-opening wallet popups on page load.`,
  },
  {
    title: "GitHub security checklist",
    outputTitle: "GitHub security checklist",
    description: "Repo hygiene before sharing source with auditors, grants, users, or investors.",
    template: (project: string) => `# ${project} — GitHub Security\n\n- [ ] Branch protection enabled for main branch.\n- [ ] Required reviews for production changes.\n- [ ] GitHub Actions use least-privilege permissions.\n- [ ] Secrets stored in GitHub/Vercel/Render/Supabase env, not code.\n- [ ] Dependency lockfiles committed and reviewed.\n- [ ] Security policy added in SECURITY.md.\n- [ ] Dependabot or equivalent alerts enabled.`,
  },
  {
    title: "security.txt generator",
    outputTitle: "security.txt",
    description: "Responsible disclosure contact file for /.well-known/security.txt.",
    template: (project: string, domain = "example.com") => `Contact: mailto:security@${domain}\nExpires: 2027-05-19T00:00:00.000Z\nPreferred-Languages: en, hi\nCanonical: https://${domain}/.well-known/security.txt\nPolicy: https://${domain}/security\nHiring: https://${domain}/contact\n# ${project}: Do not send private keys, seed phrases, or exploit payloads.`,
  },
  {
    title: "robots.txt / sitemap guidance",
    outputTitle: "robots.txt + sitemap guidance",
    description: "Simple production crawl guidance without hiding security through robots.txt.",
    template: (_project: string, domain = "example.com") => `User-agent: *\nAllow: /\nDisallow: /dashboard\nDisallow: /admin\nDisallow: /api/private\nSitemap: https://${domain}/sitemap.xml\n\n# Note: robots.txt is not access control. Protect private routes with auth/server checks.`,
  },
  {
    title: "Foundry/Echidna starter test templates",
    outputTitle: "Foundry + Echidna starter templates",
    description: "Developer testing readiness starter, not a substitute for audit or formal verification.",
    template: (project: string) => `# ${project} — Developer Test Starter\n\n## Foundry invariant idea\n\`\`\`solidity\nfunction invariant_totalSupplyNeverExceedsCap() public {\n    assertLe(token.totalSupply(), token.cap());\n}\n\`\`\`\n\n## Echidna property idea\n\`\`\`solidity\nfunction echidna_owner_cannot_be_zero() public view returns (bool) {\n    return owner() != address(0);\n}\n\`\`\`\n\n- [ ] Add role/owner invariants.\n- [ ] Add pause/unpause authorization tests.\n- [ ] Add upgrade initializer tests.\n- [ ] Add fuzz tests for transfer/mint/burn limits.`,
  },
  {
    title: "Pre-audit pack guidance",
    outputTitle: "Pre-audit pack",
    description: "Artifacts to prepare before a manual audit, contest, or investor diligence review.",
    template: (project: string) => `# ${project} — Pre-Audit Pack\n\n- Scope: contracts, commit hash, networks, addresses.\n- Architecture diagram and trust assumptions.\n- Privileged roles and admin controls.\n- Known issues and accepted risks.\n- Test coverage summary and CI status.\n- Deployment checklist and upgrade plan.\n- External dependency list: oracles, bridges, routers, APIs.\n- Bug bounty / disclosure contact.`,
  },
  {
    title: "Bug bounty readiness template",
    outputTitle: "Bug bounty readiness",
    description: "Immunefi-style readiness baseline without claiming a live bounty exists.",
    template: (project: string) => `# ${project} — Bug Bounty Readiness\n\n## Scope\n- In scope: production contracts, dApp frontend, API endpoints, wallet flows.\n- Out of scope: social engineering, spam, physical attacks, DDoS, leaked keys not caused by project code.\n\n## Severity examples\n- Critical: direct fund loss, mint abuse, ownership takeover.\n- High: privilege escalation, bypass of user/fund protection.\n- Medium: broken access control with limited impact.\n\n## Safe harbor\nResearchers must avoid destructive testing, user harm, private key collection, and public disclosure before triage.`,
  },
  {
    title: "CI security workflow generator",
    outputTitle: "GitHub Actions CI security workflow",
    description: "Read-only CI starter. External scanners run only when installed/configured by the repo owner.",
    template: (project: string) => `name: ${project} Security Readiness\n\non:\n  pull_request:\n  workflow_dispatch:\n\npermissions:\n  contents: read\n\njobs:\n  web3guard-readiness:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Run local checks\n        run: |\n          echo "Run tests/lint here"\n          echo "Do not print secrets"\n      - name: Optional Slither/Aderyn/Mythril\n        run: |\n          echo "Install and run real tools only if your project enables them"\n          echo "Missing tools must be reported as Tool Not Installed, not faked"`,
  },
];
