import Link from "next/link";
import { StatusPill } from "@/components/ui/StatusPill";

const rows = [
  ["Unified URL launch scan", "Live", "Real website passive scan + optional Solidity/API inputs; missing modules remain Not assessed."],
  ["UPI package funnel", "Manual", "UPI deep link works, but admin must verify settlement before delivery."],
  ["AI explanations", "Needs API key", "Fallback explanations are local; real AI is backend-only and opt-in."],
  ["Razorpay subscription", "Not enabled", "No fake payment success; scheduled for real payment phase."],
  ["GitHub / Explorer / Slither", "Not enabled", "No fake score; will be added as real integrations in later MVP phases."],
];

export function ProductionReadiness() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card p-6 sm:p-8">
          <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Real-only production posture</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">No fake audit claims. No fake payment success.</h2>
          <p className="mt-4 text-sm leading-6 text-slate-400">
            Phase 6.2 makes the MVP more launchable by polishing the UI, exposing real feature status, and adding a deployment launch pack. Every module is labeled as live, manual, needs API key, or not enabled.
          </p>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <Link href="/launch-pack" className="btn-primary">Open Launch Pack</Link>
            <Link href="/feature-status" className="btn-secondary">Feature Status</Link>
          </div>
        </div>
        <div className="space-y-3">
          {rows.map(([name, status, detail]) => (
            <div key={name} className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="font-black text-white">{name}</h3>
                <StatusPill status={status} />
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-400">{detail}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
