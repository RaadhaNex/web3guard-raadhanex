import Link from "next/link";
import { StatusPill } from "@/components/ui/StatusPill";

const deploySteps = [
  ["Backend on Render", ["Create Python 3.12 web service", "Build: pip install -r requirements.txt", "Start: uvicorn main:app --host 0.0.0.0 --port $PORT", "Set FRONTEND_URL, ADMIN_TOKEN, RAADHANEX_UPI_ID"]],
  ["Frontend on Vercel", ["Import frontend folder", "Set NEXT_PUBLIC_API_BASE_URL", "Set NEXT_PUBLIC_UPI_ID and NEXT_PUBLIC_UPI_NAME", "Run production build", "Open /local-qa after deploy"]],
  ["Manual launch checks", ["/health/readiness passes", "Run real unified URL scan", "Create payment intent", "Submit lead", "Verify admin leads and CSV export"]],
];

const salesPlan = [
  ["Days 1-3", "Build target list", "Find 50 early-stage Web3 launches from hackathons, Twitter/X, Discord, Telegram, GitHub."],
  ["Days 4-10", "Get first paid reports", "Offer free real scan preview, then pitch ₹999/₹2,999 only when findings exist."],
  ["Days 11-30", "Repeatable service funnel", "Convert repeat users into Builder monthly subscription and publish Hinglish security education."],
];

export default function LaunchPackPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <div className="max-w-4xl">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">• Deploy + launch pack</p>
        <h1 className="mt-3 text-4xl font-black sm:text-5xl">Launch Web3Guard AI without fake promises.</h1>
        <p className="mt-4 text-slate-400">
          This page is the operating checklist for local QA, Render/Vercel deployment, UPI manual payment flow, and the first 30-day outreach plan. Use it before public testing.
        </p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Link href="/local-qa" className="btn-primary">Run Local QA</Link>
          <Link href="/scanner/unified-url" className="btn-secondary">Test URL Scanner</Link>
        </div>
      </div>

      <section className="mt-10 grid gap-5 lg:grid-cols-3">
        {[
          ["Live", "Contract, website, checklist scanners, report builder, lead capture, UPI intents."],
          ["Manual", "UPI settlement verification, manual pre-audit delivery, report review."],
          ["Not enabled", "Razorpay webhook, GitHub, Etherscan, Slither, monitoring, certified audit claims."],
        ].map(([status, detail]) => (
          <div key={status} className="card p-6">
            <StatusPill status={status} />
            <p className="mt-4 text-sm leading-6 text-slate-400">{detail}</p>
          </div>
        ))}
      </section>

      <section className="mt-10 grid gap-6 lg:grid-cols-3">
        {deploySteps.map(([title, steps]) => (
          <div key={title as string} className="card p-6">
            <h2 className="text-xl font-black text-white">{title}</h2>
            <ol className="mt-4 space-y-3 text-sm text-slate-300">
              {(steps as string[]).map((step, index) => <li key={step}><span className="text-cyan">{index + 1}.</span> {step}</li>)}
            </ol>
          </div>
        ))}
      </section>

      <section className="mt-10 card p-6 sm:p-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">30-day sales playbook</p>
            <h2 className="mt-3 text-3xl font-black">Income-focused but honest.</h2>
          </div>
          <Link href="/pricing" className="btn-secondary">View Packages</Link>
        </div>
        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          {salesPlan.map(([days, goal, detail]) => (
            <div key={days} className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
              <p className="text-sm font-black text-cyan">{days}</p>
              <h3 className="mt-2 text-xl font-black text-white">{goal}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-400">{detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-10 rounded-3xl border border-amber-300/20 bg-amber-300/10 p-6 text-sm leading-6 text-amber-50">
        <strong>Required public wording:</strong> “AI-assisted preliminary Web3 launch security review.” Do not use “certified audit,” “100% secure,” or “payment successful” until real verification exists.
      </section>
    </div>
  );
}
