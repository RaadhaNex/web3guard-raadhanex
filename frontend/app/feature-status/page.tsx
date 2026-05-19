import { integrationReadiness } from "@/lib/publicBetaContent";
import { TrustHero } from "@/components/ui/TrustPage";
import { brand } from "@/lib/constants";

const features = [
  ["Website passive scanner", "Live", "Real GET/HEAD passive checks only."],
  ["Unified URL launch map", "Live", "Missing modules are Not Assessed, not fake-scored."],
  ["Direct report export", "Live", "PDF/HTML/Markdown/JSON export from scanner result and saved reports."],
  ["Smart contract scanner", "Live for pasted Solidity", "Rule engine only; no certified audit claim."],
  ["Score split", "Live", "Website Surface Score, Contract Rule Score, Launch Evidence Score, Overall Launch Confidence."],
  ["Free value tools", "Live", "Checklist/security.txt/CI/pre-audit/bug-bounty templates generated locally in frontend."],
  ["Scan history / projects", "Live where Supabase/local storage is configured", "Dashboard data depends on auth/storage env and ownership checks."],
  ["Supabase Auth + DB", "Configured if env present", "Auth/session/database status depends on Render/Vercel/Supabase env."],
  ["UPI payment", "Deferred", "Pending until final payment phase. No frontend-only paid status."],
  ["Razorpay subscription", "Deferred", "Pending until test checkout + webhook + audit logs are verified."],
  ["AI explanations", "Provider Not Configured / Needs API Key", "Fallback local fix guidance works when AI is disabled."],
  ["Etherscan address scanner", "Needs API Key unless configured", "No fake address/source score when API key/source verification is missing."],
  ["GitHub repo scanner", "Live for public repos; token optional", "No cloning, dependency install, execution, or private repo scan without authorization."],
  ["Slither/Aderyn/Semgrep", "Tool Not Installed until worker ready", "Runs real subprocess output only when installed/enabled."],
  ["Mythril/Manticore/Echidna", "Worker required / Not Assessed by default", "No fake symbolic/fuzz output."],
  ["GoPlus token/wallet risk", "Provider Not Configured unless env enabled", "Read-only checks only; no wallet connect/signing/private keys."],
  ["Monitoring / public badges / bounty automation", "Manual / Not Assessed", "Do not show live badges/automation until verified."],
];

function statusClass(status: string) {
  const s = status.toLowerCase();
  if (s.includes("live")) return "status-node-live border-emerald-400/25 bg-emerald-500/10 text-emerald-100";
  if (s.includes("deferred") || s.includes("not installed") || s.includes("needs") || s.includes("not assessed") || s.includes("not configured") || s.includes("manual")) return "status-node-warn border-amber-300/25 bg-amber-300/10 text-amber-100";
  return "border-white/10 bg-white/[0.03] text-slate-200";
}

function badge(status: string) {
  return <span className={`rounded-full border px-3 py-1 text-xs font-black ${statusClass(status)}`}>{status}</span>;
}

export default function FeatureStatusPage() {
  const liveCount = features.filter(([, status]) => status.toLowerCase().includes("live")).length;
  const deferredCount = features.filter(([, status]) => status.toLowerCase().includes("deferred")).length;
  const gatedCount = features.length - liveCount - deferredCount;

  return (
    <main className="min-h-screen bg-ink text-white">
      <TrustHero eyebrow="Real-only status matrix" title="A transparent command board for every integration." text={`${brand.product} by ${brand.company} shows what is live, deferred, gated by API key, worker-required, or Not Assessed. No dummy trust badges.`} />
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="mb-8 grid gap-4 md:grid-cols-3">
          <div className="stat-slab p-5"><p className="text-3xl font-black text-white">{liveCount}</p><p className="mt-1 text-xs font-black uppercase tracking-[0.2em] text-emerald-300">live / usable</p></div>
          <div className="stat-slab p-5"><p className="text-3xl font-black text-white">{gatedCount}</p><p className="mt-1 text-xs font-black uppercase tracking-[0.2em] text-amber-200">gated / manual</p></div>
          <div className="stat-slab p-5"><p className="text-3xl font-black text-white">{deferredCount}</p><p className="mt-1 text-xs font-black uppercase tracking-[0.2em] text-slate-400">deferred</p></div>
        </div>

        <div className="tool-console overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[880px] border-collapse text-left text-sm">
              <thead className="bg-white/[0.04] text-slate-300">
                <tr><th className="p-4">Feature</th><th className="p-4">Status</th><th className="p-4">Evidence / limitation</th></tr>
              </thead>
              <tbody>
                {features.map(([feature, status, evidence]) => (
                  <tr key={feature} className="border-t border-white/10">
                    <td className="p-4 font-black text-white">{feature}</td>
                    <td className="p-4">{badge(status)}</td>
                    <td className="p-4 text-slate-300">{evidence}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          {integrationReadiness.map((item) => (
            <div key={item.title} className={`status-node p-5 ${item.tone === "live" ? "status-node-live" : item.tone === "blocked" ? "status-node-blocked" : "status-node-warn"}`}>
              <p className="font-black text-white">{item.title}</p>
              <div className="mt-3">{badge(item.status)}</div>
              <p className="mt-3 text-sm leading-6 text-slate-300">{item.evidence}</p>
              <p className="mt-3 text-xs leading-5 text-slate-500">Next: {item.nextStep}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
