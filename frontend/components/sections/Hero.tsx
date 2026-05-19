import Link from "next/link";

const findings = [
  ["CRITICAL", "Reentrancy in withdraw()"],
  ["CRITICAL", "Arbitrary transferFrom risk"],
  ["HIGH", "Governance flash-loan review"],
  ["HIGH", "NFT receiver safety check"],
  ["MEDIUM", "Missing CSP header evidence"],
];

const particles = [
  ["left-[8%] top-[18%]", "animation-delay-0"],
  ["left-[22%] top-[72%]", "animation-delay-200"],
  ["left-[42%] top-[14%]", "animation-delay-500"],
  ["left-[62%] top-[82%]", "animation-delay-700"],
  ["left-[78%] top-[20%]", "animation-delay-1000"],
  ["left-[90%] top-[58%]", "animation-delay-300"],
  ["left-[52%] top-[44%]", "animation-delay-100"],
  ["left-[15%] top-[48%]", "animation-delay-700"],
];

export function Hero() {
  return (
    <section className="quantum-hero relative overflow-hidden border-b border-white/[0.07]">
      <div className="pointer-events-none absolute inset-0 w3g-cyber-grid" />
      <div className="pointer-events-none absolute left-[-10rem] top-[-12rem] h-[38rem] w-[38rem] rounded-full bg-cyan/10 blur-3xl" />
      <div className="pointer-events-none absolute right-[-12rem] top-8 h-[34rem] w-[34rem] rounded-full bg-purple-500/10 blur-3xl" />

      {particles.map(([position], index) => (
        <span
          key={position}
          className={`pointer-events-none absolute ${position} h-1.5 w-1.5 rounded-full bg-cyan opacity-40 shadow-[0_0_18px_rgba(6,182,212,.8)] animate-float`}
          style={{ animationDelay: `${index * 0.32}s` }}
        />
      ))}

      <div className="relative mx-auto grid min-h-[calc(100vh-56px)] max-w-7xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.04fr_0.96fr] lg:px-8 lg:py-20">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan/20 bg-white/[0.035] px-3.5 py-1.5 backdrop-blur-xl">
            <span className="pulse-dot h-2 w-2 rounded-full bg-cyan shadow-[0_0_18px_rgba(6,182,212,.85)]" />
            <span className="text-[11px] font-black uppercase tracking-[0.22em] text-cyan">Live</span>
            <span className="text-xs font-semibold text-slate-300">Free Public Beta · India-focused full-surface scanner</span>
          </div>

          <h1 className="max-w-5xl text-[clamp(3rem,7vw,5.5rem)] font-black leading-[0.95] tracking-[-0.075em] text-white">
            Secure your Web3
            <span className="block">project before</span>
            <span className="text-gradient block text-glow">expensive audits.</span>
          </h1>

          <p className="mt-7 max-w-2xl text-[1.0625rem] leading-8 text-slate-400">
            53-rule scanner covering smart contracts, websites, dApps, admin OpSec, GitHub, and wallet UX readiness. Free public beta with Hindi-friendly guidance.
          </p>

          <div className="mt-9 flex flex-wrap gap-3">
            <Link href="/scanner/unified-url" className="btn-primary">Start Free Scan →</Link>
            <Link href="/sample-reports" className="btn-secondary">View Sample Report</Link>
          </div>

          <p className="mt-4 text-xs font-medium text-slate-500">
            · No account needed · Pre-audit only · Not a certified audit
          </p>

          <div className="mt-8 flex flex-wrap gap-3 text-xs font-bold text-slate-300">
            {[
              "🛡 53 rules",
              "⚡ 6+ surfaces",
              "🇮🇳 Hindi support",
              "₹0 free",
            ].map((item) => (
              <span key={item} className="rounded-full border border-white/[0.07] bg-white/[0.03] px-3 py-1.5">
                {item}
              </span>
            ))}
          </div>
        </div>

        <div className="terminal-card animate-float relative overflow-hidden rounded-2xl">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_0%,rgba(6,182,212,0.08),transparent)]" />
          <div className="relative">
            <div className="flex items-center justify-between border-b border-cyan/10 px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-red-400" />
                <span className="h-3 w-3 rounded-full bg-yellow-300" />
                <span className="h-3 w-3 rounded-full bg-emerald-400" />
              </div>
              <p className="mono text-[11px] text-slate-500">web3guard-scan.sol — VulnToken.sol</p>
            </div>

            <div className="p-5 sm:p-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="mono text-xs font-bold uppercase tracking-[0.22em] text-cyan">▸ Web3Guard AI — Scan Result</p>
                  <p className="mt-2 text-xs text-slate-500">Static sample transcript · real scans use submitted evidence</p>
                </div>
                <span className="sev-critical">Critical</span>
              </div>

              <div className="mt-6">
                <div className="flex items-end justify-between gap-4">
                  <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-500">Score</p>
                  <p className="mono text-xl font-black text-red-200">34 / 100</p>
                </div>
                <div className="mt-3 h-3 overflow-hidden rounded-full border border-red-400/20 bg-white/[0.05]">
                  <div className="score-fill h-full w-[34%] rounded-full bg-gradient-to-r from-red-500 via-orange-400 to-yellow-300 shadow-[0_0_24px_rgba(239,68,68,.45)]" />
                </div>
                <p className="mt-2 flex items-center gap-2 text-sm font-bold text-red-200"><span className="h-2 w-2 rounded-full bg-red-400" /> Critical Launch Risk</p>
              </div>

              <div className="mt-6">
                <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-500">Findings</p>
                <div className="mt-3 space-y-2.5">
                  {findings.map(([severity, title], index) => (
                    <div key={title} className="finding-row flex items-center gap-3 rounded-xl border border-white/[0.06] bg-black/25 px-3 py-2.5" style={{ animationDelay: `${index * 90}ms` }}>
                      <span className={severity === "CRITICAL" ? "sev-critical" : severity === "HIGH" ? "sev-high" : "sev-medium"}>{severity}</span>
                      <span className="mono min-w-0 truncate text-xs text-slate-300">{title}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-6 grid gap-2 rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.05] p-4 text-xs text-emerald-100/90">
                <p>▸ 5 inline fix hints ready</p>
                <p>▸ Full report: PDF / HTML / MD / JSON</p>
                <p>▸ Not assessed modules separated from scored evidence</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
