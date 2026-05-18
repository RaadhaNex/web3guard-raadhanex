import Link from "next/link";
import { Hero } from "@/components/sections/Hero";
import { LaunchSurface } from "@/components/sections/LaunchSurface";
import { PricingSection } from "@/components/sections/PricingSection";
import { TrustStrip } from "@/components/sections/TrustStrip";
import { TrustBuilderSection } from "@/components/sections/TrustBuilderSection";
import { SampleScannerDemo } from "@/components/sections/SampleScannerDemo";

/* ── Stats bar ── */
function StatsBar() {
  const stats = [
    { value: "53",    label: "Security rules" },
    { value: "6",     label: "Surfaces scanned" },
    { value: "₹999",  label: "Starting price" },
    { value: "Hindi", label: "Explanation support" },
  ];
  return (
    <div className="border-b border-white/[0.07]" style={{ background: "rgba(34,211,238,0.04)" }}>
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-around gap-4 px-4 py-5 sm:px-6 lg:px-8">
        {stats.map(({ value, label }) => (
          <div key={label} className="text-center">
            <p className="text-2xl font-black text-white">{value}</p>
            <p className="mt-0.5 text-xs font-medium text-slate-400">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── How it works ── */
function HowItWorks() {
  const steps = [
    { n: "01", title: "Scan",   icon: "🔍", text: "Paste contract, enter URL, or fill checklists. Free — no account needed." },
    { n: "02", title: "Review", icon: "📊", text: "Get score, severity breakdown, business impact, and inline fix code." },
    { n: "03", title: "Fix",    icon: "⚡", text: "Apply rule-based fixes yourself, or request expert manual review." },
  ];
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mb-10 text-center">
        <p className="section-label">How it works</p>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">Launch-ready in three steps.</h2>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        {steps.map(({ n, title, icon, text }) => (
          <div key={n} className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-cyan/20 bg-cyan/[0.07] text-sm font-black text-cyan">
                {n}
              </div>
              <span className="text-2xl">{icon}</span>
            </div>
            <h3 className="text-lg font-black text-white">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ── Competitor comparison ── */
function ComparisonTable() {
  const features = [
    { label: "Smart contract scan",         us: true,  certik: true,  hashlock: true,  slither: true  },
    { label: "Website security scan",       us: true,  certik: false, hashlock: false, slither: false },
    { label: "dApp frontend review",        us: true,  certik: false, hashlock: false, slither: false },
    { label: "Wallet flow review",          us: true,  certik: false, hashlock: false, slither: false },
    { label: "Admin OpSec review",          us: true,  certik: false, hashlock: false, slither: false },
    { label: "53+ security rules",          us: true,  certik: true,  hashlock: false, slither: true  },
    { label: "Inline fix code per finding", us: true,  certik: false, hashlock: true,  slither: false },
    { label: "Hindi / Hinglish support",    us: true,  certik: false, hashlock: false, slither: false },
    { label: "INR pricing + UPI",           us: true,  certik: false, hashlock: false, slither: false },
    { label: "India VDA compliance hint",   us: true,  certik: false, hashlock: false, slither: false },
    { label: "Rug pull pattern detection",  us: true,  certik: false, hashlock: false, slither: false },
    { label: "Starting price",              us: "₹999", certik: "$15,000", hashlock: "Free", slither: "Free CLI" },
  ];

  const cols = [
    { key: "us",       label: "Web3Guard AI", highlight: true  },
    { key: "certik",   label: "CertiK",       highlight: false },
    { key: "hashlock", label: "Hashlock AI",  highlight: false },
    { key: "slither",  label: "Slither",      highlight: false },
  ];

  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="text-center mb-10">
        <p className="section-label">Why Web3Guard AI</p>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">
          More coverage. Fraction of the cost.
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-slate-400">
          CertiK charges $15,000+ for enterprise audits. Free tools are CLI-only. Web3Guard AI gives you professional-grade scanning in a self-serve platform — starting at ₹999.
        </p>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                <th className="p-4 text-left text-xs font-bold uppercase tracking-wider text-slate-500 w-48">Feature</th>
                {cols.map(({ key, label, highlight }) => (
                  <th key={key} className={`p-4 text-center text-sm font-black ${highlight ? "text-cyan" : "text-slate-400"}`}>
                    {highlight && <span className="mb-1 block text-xs font-medium text-cyan/70">YOU ARE HERE</span>}
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {features.map(({ label, ...vals }, i) => (
                <tr key={label} className={i % 2 === 0 ? "bg-white/[0.015]" : ""}>
                  <td className="p-3 pl-4 text-xs font-medium text-slate-300">{label}</td>
                  {cols.map(({ key, highlight }) => {
                    const v = (vals as Record<string,unknown>)[key];
                    return (
                      <td key={key} className={`p-3 text-center text-sm font-bold ${highlight ? "bg-cyan/[0.04]" : ""}`}>
                        {typeof v === "boolean" ? (
                          v ? <span className="text-green-400">✓</span> : <span className="text-slate-600">✕</span>
                        ) : (
                          <span className={highlight ? "text-cyan font-black" : "text-slate-400"}>{String(v)}</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <p className="mt-4 text-center text-xs text-slate-600">
        Comparison based on publicly available information. CertiK, Hashlock, and Slither are independent products.
      </p>
    </section>
  );
}

/* ── Social proof ── */
function SocialProof() {
  const items = [
    { icon: "🏆", title: "Hackathon-Ready",    text: "Used by ETHIndia builders for quick pre-submission security checks before demo day." },
    { icon: "🇮🇳", title: "India-First",       text: "First Web3 security scanner with Hindi explanations, INR pricing, and UPI payments." },
    { icon: "⚖️", title: "Legally Safe",       text: "Passive checks only. No exploit automation. No certified audit claims. Responsible use policy." },
    { icon: "🔓", title: "Transparent",         text: "Every rule has an ID, references, and confidence score. No black-box scores." },
  ];
  return (
    <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map(({ icon, title, text }) => (
          <div key={title} className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5 text-center">
            <div className="mb-3 text-3xl">{icon}</div>
            <h3 className="text-sm font-black text-white">{title}</h3>
            <p className="mt-2 text-xs leading-5 text-slate-400">{text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ── CTA banner ── */
function CtaBanner() {
  return (
    <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
      <div className="relative overflow-hidden rounded-3xl border border-cyan/20 p-8 text-center sm:p-12"
        style={{ background: "linear-gradient(135deg, rgba(34,211,238,0.08), rgba(96,165,250,0.08))" }}>
        <div className="absolute inset-0 opacity-10"
          style={{ backgroundImage: "radial-gradient(circle at 20% 50%, #22d3ee 0%, transparent 50%), radial-gradient(circle at 80% 50%, #60a5fa 0%, transparent 50%)" }} />
        <div className="relative">
          <p className="section-label">Ready to launch securely?</p>
          <h2 className="mt-3 text-3xl font-black text-white sm:text-4xl">
            Scan your project before launch. <span style={{ color: "#22d3ee" }}>It takes 5 minutes.</span>
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-sm leading-7 text-slate-400">
            Free scan covers smart contract, website, and dApp basics. Upgrade to paid review for expert manual analysis.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/scanner/unified-url" className="btn-primary" style={{ padding: "0.75rem 2rem", fontSize: "1rem" }}>
              Start Free Scan →
            </Link>
            <Link href="/sample-reports" className="btn-secondary" style={{ padding: "0.75rem 2rem" }}>
              View Sample Reports
            </Link>
          </div>
          <p className="mt-5 text-xs text-slate-500">No account needed · Free forever · Hindi support</p>
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
      <TrustBuilderSection />
      <SocialProof />
      <PricingSection />
      <CtaBanner />
    </>
  );
}
