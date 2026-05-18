import Link from "next/link";
import { brand } from "@/lib/constants";

const topFindings = [
  { sev: "critical", rule: "WG-SOL-OVFL-001", text: "Integer overflow — pre-0.8.0" },
  { sev: "critical", rule: "WG-SOL-ARBTRF",   text: "Arbitrary transferFrom vector" },
  { sev: "high",     rule: "WG-SOL-REENT-003", text: "Cross-function reentrancy" },
  { sev: "high",     rule: "WG-SOL-GOV-001",  text: "Governance flash loan risk" },
  { sev: "medium",   rule: "WG-SOL-PRICE-001", text: "Spot price manipulation" },
];

const sevCls: Record<string, string> = {
  critical: "sev-critical", high: "sev-high", medium: "sev-medium",
};

export function Hero() {
  return (
    <section className="grid-bg relative overflow-hidden border-b border-white/[0.07]">
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div style={{ position: "absolute", top: -100, left: -100, width: 600, height: 600, borderRadius: "50%", background: "radial-gradient(circle, rgba(34,211,238,0.07) 0%, transparent 70%)" }} />
        <div style={{ position: "absolute", top: -50, right: -100, width: 500, height: 500, borderRadius: "50%", background: "radial-gradient(circle, rgba(96,165,250,0.05) 0%, transparent 70%)" }} />
      </div>

      <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8 lg:py-28">

        {/* Left */}
        <div>
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan/20 bg-cyan/[0.06] px-3.5 py-1.5">
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22d3ee", display: "inline-block", flexShrink: 0, boxShadow: "0 0 6px #22d3ee" }} />
            <span className="text-xs font-semibold text-cyan">India&apos;s first full-surface Web3 security platform</span>
          </div>

          <h1 className="max-w-2xl text-4xl font-black leading-tight tracking-tight text-white sm:text-5xl lg:text-[3.4rem]">
            Find security risks in your
            <span style={{ background: "linear-gradient(135deg,#22d3ee 0%,#60a5fa 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", display: "block" }}>
              Web3 project before launch.
            </span>
          </h1>

          <p className="mt-5 max-w-lg text-base leading-7 text-slate-400">
            Smart contract scanner with <strong className="text-white font-semibold">53 security rules</strong>, website scanner, dApp review, wallet flow check, and admin OpSec audit — all in one platform. Hindi support. From ₹999.
          </p>

          {/* Trust signals */}
          <div className="mt-6 flex flex-wrap gap-2">
            {["53 rules", "6 surfaces", "Inline fix code", "Hindi support", "Pre-audit only"].map(t => (
              <span key={t} className="rounded-full border border-white/[0.08] bg-white/[0.03] px-3 py-1 text-xs font-medium text-slate-300">
                {t}
              </span>
            ))}
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/scanner/unified-url" className="btn-primary" style={{ padding: "0.75rem 1.75rem", fontSize: "0.9375rem" }}>
              Start Free Scan
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}><path d="M2 7.5h11M8.5 3l4.5 4.5L8.5 12"/></svg>
            </Link>
            <Link href="/sample-reports" className="btn-secondary" style={{ padding: "0.75rem 1.75rem", fontSize: "0.9375rem" }}>
              View Sample Report
            </Link>
          </div>

          <p className="mt-5 text-xs text-slate-500">{brand.disclaimer}</p>
        </div>

        {/* Right — Scanner output preview */}
        <div className="card overflow-hidden border-cyan/[0.15]">
          {/* Scanner header */}
          <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-3">
            <div className="flex items-center gap-2">
              <div className="flex gap-1.5">
                <span style={{ width: 9, height: 9, borderRadius: "50%", background: "#ff5f57", display: "block" }} />
                <span style={{ width: 9, height: 9, borderRadius: "50%", background: "#febc2e", display: "block" }} />
                <span style={{ width: 9, height: 9, borderRadius: "50%", background: "#28c840", display: "block" }} />
              </div>
              <span className="mono text-xs text-slate-500">Web3Guard AI — Scan Results</span>
            </div>
            <span className="rounded-full bg-red-500/10 px-2.5 py-1 text-xs font-bold text-red-400">Score: 12 · Critical Risk</span>
          </div>

          {/* Score ring + breakdown */}
          <div className="flex items-center gap-5 border-b border-white/[0.07] px-5 py-4">
            {/* Mini ring */}
            <div style={{ position: "relative", width: 72, height: 72, flexShrink: 0 }}>
              <svg width="72" height="72" viewBox="0 0 72 72">
                <circle cx="36" cy="36" r="28" fill="none" stroke="rgba(148,163,184,0.12)" strokeWidth="7" />
                <circle cx="36" cy="36" r="28" fill="none" stroke="#ef4444" strokeWidth="7"
                  strokeLinecap="round"
                  strokeDasharray={`${(12/100)*175.9} 175.9`}
                  transform="rotate(-90 36 36)" />
              </svg>
              <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                <span style={{ fontSize: "1.25rem", fontWeight: 900, color: "#ef4444", lineHeight: 1 }}>12</span>
                <span style={{ fontSize: "0.55rem", color: "#64748b" }}>/100</span>
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold text-red-400">Critical Launch Risk</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                <span className="sev-critical">3 Critical</span>
                <span className="sev-high">2 High</span>
                <span className="sev-medium">1 Medium</span>
              </div>
              <p className="mt-1.5 text-xs text-slate-500">Contract · Website · Admin</p>
            </div>
          </div>

          {/* Findings list */}
          <div className="divide-y divide-white/[0.05] px-1 pb-1">
            {topFindings.map(({ sev, rule, text }) => (
              <div key={rule} className="flex items-center gap-3 px-4 py-2.5">
                <span className={sevCls[sev] ?? "sev-info"}>{sev}</span>
                <span className="mono text-xs text-slate-500 shrink-0">{rule}</span>
                <span className="text-xs text-slate-300 truncate">{text}</span>
                <span className="ml-auto shrink-0 rounded bg-green-500/10 px-1.5 py-0.5 text-xs text-green-400">Fix ↗</span>
              </div>
            ))}
          </div>

          <div className="border-t border-white/[0.07] px-5 py-3 text-center">
            <p className="text-xs text-slate-500">Sample output — real scans use your code</p>
          </div>
        </div>
      </div>
    </section>
  );
}
