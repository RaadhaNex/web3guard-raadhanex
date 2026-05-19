import Link from "next/link";
import { Hero } from "@/components/sections/Hero";
import { LaunchSurface } from "@/components/sections/LaunchSurface";
import { PricingSection } from "@/components/sections/PricingSection";
import { ProductionReadiness } from "@/components/sections/ProductionReadiness";
import { SampleScannerDemo } from "@/components/sections/SampleScannerDemo";
import { TrustBuilderSection } from "@/components/sections/TrustBuilderSection";
import { TrustStrip } from "@/components/sections/TrustStrip";

function StatsBar() {
  const stats = [
    { value: "53", label: "Rule checks", note: "launch-risk signals" },
    { value: "6+", label: "Core surfaces", note: "website to admin OpSec" },
    { value: "₹0", label: "Public beta", note: "free founder access" },
    { value: "24/7", label: "Command view", note: "always ready" },
  ];

  return (
    <section className="border-y border-cyan/[0.08] bg-cyan/[0.02]">
      <div className="mx-auto grid max-w-7xl gap-3 px-4 py-6 sm:px-6 md:grid-cols-2 lg:grid-cols-4 lg:px-8">
        {stats.map(({ value, label, note }) => (
          <div key={label} className="stat-slab px-5 py-5 text-center">
            <p className="text-3xl font-black tracking-tight text-white">{value}</p>
            <p className="mt-1 text-xs font-black uppercase tracking-[0.2em] text-slate-400">{label}</p>
            <p className="mt-2 text-xs text-slate-500">{note}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    {
      n: "01",
      title: "Collect",
      icon: "◉",
      text: "Paste only what you own or are authorized to review: URL, Solidity source, public repo, API base, or launch evidence.",
    },
    {
      n: "02",
      title: "Scan",
      icon: "◎",
      text: "The platform checks live passive signals, rule-engine findings, evidence completeness, and cleanly marks missing modules as Not Assessed.",
    },
    {
      n: "03",
      title: "Ship",
      icon: "◇",
      text: "Export a polished pre-audit package, share priorities with your team, and close obvious launch blockers before public release.",
    },
  ];

  return (
    <section className="mx-auto max-w-7xl px-4 py-18 sm:px-6 lg:px-8">
      <div className="mb-12 text-center">
        <p className="section-label justify-center">Flight path</p>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">A cleaner path from raw inputs to launch confidence.</h2>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-400">
          The new UI feels more futuristic, but the logic stays strict: only real evidence goes into the result.
        </p>
      </div>

      <div className="relative grid gap-4 md:grid-cols-3">
        <div className="pointer-events-none absolute left-[17%] right-[17%] top-12 hidden h-px bg-gradient-to-r from-transparent via-cyan/60 to-transparent md:block" />
        {steps.map(({ n, title, icon, text }) => (
          <div key={n} className="glass-tile p-6">
            <div className="flex items-start justify-between gap-3">
              <div className="grid h-12 w-12 place-items-center rounded-2xl border border-cyan/20 bg-cyan/10 mono text-xl font-black text-cyan shadow-soft">
                {icon}
              </div>
              <span className="mono text-4xl font-black leading-none text-cyan/10">{n}</span>
            </div>
            <p className="mt-5 text-xs font-black uppercase tracking-[0.24em] text-cyan">Step {n}</p>
            <h3 className="mt-2 text-xl font-black text-white">{title}</h3>
            <p className="mt-3 text-sm leading-6 text-slate-400">{text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function ComparisonTable() {
  const rows = [
    ["Free pre-audit scan", "✓", "✕", "✕", "✕"],
    ["Website + dApp + API + admin surface", "✓", "Manual", "Manual", "Manual"],
    ["Contract rule hints", "✓", "✓", "✓", "✓"],
    ["Not Assessed separation", "✓", "Manual", "Manual", "Manual"],
    ["Founder OpSec checklist", "✓", "Manual", "Manual", "Manual"],
    ["Bug bounty readiness", "✓", "Manual", "✓", "✓"],
    ["Certified audit claim", "✕", "✓", "✓", "✓"],
    ["Typical starting cost", "₹0 Free", "$15,000+", "High", "Contest budget"],
  ];

  const columns = ["Coverage", "Web3Guard AI", "Premium audit firms", "Manual consultants", "Contest platforms"];

  return (
    <section className="mx-auto max-w-7xl px-4 py-18 sm:px-6 lg:px-8">
      <div className="mb-8 text-center">
        <p className="section-label justify-center">Positioning</p>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">Founder-first preparation before expensive review cycles.</h2>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-400">
          Web3Guard AI helps teams get sharper before formal audits or bounty programs begin. It complements—not replaces—manual experts.
        </p>
      </div>

      <div className="holo-shell overflow-x-auto rounded-[28px] border border-white/[0.07] bg-white/[0.02] shadow-[0_24px_90px_rgba(6,182,212,.06)]">
        <table className="min-w-[850px] w-full border-collapse text-sm">
          <thead className="sticky top-0 bg-[#060b18]/95 backdrop-blur-xl text-left">
            <tr>
              {columns.map((col, index) => (
                <th
                  key={col}
                  className={`border-b border-white/[0.07] px-4 py-4 text-xs font-black uppercase tracking-[0.18em] ${
                    index === 1 ? "bg-cyan/[0.05] text-cyan" : "text-slate-500"
                  }`}
                >
                  {index === 1 ? <span className="mb-1 block text-[10px] text-cyan/70">Best pre-launch fit</span> : null}
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={row[0]} className={rowIndex % 2 ? "bg-white/[0.018]" : ""}>
                {row.map((cell, index) => (
                  <td
                    key={`${row[0]}-${index}`}
                    className={`border-b border-white/[0.05] px-4 py-3 ${
                      index === 1
                        ? "bg-cyan/[0.035] font-bold text-cyan"
                        : index === 0
                        ? "font-semibold text-slate-200"
                        : "text-slate-400"
                    }`}
                  >
                    {cell === "✓" ? <span className="font-black text-cyan">✓</span> : cell === "✕" ? <span className="font-black text-slate-600">✕</span> : cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SocialProof() {
  const cards = [
    ["3D", "Future-facing UI", "Premium motion, layered surfaces, and a cleaner command-center look across phases."],
    ["IND", "India-friendly", "Founder-friendly language, practical guidance, and beta positioning that stays easy to understand."],
    ["SAFE", "Safer wording", "No 100% secure promises, no certified audit claims, and no hidden provider limitations."],
    ["REAL", "Transparent outputs", "If a tool or provider is missing, the interface says so clearly instead of pretending."],
  ];

  return (
    <section className="mx-auto max-w-7xl px-4 py-18 sm:px-6 lg:px-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(([code, title, text]) => (
          <div key={title} className="glass-tile p-6 text-center">
            <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl border border-cyan/20 bg-cyan/10 mono text-sm font-black text-cyan">{code}</div>
            <h3 className="mt-4 text-base font-black text-white">{title}</h3>
            <p className="mt-2 text-xs leading-6 text-slate-400">{text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function CtaBanner() {
  return (
    <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
      <div className="quantum-stage p-8 text-center sm:p-12">
        <div className="pointer-events-none absolute left-[-8rem] top-[-8rem] h-72 w-72 rounded-full bg-cyan/10 blur-3xl" />
        <div className="pointer-events-none absolute bottom-[-10rem] right-[-8rem] h-80 w-80 rounded-full bg-purple-500/10 blur-3xl" />
        <div className="relative">
          <p className="section-label justify-center">Quantum command center</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">Run the command-center scan before launch day.</h2>
          <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-400">
            Find blockers early, keep wording safe, and export a professional result your team can actually act on.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/scanner/unified-url" className="btn-primary">Start free scan →</Link>
            <Link href="/sample-reports" className="btn-secondary">View sample reports</Link>
          </div>
          <p className="mt-4 text-xs text-slate-500">No account needed for basic use · Real-only status by design</p>
        </div>
      </div>
    </section>
  );
}

export default function HomePage() {
  return (
    <>
      <Hero />
      <StatsBar />
      <TrustStrip />
      <LaunchSurface />
      <HowItWorks />
      <SampleScannerDemo />
      <ComparisonTable />
      <ProductionReadiness />
      <TrustBuilderSection />
      <SocialProof />
      <PricingSection />
      <CtaBanner />
    </>
  );
}
