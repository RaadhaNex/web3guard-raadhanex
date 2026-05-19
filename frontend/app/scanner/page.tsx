import Link from "next/link";
import { RiskSignalOrb } from "@/components/home/RiskSignalOrb";

const primaryModules = [
  {
    title: "Unified Launch Scan",
    href: "/scanner/unified-url",
    icon: "01",
    badge: "Recommended",
    description: "One flow for website, dApp, API, contract, GitHub, wallet, and admin evidence.",
  },
  {
    title: "Smart Contract",
    href: "/scanner/contract",
    icon: "{ }",
    badge: "Rule engine",
    description: "Paste Solidity source and get rule-based findings with severity, evidence, and fix direction.",
  },
  {
    title: "Website Surface",
    href: "/scanner/website",
    icon: "WEB",
    badge: "Passive",
    description: "Review HTTPS, headers, robots, sitemap, security.txt, and policy visibility.",
  },
  {
    title: "GitHub Repository",
    href: "/scanner/github",
    icon: "GH",
    badge: "Repo hygiene",
    description: "Check public repo signals, dependency metadata, CI hints, and secret-exposure patterns.",
  },
  {
    title: "Contract Address",
    href: "/scanner/address",
    icon: "0x",
    badge: "Explorer",
    description: "Use verified source when explorer keys are configured; missing source stays Not Assessed.",
  },
  {
    title: "Static Tool Status",
    href: "/scanner/static-analysis",
    icon: "ST",
    badge: "Real tools",
    description: "Slither, Semgrep, Aderyn, and related tools show output only when installed and enabled.",
  },
];

const advancedModules = [
  ["API Readiness", "/scanner/api-deep", "Auth, CORS, webhook, rate-limit, and object-authorization checklist review."],
  ["Wallet Flow", "/scanner/wallet", "Approval, chain mismatch, phishing-warning, and transaction-preview readiness."],
  ["Admin OpSec", "/scanner/admin-opsec", "MFA, multisig, role separation, treasury, timelock, and incident-response evidence."],
  ["Permission Map", "/scanner/permission-map", "Owner, minter, pauser, upgrader, treasury, fee, and oracle authority mapping."],
  ["Launch Transparency", "/scanner/launch-transparency", "Disclosure readiness for taxes, blacklist, pausing, treasury, minting, and presale controls."],
  ["Upgrade Safety", "/scanner/upgrade-safety", "Proxy, initializer, upgrade authorization, and storage-order checklist review."],
  ["Contract Diff", "/scanner/contract-diff", "Compare old and new source to surface newly introduced risky patterns."],
  ["Deep Analysis", "/scanner/deep-analysis", "Mythril, Manticore, and Echidna remain worker-required unless configured."],
];

const trustNotes = ["No private key collection", "No wallet signing", "No exploit automation", "No fake pass"];

const resultStates = [
  ["Assessed", "A real rule, provider, or uploaded evidence produced a check."],
  ["Not Assessed", "No evidence was supplied or the provider/tool is not configured."],
  ["Manual Review Required", "A human review is needed before launch decisions."],
  ["Tool Not Installed", "Worker/runtime does not have the tool available."],
] as const;

export default function ScannerPage() {
  return (
    <main className="cinematic-page-shell relative overflow-hidden">
      <section className="cinematic-page-hero mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-[0.95fr_0.85fr] lg:items-center">
          <div>
            <p className="section-label">Scanner</p>
            <h1 className="mt-4 max-w-4xl text-4xl font-black tracking-[-0.07em] sm:text-6xl">
              Start with one cinematic readiness scan.
            </h1>
            <p className="mt-5 max-w-3xl text-base leading-8 text-slate-300 sm:text-lg">
              Choose a module, supply evidence you own or are authorized to review, and get findings, missing checks, limitations, and export-ready output without unsafe audit claims.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/scanner/unified-url" className="btn-primary">Start unified scan →</Link>
              <Link href="/results" className="btn-secondary">See result states</Link>
              <Link href="/methodology" className="btn-secondary">Methodology</Link>
            </div>
            <div className="mt-7 flex flex-wrap gap-2">
              {trustNotes.map((note) => (
                <span key={note} className="badge badge-cyan">{note}</span>
              ))}
            </div>
          </div>

          <div className="scanner-hero-orb hidden lg:block">
            <RiskSignalOrb variant="compact" />
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-8 sm:px-6 lg:px-8">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {resultStates.map(([title, text]) => (
            <div key={title} className="cinematic-mini-card p-4">
              <p className="font-black text-white">{title}</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-14 sm:px-6 lg:px-8">
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {primaryModules.map((module) => (
            <Link key={module.href} href={module.href} className="glass-tile cinematic-card group block p-6 transition hover:-translate-y-1">
              <div className="mb-5 flex items-start justify-between gap-4">
                <div className="grid h-12 w-12 place-items-center rounded-[14px] border border-cyan/25 bg-cyan/10 mono text-xs font-black text-cyan shadow-soft">
                  {module.icon}
                </div>
                <span className="badge badge-cyan">{module.badge}</span>
              </div>
              <h2 className="text-xl font-black text-white">{module.title}</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">{module.description}</p>
              <p className="mt-5 text-sm font-bold text-cyan opacity-80 transition group-hover:translate-x-1 group-hover:opacity-100">Open scanner →</p>
            </Link>
          ))}
        </div>
      </section>

      <section className="cinematic-band border-y border-cyan/10">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="section-label">Advanced evidence</p>
              <h2 className="mt-3 text-3xl font-black">Use deeper modules only when needed.</h2>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-400">
                These tools stay available for detailed review, but the main product path remains simple for beta users.
              </p>
            </div>
            <Link href="/advanced" className="btn-secondary">Open advanced hub</Link>
          </div>
          <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {advancedModules.map(([title, href, text]) => (
              <Link key={href} href={href} className="glass-tile cinematic-card p-5 transition hover:-translate-y-1 hover:border-cyan/25 hover:bg-cyan/[0.04]">
                <p className="text-base font-black text-white">{title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
