import Link from "next/link";
import { StatusPill } from "@/components/ui/StatusPill";

const rows = [
  ["Scanner + Dashboard", "Live", "Real scan flow with auth, progress indicators, saved scans, and readable results."],
  ["Razorpay Payments", "Needs API Key", "Order creation, signature verification, and UPI fallback are ready — keys required to activate."],
  ["Supabase Auth", "Manual", "Auth is wired. Add your production domain and redirect URLs in Supabase settings."],
  ["AI Provider (OpenAI / Claude)", "Needs API Key", "Rule-based guidance works without a key. Real AI explanations activate after backend key is set."],
  ["Slither / Aderyn / Mythril", "Manual", "Tools run only from installed binaries. Missing tools show 'Not Installed' — never fake results."],
  ["Etherscan + GitHub", "Needs API Key", "Etherscan requires a backend key. GitHub scans public repos without a token."],
];

export function ProductionReadiness() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">

        <div className="card p-6 sm:p-8">
          <p className="section-label">Integration status</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">
            Platform is live. External keys activate advanced features.
          </h2>
          <p className="mt-4 text-sm leading-7 text-slate-400">
            Scanners, auth, reports, and hardening tools are live. Payments, AI, and static analysis tools activate once you add the respective API keys.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/feature-status" className="btn-primary">Feature Status</Link>
            <Link href="/contact" className="btn-secondary">Get Help</Link>
          </div>
        </div>

        <div className="space-y-3">
          {rows.map(([name, status, detail]) => (
            <div key={name} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="text-sm font-bold text-white">{name}</h3>
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
