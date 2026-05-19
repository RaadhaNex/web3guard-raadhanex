import Link from "next/link";
import { Hero } from "@/components/sections/Hero";
import { LaunchSurface } from "@/components/sections/LaunchSurface";
import { PricingSection } from "@/components/sections/PricingSection";
import { TrustStrip } from "@/components/sections/TrustStrip";
import { TrustBuilderSection } from "@/components/sections/TrustBuilderSection";
import { SampleScannerDemo } from "@/components/sections/SampleScannerDemo";

function StatsBar() {
  const stats = [
    { value: "53+", label: "Local rule hints" },
    { value: "7", label: "Launch surfaces" },
    { value: "Free", label: "Beta tools" },
    { value: "0", label: "Fake provider results" },
  ];
  return <div className="border-b border-white/10 bg-black/20"><div className="mx-auto flex max-w-7xl flex-wrap items-center justify-around gap-4 px-4 py-5 sm:px-6 lg:px-8">{stats.map(({ value, label }) => <div key={label} className="text-center"><p className="text-2xl font-black text-white">{value}</p><p className="mt-0.5 text-xs font-medium text-slate-400">{label}</p></div>)}</div></div>;
}

function HowItWorks() {
  const steps = [
    { n: "01", title: "Input real evidence", text: "Enter an authorized URL and optional Solidity, API URL, contract address, or public GitHub repo." },
    { n: "02", title: "Review split scores", text: "Website Surface, Contract Rule, Launch Evidence, and Overall Launch Confidence stay separate." },
    { n: "03", title: "Export and fix", text: "Download PDF/HTML/Markdown/JSON and use fix hints/checklists before manual audit or public beta." },
  ];
  return <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8"><div className="mb-10 text-center"><p className="section-label">How it works</p><h2 className="mt-3 text-3xl font-black text-white sm:text-4xl">Launch-readiness workflow without overclaiming.</h2></div><div className="grid gap-4 sm:grid-cols-3">{steps.map(({ n, title, text }) => <div key={n} className="rounded-2xl border border-white/10 bg-white/[0.03] p-6"><div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl border border-risk-yellow/20 bg-risk-yellow/10 text-sm font-black text-yellow-100">{n}</div><h3 className="text-lg font-black text-white">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-400">{text}</p></div>)}</div></section>;
}

function InspiredCoverage() {
  const items = [
    ["Launch confidence snapshot", "Due-diligence style readiness summary, but never a certified audit score."],
    ["Secure pattern guidance", "OpenZeppelin-style safe deployment checklist and fix direction."],
    ["Full launch surface", "Website, dApp, API, wallet, admin OpSec, GitHub, and contract evidence map."],
    ["Wallet/token risk readiness", "GoPlus-style provider status without fake data when provider is disabled."],
    ["Bounty readiness", "Immunefi/Sherlock-style scope, triage, safe harbor, and post-launch protection checklist."],
    ["Contest/pre-audit pack", "Code4rena-style package prep: scope, commit hash, invariants, known risks, tests."],
    ["Developer testing", "Foundry/Echidna/Slither/Aderyn/Mythril readiness templates/status."],
  ];
  return <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8"><div className="mb-8"><p className="section-label">Competitor-inspired equivalents</p><h2 className="mt-3 text-3xl font-black text-white sm:text-4xl">Best ideas, Web3Guard real-only implementation.</h2><p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">Inspired by industry workflows, not branding copies. Every module shows real status: Live, Manual, Needs API Key, Tool Not Installed, Provider Not Configured, or Not Assessed.</p></div><div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">{items.map(([title, text]) => <div key={title} className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"><h3 className="font-black text-white">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-400">{text}</p></div>)}</div></section>;
}

function CtaBanner() {
  return <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8"><div className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-risk-red/10 via-white/[0.03] to-risk-green/10 p-8 text-center sm:p-12"><p className="section-label">Ready for public beta?</p><h2 className="mt-3 text-3xl font-black text-white sm:text-4xl">Scan now. Fix evidence gaps. Keep payment pending until verified.</h2><p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-400">Free scan and free tools are available now. Paid review remains request-only until UPI/Razorpay order, checkout, webhook, and audit trail are implemented.</p><div className="mt-8 flex flex-wrap justify-center gap-3"><Link href="/scanner/unified-url" className="btn-primary">Start scan</Link><Link href="/free-tools" className="btn-secondary">Use free tools</Link></div></div></section>;
}

export default function HomePage() {
  return <><Hero /><StatsBar /><TrustStrip /><LaunchSurface /><HowItWorks /><SampleScannerDemo /><InspiredCoverage /><TrustBuilderSection /><PricingSection /><CtaBanner /></>;
}
