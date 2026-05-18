import { brand } from "@/lib/constants";

const features = [
  ["Website passive scanner", "Live", "Real GET/HEAD passive checks only."],
  ["Unified URL launch map", "Live", "Missing modules are Not assessed, not fake-scored."],
  ["Direct report export", "Live", "PDF/HTML/Markdown/JSON export from scanner result and saved reports."],
  ["Smart contract scanner", "Live for pasted Solidity", "Rule engine only; no certified audit claim."],
  ["Scan history / projects", "Live", "User can reuse saved scans/projects where dashboard data exists."],
  ["BOLA/IDOR ownership", "Needs manual QA", "Two-user test must pass before storing sensitive data."],
  ["Supabase Auth + DB", "Configured if env present", "Auth/session/database status depends on Render/Vercel/Supabase env."],
  ["Supabase SMTP", "External setup pending", "Configure in Supabase dashboard for reliable email/password reset."],
  ["Custom domain + CSP", "External setup pending", "Update Supabase redirect URLs, Render origin, and CSP after domain is added."],
  ["UPI payment", "Deferred", "Pending until final payment phase. No frontend-only paid status."],
  ["Razorpay subscription", "Deferred", "Pending until test checkout + webhook + audit logs are verified."],
  ["AI explanations", "Optional / Needs API key", "Fallback local fix guidance works when AI is disabled."],
  ["GitHub repo scanner", "Optional / Needs token for best results", "No fake repo score when repo/API access is missing."],
  ["Explorer address scanner", "Optional / Needs API key", "No fake address score until Etherscan/BscScan integration."],
  ["Slither/Aderyn", "Tool Not Installed until worker ready", "Enable only when binaries are actually installed."],
  ["Monitoring / bug bounty / public badge", "Not live", "Do not show as active product features yet."],
];

function badge(status: string) {
  const s = status.toLowerCase();
  const cls = s.includes("live") ? "border-emerald-300 bg-emerald-50 text-emerald-800" : s.includes("pending") || s.includes("needs") || s.includes("deferred") || s.includes("optional") ? "border-amber-300 bg-amber-50 text-amber-800" : "border-slate-300 bg-slate-50 text-slate-700";
  return <span className={`rounded-full border px-3 py-1 text-xs font-bold ${cls}`}>{status}</span>;
}

export default function FeatureStatusPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-emerald-700">Real-only status matrix</p>
      <h1 className="mt-3 text-4xl font-black text-slate-950 sm:text-5xl">What is live, pending, or optional?</h1>
      <p className="mt-4 max-w-3xl text-slate-600">
        {brand.product} by {brand.company} must not show dummy trust. This page defines the current MVP truth so users and admins know exactly what is real.
      </p>
      <div className="mt-8 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full min-w-[760px] border-collapse text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr><th className="p-4">Feature</th><th className="p-4">Status</th><th className="p-4">Evidence / limitation</th></tr>
          </thead>
          <tbody>
            {features.map(([feature, status, evidence]) => (
              <tr key={feature} className="border-t border-slate-100">
                <td className="p-4 font-bold text-slate-950">{feature}</td>
                <td className="p-4">{badge(status)}</td>
                <td className="p-4 text-slate-600">{evidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-8 rounded-3xl border border-red-200 bg-red-50 p-6 text-red-900">
        <h2 className="text-xl font-black">Blocked wording</h2>
        <p className="mt-2 text-sm leading-6">Do not use: certified audit, 100% secure, AI verified, payment successful, subscription active, monitoring enabled, public verified badge — unless the matching real system is implemented and verified.</p>
      </div>
    </div>
  );
}
