import Link from "next/link";

const readyNow = [
  "Login-required scanner flow",
  "URL launch-surface scanner",
  "Project/history UX on scanner page",
  "Direct PDF/HTML/Markdown/JSON export",
  "Solidity rule scanner with local fix hints",
  "Missing modules shown as Not assessed",
  "No private key / seed phrase / wallet signing collection",
];

const mustVerify = [
  "Two-user BOLA/IDOR test: User B must not access User A scan/report/export",
  "Report export final QA after each scanner update",
  "Supabase Auth URL + Redirect URL check",
  "Supabase SMTP setup for production email reliability",
  "Custom domain + CSP/CORS update after domain setup",
  "Provider status page must show Tool Not Installed / Needs API Key when missing",
];

const later = [
  "UPI QR + UTR manual verification system",
  "Razorpay test/live checkout and webhook verification",
  "Slither/Aderyn isolated worker",
  "Etherscan/GitHub optional API keys",
  "OpenAI/Claude AI explanation provider",
  "Monitoring, public badges, bug bounty automation",
];

function Section({ title, tone, items }: { title: string; tone: "green" | "yellow" | "slate"; items: string[] }) {
  const styles = {
    green: "border-emerald-200 bg-emerald-50 text-emerald-950",
    yellow: "border-amber-200 bg-amber-50 text-amber-950",
    slate: "border-slate-200 bg-white text-slate-950",
  }[tone];

  return (
    <div className={`rounded-3xl border p-6 shadow-sm ${styles}`}>
      <h2 className="text-2xl font-black">{title}</h2>
      <ul className="mt-5 space-y-3">
        {items.map((item) => (
          <li key={item} className="flex gap-3 text-sm leading-6">
            <span className="mt-1 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-white/80 text-xs font-black">✓</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function LaunchReadinessPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-slate-500">Non-payment launch readiness</p>
      <h1 className="mt-3 text-4xl font-black text-slate-950 sm:text-5xl">Finish everything except payments first.</h1>
      <p className="mt-4 max-w-3xl text-slate-600">
        This checklist keeps Web3Guard AI launch-safe while UPI/Razorpay stays intentionally pending for the final payment phase.
      </p>

      <div className="mt-8 grid gap-5 lg:grid-cols-3">
        <Section title="Ready now" tone="green" items={readyNow} />
        <Section title="Verify before beta" tone="yellow" items={mustVerify} />
        <Section title="Final/later phases" tone="slate" items={later} />
      </div>

      <div className="mt-8 rounded-3xl border border-red-200 bg-red-50 p-6 text-red-900">
        <h2 className="text-xl font-black">Important: payment is intentionally pending</h2>
        <p className="mt-2 text-sm leading-6">
          Until the payment phase is complete, do not show Paid, Subscription active, Premium unlocked, or Payment successful. Paid plans are request-only.
        </p>
      </div>

      <div className="mt-8 flex flex-wrap gap-3">
        <Link href="/scanner/unified-url" className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-black text-white hover:bg-slate-800">Run URL scan</Link>
        <Link href="/feature-status" className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-800 hover:bg-slate-50">Feature status</Link>
        <Link href="/billing" className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-800 hover:bg-slate-50">Billing pending</Link>
      </div>
    </div>
  );
}
