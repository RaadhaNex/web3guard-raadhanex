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

function badge(status: string) {
  const s = status.toLowerCase();
  const cls = s.includes("live") ? "border-risk-green/40 bg-risk-green/10 text-green-200" : s.includes("deferred") || s.includes("not installed") || s.includes("needs") || s.includes("not assessed") || s.includes("not configured") || s.includes("manual") ? "border-risk-yellow/40 bg-risk-yellow/10 text-yellow-100" : "border-white/15 bg-white/10 text-slate-200";
  return <span className={`rounded-full border px-3 py-1 text-xs font-black ${cls}`}>{status}</span>;
}

export default function FeatureStatusPage() {
  return (
    <main className="min-h-screen bg-ink text-white">
      <TrustHero eyebrow="Real-only status matrix" title="What is live, pending, optional, or Not Assessed?" text={`${brand.product} by ${brand.company} must not show dummy trust. This page defines the public beta truth so users and admins know exactly what is real.`} />
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/[0.035] shadow-soft">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[860px] border-collapse text-left text-sm">
              <thead className="bg-white/[0.05] text-slate-300"><tr><th className="p-4">Feature</th><th className="p-4">Status</th><th className="p-4">Evidence / limitation</th></tr></thead>
              <tbody>{features.map(([feature, status, evidence]) => <tr key={feature} className="border-t border-white/10"><td className="p-4 font-black text-white">{feature}</td><td className="p-4">{badge(status)}</td><td className="p-4 text-slate-300">{evidence}</td></tr>)}</tbody>
            </table>
          </div>
        </div>
        <div className="mt-8 grid gap-4 lg:grid-cols-3">{integrationReadiness.map((item) => <div key={item.title} className="rounded-3xl border border-white/10 bg-black/25 p-5"><p className="font-black text-white">{item.title}</p><div className="mt-3">{badge(item.status)}</div><p className="mt-3 text-sm leading-6 text-slate-300">{item.evidence}</p></div>)}</div>
      </div>
    </main>
  );
}
