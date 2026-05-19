import Link from "next/link";

const findings = [
  ["CRITICAL", "Reentrancy path in withdraw()"],
  ["CRITICAL", "Unchecked token transfer authority"],
  ["HIGH", "Wallet approval preview missing"],
  ["HIGH", "Admin emergency role review needed"],
  ["MEDIUM", "security.txt / disclosure workflow missing"],
];

const highlights = [
  "Website · dApp · API · contract · wallet · admin OpSec",
  "Live passive checks + honest Not Assessed separation",
  "Hindi-friendly founder guidance + export-ready reports",
  "No wallet signing · no seed phrase collection · no exploit automation",
];

const signalCards = [
  ["53", "Rule checks"],
  ["6+", "Launch surfaces"],
  ["₹0", "Public beta"],
  ["24/7", "Readiness view"],
];

const commandSnippets = [
  "website://app.project.com",
  "github://raadhanex/protocol",
  "contract://VulnToken.sol",
  "api://launch-ready/v1",
];

export function Hero() {
  return (
    <section className="quantum-hero relative overflow-hidden border-b border-white/[0.07]">
      <div className="pointer-events-none absolute inset-0 w3g-cyber-grid opacity-80" />
      <div className="pointer-events-none absolute left-[-10rem] top-[-12rem] h-[38rem] w-[38rem] rounded-full bg-cyan/10 blur-3xl" />
      <div className="pointer-events-none absolute right-[-12rem] top-8 h-[34rem] w-[34rem] rounded-full bg-purple-500/10 blur-3xl" />

      <div className="relative mx-auto grid min-h-[calc(100vh-56px)] max-w-7xl items-center gap-12 px-4 py-14 sm:px-6 lg:grid-cols-[1.02fr_0.98fr] lg:px-8 lg:py-20">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan/20 bg-white/[0.035] px-3.5 py-1.5 backdrop-blur-xl">
            <span className="pulse-dot h-2 w-2 rounded-full bg-cyan shadow-[0_0_18px_rgba(6,182,212,.85)]" />
            <span className="text-[11px] font-black uppercase tracking-[0.22em] text-cyan">Quantum launch mode</span>
            <span className="text-xs font-semibold text-slate-300">Futuristic UI + real-only scan posture</span>
          </div>

          <h1 className="max-w-5xl text-[clamp(3rem,7vw,5.65rem)] font-black leading-[0.92] tracking-[-0.08em] text-white">
            Futuristic security
            <span className="block">for Web3 teams</span>
            <span className="text-gradient block text-glow">before launch goes live.</span>
          </h1>

          <p className="mt-7 max-w-2xl text-[1.05rem] leading-8 text-slate-400">
            Web3Guard AI now moves like a premium command center: 3D-inspired surfaces, motion-rich scan presentation, and cleaner professional copy—while still keeping every result honest, pre-audit, and evidence-first.
          </p>

          <div className="mt-9 flex flex-wrap gap-3">
            <Link href="/scanner/unified-url" className="btn-primary">Launch free scan →</Link>
            <Link href="/sample-reports" className="btn-secondary">See report flow</Link>
          </div>

          <p className="mt-4 text-xs font-medium text-slate-500">
            No fake claims · No certified audit wording · Clean founder-friendly UX
          </p>

          <div className="mt-8 grid gap-3 sm:grid-cols-2">
            {commandSnippets.map((line, index) => (
              <div key={line} className="command-line">
                <span className="kbd-chip">0{index + 1}</span>
                <p className="mono min-w-0 truncate text-xs text-slate-300">{line}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {signalCards.map(([value, label]) => (
              <div key={label} className="stat-slab px-4 py-4">
                <p className="text-2xl font-black tracking-tight text-white">{value}</p>
                <p className="mt-1 text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">{label}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="scan-door-shell perspective-card">
          <div className="scan-door-left" />
          <div className="scan-door-right" />
          <div className="holo-orb" />
          <div className="holo-ring" />
          <div className="holo-ring-2" />
          <div className="scan-door-label mono">scan chamber opening</div>

          <div className="relative z-[2] perspective-inner">
            <div className="threat-tape mb-4">
              <div className="threat-track">
                {[...highlights, ...highlights].map((item, index) => (
                  <span key={`${item}-${index}`} className="badge badge-cyan">{item}</span>
                ))}
              </div>
            </div>

            <div className="terminal-card relative overflow-hidden rounded-[24px]">
              <div className="hud-grid" />
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_55%_at_50%_0%,rgba(6,182,212,0.10),transparent)]" />
              <div className="relative">
                <div className="flex items-center justify-between border-b border-cyan/10 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full bg-red-400" />
                    <span className="h-3 w-3 rounded-full bg-yellow-300" />
                    <span className="h-3 w-3 rounded-full bg-emerald-400" />
                  </div>
                  <p className="mono text-[11px] text-slate-500">quantum.scan — launch-readiness.session</p>
                </div>

                <div className="p-5 sm:p-6">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="mono text-xs font-bold uppercase tracking-[0.22em] text-cyan">▸ Web3Guard AI — unified scan result</p>
                      <p className="mt-2 text-xs text-slate-500">3D phase upgrade · cleaner presentation · same real-only boundaries</p>
                    </div>
                    <span className="sev-critical">Critical</span>
                  </div>

                  <div className="mt-6 grid gap-4 sm:grid-cols-[0.9fr_1.1fr]">
                    <div className="glass-tile p-4">
                      <div className="flex items-end justify-between gap-4">
                        <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-500">Launch confidence</p>
                        <p className="mono text-xl font-black text-red-200">34 / 100</p>
                      </div>
                      <div className="mt-3 h-3 overflow-hidden rounded-full border border-red-400/20 bg-white/[0.05]">
                        <div className="score-fill h-full w-[34%] rounded-full bg-gradient-to-r from-red-500 via-orange-400 to-yellow-300 shadow-[0_0_24px_rgba(239,68,68,.45)]" />
                      </div>
                      <p className="mt-2 flex items-center gap-2 text-sm font-bold text-red-200"><span className="h-2 w-2 rounded-full bg-red-400" /> Critical launch risk</p>
                    </div>

                    <div className="glass-tile p-4">
                      <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-500">Active modules</p>
                      <div className="mt-3 flex flex-wrap gap-2 text-xs">
                        <span className="badge badge-cyan">Website assessed</span>
                        <span className="badge badge-green">Contract rule engine</span>
                        <span className="badge badge-amber">Wallet evidence needed</span>
                        <span className="badge badge-purple">Admin OpSec partial</span>
                      </div>
                      <p className="mt-4 text-sm leading-6 text-slate-400">
                        Missing modules remain outside the scored result so the UI stays honest even when it looks premium.
                      </p>
                    </div>
                  </div>

                  <div className="mt-6">
                    <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-500">Priority findings</p>
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
                    <p>▸ PDF / HTML / MD / JSON delivery flow stays available</p>
                    <p>▸ Not Assessed modules separated from confidence score</p>
                    <p>▸ Clean UI upgrade does not change real-only security policy</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
