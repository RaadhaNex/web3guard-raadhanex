import { brand } from "@/lib/constants";

const features = [
  ["Website passive scanner", "Live", "Real GET/HEAD passive checks only."],
  ["Unified URL launch map", "Live", "Missing modules are Not assessed, not fake-scored."],
  ["Smart contract scanner", "Live for pasted Solidity", "Rule engine only; no certified audit claim."],
  ["UPI payment", "Manual", "Real UPI deeplink; admin verifies payment reference."],
  ["Razorpay subscription", "Not live", "No auto subscription until checkout + webhook."],
  ["AI explanations", "Needs API key", "Fallback local mode when AI disabled."],
  ["GitHub repo scanner", "Not live", "No fake repo score."],
  ["Explorer address scanner", "Not live", "No fake address score until Etherscan/BscScan integration."],
  ["Monitoring / bug bounty / public badge", "Not live", "Do not show as active product features yet."],
];

function badge(status: string) {
  const s = status.toLowerCase();
  const cls = s.includes("live") ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-100" : s.includes("manual") || s.includes("needs") ? "border-amber-400/30 bg-amber-500/10 text-amber-100" : "border-slate-400/30 bg-slate-500/10 text-slate-200";
  return <span className={`rounded-full border px-3 py-1 text-xs font-bold ${cls}`}>{status}</span>;
}

export default function FeatureStatusPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Real-only status matrix</p>
      <h1 className="mt-3 text-4xl font-black sm:text-5xl">What is live, manual, or not live?</h1>
      <p className="mt-4 max-w-3xl text-slate-400">
        {brand.product} by {brand.company} must not show dummy trust. This page defines the current MVP truth so users and admins know exactly what is real.
      </p>
      <div className="mt-8 overflow-hidden rounded-3xl border border-white/10">
        <table className="w-full min-w-[760px] border-collapse text-left text-sm">
          <thead className="bg-white/[0.05] text-slate-300">
            <tr><th className="p-4">Feature</th><th className="p-4">Status</th><th className="p-4">Evidence / limitation</th></tr>
          </thead>
          <tbody>
            {features.map(([feature, status, evidence]) => (
              <tr key={feature} className="border-t border-white/10">
                <td className="p-4 font-bold text-white">{feature}</td>
                <td className="p-4">{badge(status)}</td>
                <td className="p-4 text-slate-300">{evidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-8 rounded-3xl border border-amber-300/20 bg-amber-300/10 p-6 text-amber-50">
        <h2 className="text-xl font-black">Blocked wording</h2>
        <p className="mt-2 text-sm">Do not use: certified audit, 100% secure, AI verified, payment successful, subscription active, monitoring enabled, public verified badge — unless the matching real system is implemented and verified.</p>
      </div>
    </div>
  );
}
