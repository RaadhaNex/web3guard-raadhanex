import Link from "next/link";

const primaryModules = [
  {
    title: "Unified Launch Scan",
    href: "/scanner/unified-url",
    icon: "◈",
    badge: "Recommended",
    description: "One clean flow for website, dApp, API, contract, GitHub, wallet, and admin evidence.",
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
    icon: "⌁",
    badge: "Passive",
    description: "Review public launch signals such as HTTPS, headers, robots, sitemap, and policy visibility.",
  },
  {
    title: "GitHub Repository",
    href: "/scanner/github",
    icon: "⌬",
    badge: "Repo hygiene",
    description: "Check Solidity presence, dependency hygiene, CI hints, and secret exposure patterns.",
  },
  {
    title: "Contract Address",
    href: "/scanner/address",
    icon: "0x",
    badge: "Explorer ready",
    description: "Use verified public source when explorer API keys are configured; missing source stays Not Assessed.",
  },
  {
    title: "Static Tool Status",
    href: "/scanner/static-analysis",
    icon: "ST",
    badge: "Honest status",
    description: "Slither, Aderyn, and similar tools only report output when real tooling is installed and enabled.",
  },
];

const deepModules = [
  ["API Readiness", "/scanner/api-deep", "Auth, CORS, webhook, rate-limit, and BOLA/IDOR checklist review."],
  ["Wallet Flow", "/scanner/wallet", "Approval, chain mismatch, phishing-warning, and transaction-preview readiness."],
  ["Admin OpSec", "/scanner/admin-opsec", "MFA, multisig, role separation, treasury, timelock, and incident-response evidence."],
  ["Permission Map", "/scanner/permission-map", "Owner, minter, pauser, upgrader, treasury, fee, and oracle authority mapping."],
  ["Launch Transparency", "/scanner/launch-transparency", "Disclosure readiness for taxes, blacklist, pausing, treasury, minting, and presale controls."],
  ["Upgrade Safety", "/scanner/upgrade-safety", "Proxy, initializer, upgrade authorization, and storage-order checklist review."],
  ["Contract Diff", "/scanner/contract-diff", "Compare old and new source to surface newly introduced risky patterns."],
  ["Deep Analysis", "/scanner/deep-analysis", "Mythril, Manticore, and Echidna remain worker-required unless configured."],
];

const trustNotes = [
  "No wallet signing",
  "No seed phrase collection",
  "No exploit automation",
  "Missing tools show Not Assessed",
];

const flow = [
  ["01", "Collect", "URL, source code, repo, wallet notes, and admin evidence"],
  ["02", "Assess", "Only passive or user-supplied authorized evidence is scored"],
  ["03", "Separate", "Not Assessed modules stay outside launch confidence"],
  ["04", "Export", "PDF, HTML, Markdown, and JSON artifacts"],
];

export default function ScannerPage() {
  return (
    <main className="relative overflow-hidden">
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <div>
            <p className="section-label">Scanner command center</p>
            <h1 className="mt-4 max-w-4xl text-4xl font-black tracking-[-0.06em] sm:text-6xl">
              A more futuristic scan hub with the same honest security boundaries.
            </h1>
            <p className="mt-5 max-w-3xl text-base leading-8 text-slate-300 sm:text-lg">
              Choose a module, feed evidence you own or are authorized to review, and get cleaner findings, fix guidance, limitations, and export-ready output without noisy marketing text.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/scanner/unified-url" className="btn-primary">Start unified scan →</Link>
              <Link href="/sample-reports" className="btn-secondary">View sample report</Link>
              <Link href="/methodology" className="btn-secondary">Scoring methodology</Link>
            </div>
            <div className="mt-7 flex flex-wrap gap-2">
              {trustNotes.map((note) => (
                <span key={note} className="badge badge-cyan">{note}</span>
              ))}
            </div>
          </div>

          <div className="scan-door-shell">
            <div className="scan-door-left" />
            <div className="scan-door-right" />
            <div className="holo-orb" />
            <div className="scan-door-label mono">scan flow active</div>
            <div className="relative z-[2] grid gap-4 pt-10">
              <div className="terminal-card rounded-[24px] p-4 sm:p-5">
                <div className="flex items-center justify-between border-b border-white/[0.07] pb-4">
                  <div className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full bg-red-400/90" />
                    <span className="h-3 w-3 rounded-full bg-amber-300/90" />
                    <span className="h-3 w-3 rounded-full bg-emerald-400/90" />
                  </div>
                  <p className="mono text-xs uppercase tracking-[0.18em] text-slate-500">scan-flow.preview</p>
                </div>
                <div className="mt-5 grid gap-3 text-sm">
                  {flow.map(([step, title, text]) => (
                    <div key={step} className="glass-tile p-4">
                      <p className="mono text-xs font-bold text-cyan">{step} / {title}</p>
                      <p className="mt-1 text-slate-300">{text}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="threat-tape">
                <div className="threat-track">
                  {[...trustNotes, ...trustNotes].map((note, index) => (
                    <span key={`${note}-${index}`} className="badge badge-purple">{note}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {primaryModules.map((module) => (
            <Link key={module.href} href={module.href} className="glass-tile group block p-6 transition hover:-translate-y-1">
              <div className="mb-5 flex items-start justify-between gap-4">
                <div className="grid h-12 w-12 place-items-center rounded-[14px] border border-cyan/25 bg-cyan/10 mono text-sm font-black text-cyan shadow-soft">
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

      <section className="border-y border-cyan/10 bg-cyan/[0.025]">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="section-label">Advanced modules</p>
              <h2 className="mt-3 text-3xl font-black">Add deeper evidence as your launch matures.</h2>
            </div>
            <Link href="/feature-status" className="btn-secondary">Integration status</Link>
          </div>
          <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {deepModules.map(([title, href, text]) => (
              <Link key={href} href={href} className="glass-tile p-5 transition hover:-translate-y-1 hover:border-cyan/25 hover:bg-cyan/[0.04]">
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
