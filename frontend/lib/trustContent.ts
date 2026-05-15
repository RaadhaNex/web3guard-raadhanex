export const trustPillars = [
  {
    title: "Pre-audit readiness, not fake certification",
    text: "Web3Guard AI helps founders prepare before an expensive professional audit. Every page clearly says this is a preliminary review, not a certified audit.",
  },
  {
    title: "Safe passive scanning boundaries",
    text: "Website checks are passive by default: headers, HTTPS, robots/sitemap, and limited public signals. No brute force, no bypass, no exploit automation.",
  },
  {
    title: "Founder-friendly business impact",
    text: "Reports explain why each issue matters for funds, launch trust, user safety, admin control, and paid manual review priority.",
  },
  {
    title: "Clear paid-review scope",
    text: "Paid review packages show what is included, what needs manual review, when payment is manually verified, and when work starts.",
  },
];

export const whatWeCheck = [
  "Smart contract launch-blocking patterns and centralization risks",
  "Safe passive website headers and public launch-readiness signals",
  "dApp frontend risks: exposed public config, chain mismatch, unclear transaction UX",
  "API backend checklist: CORS, docs exposure, auth, rate limit, webhooks, admin endpoints",
  "Wallet flow risks: unlimited approvals, permit signatures, spender display, blind signing",
  "Founder/admin OpSec: multisig, timelock, private-key handling, treasury, incident response",
];

export const whatWeDoNotClaim = [
  "No certified audit claim from automated scan output",
  "No 100% security guarantee",
  "No exploit automation or destructive testing",
  "No unauthorized deep scans against third-party systems",
  "No financial, investment, tax, or legal advice",
  "No fake payment success or fake AI provider output",
];

export const policies = [
  {
    title: "Scope clarity",
    href: "/scope-refund",
    text: "Manual review deliverables depend on the selected package and material provided by the founder.",
  },
  {
    title: "Responsible use",
    href: "/responsible-use",
    text: "User must own the project or have authorization before using scanner workflows.",
  },
  {
    title: "Privacy",
    href: "/privacy",
    text: "MVP stores lead data locally; production should move to encrypted database storage with deletion/export workflow.",
  },
  {
    title: "Terms",
    href: "/terms",
    text: "Security results are guidance only and must be reviewed before production launch.",
  },
];

export const reportSamples = [
  {
    id: "erc20-sample",
    title: "ERC20 Token Launch Readiness",
    projectType: "ERC20 Token",
    score: 72,
    risk: "Medium Risk, Fix Before Launch",
    summary: "Owner centralization, missing multisig, and allowance UX require review before launch.",
    highlights: ["Owner privilege disclosure", "Multisig readiness", "Allowance UX", "Website trust headers"],
    package: "Detailed Web3 Launch Readiness Report — ₹2,999",
  },
  {
    id: "nft-mint-sample",
    title: "NFT Mint dApp",
    projectType: "NFT Mint",
    score: 65,
    risk: "Medium Risk, Fix Before Launch",
    summary: "Mint flow needs clearer transaction preview, metadata freeze plan, and website headers.",
    highlights: ["Mint UX", "Contract address visibility", "Metadata policy", "CSP/HSTS"],
    package: "Fix Suggestion Pack — ₹7,999",
  },
  {
    id: "staking-sample",
    title: "Staking dApp",
    projectType: "Staking / Rewards",
    score: 54,
    risk: "High Risk, Manual Review Recommended",
    summary: "Reward calculation, privileged admin roles, and API abuse protection require manual review.",
    highlights: ["Reward math", "Admin roles", "API rate-limit", "Treasury workflow"],
    package: "Manual Pre-Audit Review — ₹14,999+",
  },
  {
    id: "website-only-sample",
    title: "Website-only Web3 Landing Page",
    projectType: "Web3 Landing Page",
    score: 81,
    risk: "Low Risk, Fix Recommended",
    summary: "Website has HTTPS but needs stronger browser security headers and clearer anti-phishing trust copy.",
    highlights: ["CSP", "HSTS", "Official links", "Anti-phishing copy"],
    package: "Quick Risk Scan Report — ₹999",
  },
];

export const scopeRules = [
  "Free scan gives automated preliminary findings only.",
  "Paid quick reports begin after manual payment reference verification.",
  "Manual review scope is limited to submitted project material and selected package deliverables.",
  "Out-of-scope requests can be rejected or quoted separately before work starts.",
  "Once manual review work has started, refund decisions depend on delivered effort, scope, and written agreement.",
  "Critical fund-risk findings should still be reviewed by qualified professional auditors before mainnet launch.",
];
