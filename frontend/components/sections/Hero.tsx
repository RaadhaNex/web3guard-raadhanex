import Link from "next/link";
import { brand } from "@/lib/constants";

const signals = [
  { label: "Critical", value: "Fix before launch", cls: "border-risk-red/30 bg-risk-red/10 text-red-200" },
  { label: "Warning", value: "Evidence needed", cls: "border-risk-yellow/30 bg-risk-yellow/10 text-yellow-100" },
  { label: "Pass", value: "Control present", cls: "border-risk-green/30 bg-risk-green/10 text-green-100" },
];

const matrix = [
  ["Website Surface", "82", "Headers + policy evidence"],
  ["Contract Rules", "Not Assessed", "Paste Solidity / verified source"],
  ["Launch Evidence", "43", "Wallet/Admin evidence needed"],
  ["Overall Confidence", "Partial", "Not a full audit score"],
];

export function Hero() {
  return (
    <section className="w3g-hero relative overflow-hidden border-b border-white/10">
      <div className="pointer-events-none absolute inset-0 w3g-cyber-grid" />
      <div className="pointer-events-none absolute left-1/2 top-[-12rem] h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-risk-red/10 blur-3xl" />
      <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-28">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/30 px-3.5 py-1.5 shadow-soft">
            <span className="h-2 w-2 rounded-full bg-risk-green shadow-[0_0_18px_rgba(34,197,94,.8)]" />
            <span className="text-xs font-black uppercase tracking-[0.18em] text-slate-200">Public beta · real-only security readiness</span>
          </div>
          <h1 className="max-w-4xl text-4xl font-black leading-tight tracking-tight text-white sm:text-6xl lg:text-[4.25rem]">
            Futuristic Web3 launch security,
            <span className="block bg-gradient-to-r from-white via-slate-300 to-risk-yellow bg-clip-text text-transparent">without fake audit claims.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-8 text-slate-300">
            Scan websites, Solidity, public repos, wallet UX evidence, and founder/admin OpSec readiness. Missing providers or tools show <strong className="text-white">Tool Not Installed</strong>, <strong className="text-white">Needs API Key</strong>, or <strong className="text-white">Not Assessed</strong>.
          </p>
          <div className="mt-7 flex flex-wrap gap-2">
            {["No private keys", "No wallet signing", "No exploit automation", "Payment deferred", "Pre-audit readiness only"].map((item) => <span key={item} className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-bold text-slate-300">{item}</span>)}
          </div>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link href="/scanner/unified-url" className="btn-primary">Start public beta scan →</Link>
            <Link href="/free-tools" className="btn-secondary">Open free tools</Link>
            <Link href="/methodology" className="btn-secondary">Methodology</Link>
          </div>
          <p className="mt-5 max-w-xl text-xs leading-5 text-slate-500">{brand.disclaimer} Payment/Razorpay/UPI stays pending until the final verified payment phase.</p>
        </div>

        <div className="w3g-orbit-card relative rounded-[2rem] border border-white/10 bg-[#07101f]/90 p-5 shadow-2xl">
          <div className="absolute inset-0 rounded-[2rem] bg-gradient-to-br from-risk-red/10 via-transparent to-risk-green/10" />
          <div className="relative">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div><p className="text-xs font-black uppercase tracking-[0.22em] text-risk-yellow">Launch confidence snapshot</p><p className="mt-1 text-sm text-slate-400">CertiK-style due diligence snapshot, Web3Guard wording</p></div>
              <span className="rounded-full border border-risk-yellow/30 bg-risk-yellow/10 px-3 py-1 text-xs font-black text-yellow-100">Partial</span>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {matrix.map(([label, value, note]) => (
                <div key={label} className="rounded-2xl border border-white/10 bg-black/30 p-4">
                  <p className="text-xs text-slate-400">{label}</p>
                  <p className={`mt-1 text-2xl font-black ${value === "Not Assessed" ? "text-risk-yellow" : value === "Partial" ? "text-slate-100" : "text-white"}`}>{value}</p>
                  <p className="mt-2 text-xs leading-5 text-slate-500">{note}</p>
                </div>
              ))}
            </div>
            <div className="mt-5 space-y-2">
              {signals.map((signal) => <div key={signal.label} className={`flex items-center justify-between rounded-2xl border px-4 py-3 text-sm ${signal.cls}`}><span className="font-black">{signal.label}</span><span>{signal.value}</span></div>)}
            </div>
            <div className="mt-5 rounded-2xl border border-white/10 bg-black/40 p-4">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-risk-green">Developer testing readiness</p>
              <p className="mt-2 text-sm leading-6 text-slate-300">Foundry · Echidna · Slither · Aderyn · Mythril status stays honest: real output only, otherwise Tool Not Installed / Worker Required.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
