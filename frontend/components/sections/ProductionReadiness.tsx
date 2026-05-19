import Link from "next/link";
import { StatusPill } from "@/components/ui/StatusPill";

const rows = [
  ["Scanner + Dashboard", "Live", "Real scan flow with auth, progress indicators, saved scans, and direct exports."],
  ["Razorpay / UPI", "Manual", "Payment collection remains deferred. No fake success, subscription, or checkout state is shown."],
  ["Supabase Auth", "Manual", "Auth is wired. Production redirects and domain allow-list must be checked in Supabase settings."],
  ["AI Provider", "Needs API Key", "Rule-based guidance works without a provider. Real AI output activates only after backend key setup."],
  ["Slither / Aderyn / Mythril", "Tool Not Installed", "Only real installed tools or workers produce output. Otherwise modules stay Not Assessed."],
  ["Etherscan + GoPlus", "Needs API Key", "Readiness is visible. Provider results are not fabricated when keys are missing."],
];

export function ProductionReadiness() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card p-6 sm:p-8">
          <p className="section-label">Integration readiness</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">Live where verified. Clear where external setup is needed.</h2>
          <p className="mt-4 text-sm leading-7 text-slate-400">
            Web3Guard keeps public beta safe by separating live modules, manual checks, provider-key requirements, and not-assessed surfaces.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/feature-status" className="btn-primary">Feature Status</Link>
            <Link href="/launch-readiness" className="btn-secondary">Launch Readiness</Link>
          </div>
        </div>

        <div className="space-y-3">
          {rows.map(([name, status, detail]) => (
            <div key={name} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 transition hover:border-cyan/20 hover:bg-white/[0.045]">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="text-sm font-black text-white">{name}</h3>
                <StatusPill status={status} />
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-400">{detail}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
