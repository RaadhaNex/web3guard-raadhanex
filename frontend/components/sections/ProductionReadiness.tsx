import Link from "next/link";
import { StatusPill } from "@/components/ui/StatusPill";

const rows = [
  [
    "Login-gated scanner + dashboard",
    "Live",
    "Scanner flow requires auth, shows progress/readable API errors, and can save scans/reports for authenticated dashboard users.",
  ],
  [
    "Razorpay Checkout + webhook",
    "Needs API Key",
    "Backend supports real order creation, checkout signature verification, webhook verification, idempotency, and UPI manual fallback. Keys + webhook URL must be configured externally.",
  ],
  [
    "Supabase Auth + SMTP",
    "Manual",
    "Auth is wired. Final branded SMTP, Site URL, and Redirect URLs are completed inside Supabase settings for the production/custom domain.",
  ],
  [
    "OpenAI / Claude AI provider",
    "Needs API Key",
    "Local safe guidance remains available. Real provider output starts only after backend keys and AI privacy/code-send flags are configured.",
  ],
  [
    "Slither / Aderyn / Mythril tools",
    "Manual",
    "Static/deep tools run only from real installed binaries or an isolated worker. Missing tools show Tool Not Installed / Provider Not Configured instead of fake findings.",
  ],
  [
    "Etherscan + GitHub optional providers",
    "Needs API Key",
    "Etherscan requires a backend key for verified-source scans. GitHub can scan public repos without a token, but a backend token improves public API limits.",
  ],
];

export function ProductionReadiness() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card p-6 sm:p-8">
          <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Final real-only launch posture</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">Code is live-ready. External providers still need real verification.</h2>
          <p className="mt-4 text-sm leading-6 text-slate-400">
            The scanner, auth gates, saved reports, and hardening UI are code-wired. Final launch depends on external provider setup: Razorpay webhook, Supabase SMTP/domain redirects, AI provider key, Etherscan key, and optional tool workers.
          </p>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <Link href="/final-qa" className="btn-primary">Open Final QA</Link>
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
