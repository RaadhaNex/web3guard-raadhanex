import Link from "next/link";
import { brand } from "@/lib/constants";

const findings = [
  { module: "Smart Contract", sev: "High",     hint: "Owner centralization — add multisig" },
  { module: "Website",        sev: "Medium",   hint: "CSP and HSTS headers missing" },
  { module: "Wallet Flow",    sev: "High",     hint: "Unlimited approval — add UI warning" },
  { module: "Admin OpSec",    sev: "Critical", hint: "No timelock on admin actions" },
];

const sevStyle: Record<string, string> = {
  Critical: "sev-critical",
  High:     "sev-high",
  Medium:   "sev-medium",
};

export function Hero() {
  return (
    <section className="grid-bg relative overflow-hidden border-b border-white/10">
      <div className="mx-auto grid max-w-7xl gap-12 px-4 py-20 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8 lg:py-28">

        {/* Left */}
        <div>
          <span className="badge mb-6 inline-flex items-center gap-2">
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--cyan)", display: "inline-block", flexShrink: 0 }} />
            Pre-audit security review · {brand.company}
          </span>

          <h1 className="max-w-2xl text-4xl font-black leading-tight tracking-tight sm:text-5xl lg:text-[3.25rem]">
            Web3 launch security review{" "}
            <span style={{ background: "linear-gradient(135deg,#22d3ee,#60a5fa)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              before expensive audits.
            </span>
          </h1>

          <p className="mt-5 max-w-lg text-base leading-7 text-slate-400">
            Check smart contracts, websites, dApp frontend, APIs, wallet flows, and admin risks before launch — with clear findings and affordable paid review options.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/scanner/unified-url" className="btn-primary">
              Start Free Scan
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                <path d="M2 7h10M8 3l4 4-4 4"/>
              </svg>
            </Link>
            <Link href="/sample-reports" className="btn-secondary">View Sample Report</Link>
          </div>

          <p className="mt-6 text-xs text-slate-500">{brand.disclaimer}</p>
        </div>

        {/* Right — Sample card */}
        <div className="card p-6">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">Sample output</p>
              <p className="mt-1.5 text-5xl font-black text-white leading-none">76</p>
              <p className="mt-1.5 text-xs font-semibold text-amber-400">Medium Risk · Fix Before Launch</p>
            </div>
            <div className="flex flex-col items-end gap-1.5">
              <span className="sev-critical">2 Critical</span>
              <span className="sev-high">3 High</span>
              <span className="sev-medium">1 Medium</span>
            </div>
          </div>

          <div className="space-y-2.5">
            {findings.map(({ module, sev, hint }) => (
              <div key={module} className="flex items-start gap-3 rounded-xl border border-white/[0.07] bg-white/[0.025] p-3.5">
                <span className={`${sevStyle[sev] ?? "badge"} mt-0.5 shrink-0`}>{sev}</span>
                <div className="min-w-0">
                  <p className="text-sm font-bold text-white">{module}</p>
                  <p className="mt-0.5 text-xs leading-5 text-slate-400">{hint}</p>
                </div>
              </div>
            ))}
          </div>

          <p className="mt-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 text-xs text-slate-500">
            Sample only — real scans generate findings from your actual contract and inputs.
          </p>
        </div>
      </div>
    </section>
  );
}
