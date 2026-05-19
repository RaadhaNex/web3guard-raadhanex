import Link from "next/link";
import { integrationReadiness } from "@/lib/publicBetaContent";
import { TrustCard, TrustHero } from "@/components/ui/TrustPage";

const readyNow = [
  "Supabase Auth + protected dashboard architecture preserved from current working codebase.",
  "URL launch-surface scanner with project/history UX.",
  "Direct PDF/HTML/Markdown/JSON exports from current scan results.",
  "Solidity rule scanner with local fix hints and report realism disclaimers.",
  "Missing modules displayed as Not Assessed instead of fake-scored.",
  "Free launch/security generators available without payment or AI provider.",
];

const betaGate = [
  "Run two-user BOLA/IDOR check for project, scan, report, and export detail access.",
  "Confirm Vercel NEXT_PUBLIC_API_BASE_URL points to Render backend.",
  "Confirm Render FRONTEND_ORIGIN matches the deployed Vercel/custom domain.",
  "Confirm Supabase redirect URLs for login/signup/callback/dashboard.",
  "Confirm custom domain CSP/CORS after domain is attached.",
  "Confirm feature status page shows Needs API Key / Tool Not Installed for missing integrations.",
];

function ChecklistPanel({ title, items, tone }: { title: string; items: string[]; tone: "green" | "yellow" }) {
  return (
    <div className={`tool-console p-6 ${tone === "green" ? "border-emerald-400/20" : "border-amber-300/20"}`}>
      <div className="relative z-[1]">
        <p className={`text-xs font-black uppercase tracking-[0.22em] ${tone === "green" ? "text-emerald-300" : "text-amber-200"}`}>{title}</p>
        <div className="mt-5 space-y-3">
          {items.map((item, index) => (
            <div key={item} className="command-line">
              <span className="kbd-chip">{tone === "green" ? "✓" : String(index + 1).padStart(2, "0")}</span>
              <span className="text-sm text-slate-300">{item}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function LaunchReadinessPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <TrustHero eyebrow="Public beta readiness" title="A launch board for everything useful except payments." text="Public beta can ship real scanners, free tools, reports, and trust pages while UPI/Razorpay/subscriptions remain deferred until verified payment integration." />
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="mb-8 grid gap-4 md:grid-cols-4">
          {["Auth", "Scanner", "Exports", "Free tools"].map((item) => (
            <div key={item} className="stat-slab p-5 text-center">
              <p className="text-2xl font-black text-white">{item}</p>
              <p className="mt-2 text-xs font-black uppercase tracking-[0.2em] text-emerald-300">public beta ready</p>
            </div>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <ChecklistPanel title="Ready now" tone="green" items={readyNow} />
          <ChecklistPanel title="Verify before public beta" tone="yellow" items={betaGate} />
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          {integrationReadiness.map((item) => (
            <TrustCard key={item.title} title={item.title} tone={item.tone === "blocked" ? "red" : item.tone === "live" ? "green" : "yellow"}>
              <p className="font-black text-white">{item.status}</p>
              <p className="mt-2">{item.evidence}</p>
              <p className="mt-3 text-slate-400">Next: {item.nextStep}</p>
            </TrustCard>
          ))}
        </div>

        <div className="mt-10 flex flex-wrap gap-3">
          <Link href="/scanner/unified-url" className="btn-primary">Run URL scan</Link>
          <Link href="/free-tools" className="btn-secondary">Open free tools</Link>
          <Link href="/feature-status" className="btn-secondary">Feature status</Link>
        </div>
      </div>
    </main>
  );
}
