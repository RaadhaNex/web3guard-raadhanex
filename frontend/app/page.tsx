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
    { value: "53", label: "Rules" },
    { value: "6+", label: "Surfaces" },
    { value: "₹0", label: "Free Beta" },
    { value: "Hindi", label: "Support" },
  ];

  return (
    <section className="border-y border-cyan/[0.08] bg-cyan/[0.02]">
      <div className="mx-auto grid max-w-7xl grid-cols-2 divide-x divide-y divide-cyan/[0.06] px-4 sm:px-6 md:grid-cols-4 md:divide-y-0 lg:px-8">
        {stats.map(({ value, label }) => (
          <div key={label} className="px-4 py-6 text-center">
            <p className="text-3xl font-black tracking-tight text-white">{value}</p>
            <p className="mt-1 text-xs font-bold uppercase tracking-[0.18em] text-slate-500">{label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { n: "01", title: "Scan", icon: "🔍", text: "Paste an authorized URL, Solidity code, public GitHub repo, API URL, or contract address." },
    { n: "02", title: "Review", icon: "📊", text: "Get severity breakdown, evidence gaps, Not Assessed modules, and split launch-confidence scoring." },
    { n: "03", title: "Fix", icon: "🛠", text: "Use fix hints, checklists, and pre-audit pack guidance before manual audit or public launch." },
  ];

  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mb-12 text-center">
        <p className="section-label justify-center">How it works</p>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">Three steps from uncertainty to launch evidence.</h2>
      </div>

      <div className="relative grid gap-4 md:grid-cols-3">
        <div className="pointer-events-none absolute left-[16%] right-[16%] top-12 hidden h-px bg-gradient-to-r from-cyan via-purple-400 to-cyan md:block" />
        {steps.map(({ n, title, icon, text }) => (
          <div key={n} className="card relative p-6">
            <span className="absolute right-5 top-3 text-6xl font-black leading-none text-cyan/[0.10]">{n}</span>
            <span className="mb-5 grid h-12 w-12 place-items-center rounded-[14px] border border-cyan/20 bg-cyan/[0.07] text-2xl">{icon}</span>
            <p className="text-xs font-black uppercase tracking-[0.22em] text-cyan">{n} {title}</p>
            <h3 className="mt-3 text-xl font-black text-white">{title} with boundaries</h3>
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
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mb-8 text-center">
        <p className="section-label justify-center">Positioning</p>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">More preparation coverage. Fraction of the cost.</h2>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-400">
          Web3Guard prepares founders before expensive reviews. It does not replace certified auditors, contest judges, or manual security experts.
        </p>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-white/[0.07] bg-white/[0.02]">
        <table className="min-w-[850px] w-full border-collapse text-sm">
          <thead className="sticky top-0 bg-[#060b18] text-left">
            <tr>
              {columns.map((col, index) => (
                <th key={col} className={`border-b border-white/[0.07] px-4 py-4 text-xs font-black uppercase tracking-[0.18em] ${index === 1 ? "border-t-2 border-t-cyan bg-cyan/[0.05] text-cyan" : "text-slate-500"}`}>
                  {index === 1 ? <span className="mb-1 block text-[10px] text-cyan/70">YOU ARE HERE</span> : null}
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={row[0]} className={rowIndex % 2 ? "bg-white/[0.018]" : ""}>
                {row.map((cell, index) => (
                  <td key={`${row[0]}-${index}`} className={`border-b border-white/[0.05] px-4 py-3 ${index === 1 ? "bg-cyan/[0.035] font-bold text-cyan" : index === 0 ? "font-semibold text-slate-200" : "text-slate-400"}`}>
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
    ["🏆", "Hackathon-ready", "Quick launch evidence for teams that need to move fast."],
    ["🇮🇳", "India-first", "Hindi-friendly guidance and founder-focused public beta posture."],
    ["⚖️", "Legally safer", "No certified audit, no exploit automation, no 100% secure claims."],
    ["🔓", "Transparent", "Provider gaps are visible instead of hidden behind fake scores."],
  ];

  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(([icon, title, text]) => (
          <div key={title} className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6 text-center transition hover:-translate-y-0.5 hover:border-cyan/25 hover:bg-white/[0.04]">
            <div className="text-4xl">{icon}</div>
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
      <div className="relative overflow-hidden rounded-[28px] border border-cyan/20 bg-[linear-gradient(135deg,rgba(6,182,212,0.07),rgba(139,92,246,0.05))] p-8 text-center shadow-[0_24px_90px_rgba(6,182,212,.08)] sm:p-12">
        <div className="pointer-events-none absolute left-[-8rem] top-[-8rem] h-72 w-72 rounded-full bg-cyan/10 blur-3xl" />
        <div className="pointer-events-none absolute bottom-[-10rem] right-[-8rem] h-80 w-80 rounded-full bg-purple-500/10 blur-3xl" />
        <div className="relative">
          <p className="section-label justify-center">Ready to launch securely?</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">Scan your project before launch. It takes 5 minutes.</h2>
          <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-400">
            Find obvious launch blockers, missing evidence, and provider gaps before users, investors, or auditors see them.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/scanner/unified-url" className="btn-primary">Start Free Scan →</Link>
            <Link href="/sample-reports" className="btn-secondary">View Sample Reports</Link>
          </div>
          <p className="mt-4 text-xs text-slate-500">· No account needed · Free forever · Hindi support</p>
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
