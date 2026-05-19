export const brand = {
  product: "Web3Guard AI",
  company: "RAADHANEX",
  tagline: "India-first Web3 founder pre-audit launch readiness scanner.",
  disclaimer:
    "Pre-audit readiness review only. Not a certified audit, penetration test, or guarantee of security.",
};

export const modules = [
  {
    key: "unified-url",
    title: "Unified Launch Scan",
    href: "/scanner/unified-url",
    description:
      "Single evidence-first flow for URL, contract, API, GitHub, wallet, and admin readiness.",
  },
  {
    key: "contract",
    title: "Smart Contract",
    href: "/scanner/contract",
    description:
      "Solidity rule engine with severity, evidence, business impact, and fix direction.",
  },
  {
    key: "website",
    title: "Website Surface",
    href: "/scanner/website",
    description:
      "Passive headers, HTTPS, robots, sitemap, policy pages, and launch-surface hints.",
  },
  {
    key: "github",
    title: "GitHub Repository",
    href: "/scanner/github",
    description:
      "Public repo hygiene for Solidity files, package metadata, CI, and secret-exposure patterns.",
  },
  {
    key: "address",
    title: "Contract Address",
    href: "/scanner/address",
    description:
      "Verified public source lookup when explorer keys are configured. Missing source remains Not Assessed.",
  },
  {
    key: "static-analysis",
    title: "Static Tool Status",
    href: "/scanner/static-analysis",
    description:
      "Slither, Aderyn, and related tools report output only when actually installed and enabled.",
  },
  {
    key: "api-deep",
    title: "API Readiness",
    href: "/scanner/api-deep",
    description:
      "Auth, CORS, webhook, rate-limit, admin route, and object-authorization checklist review.",
  },
  {
    key: "wallet",
    title: "Wallet Flow",
    href: "/scanner/wallet",
    description:
      "Approval, chain mismatch, blind-signing, transaction preview, and phishing-warning readiness.",
  },
  {
    key: "admin",
    title: "Admin OpSec",
    href: "/scanner/admin-opsec",
    description:
      "MFA, multisig, timelock, signer policy, role separation, and incident-response evidence.",
  },
  {
    key: "permission-map",
    title: "Permission Map",
    href: "/scanner/permission-map",
    description:
      "Owner, minter, pauser, upgrader, fee, treasury, and oracle authority mapping.",
  },
  {
    key: "launch-transparency",
    title: "Launch Transparency",
    href: "/scanner/launch-transparency",
    description:
      "Disclosure readiness for minting, pausing, blacklist, taxes, treasury, metadata, and presale controls.",
  },
  {
    key: "upgrade-safety",
    title: "Upgrade Safety",
    href: "/scanner/upgrade-safety",
    description:
      "Proxy pattern, initializer, upgrade authorization, and storage-order review.",
  },
  {
    key: "contract-diff",
    title: "Contract Diff",
    href: "/scanner/contract-diff",
    description:
      "Compare old and new Solidity source to identify newly introduced risky patterns.",
  },
  {
    key: "deep-analysis",
    title: "Deep Analysis",
    href: "/scanner/deep-analysis",
    description:
      "Symbolic and fuzz tooling stays worker-required unless real tools are configured.",
  },
];

export const nav = [
  { href: "/", label: "Home" },
  { href: "/scanner/unified-url", label: "Scan" },
  { href: "/pricing", label: "Price" },
  { href: "/results", label: "Results" },
  { href: "/report", label: "Report" },
  { href: "/docs", label: "Docs" },
  { href: "/advanced", label: "More" },
];
