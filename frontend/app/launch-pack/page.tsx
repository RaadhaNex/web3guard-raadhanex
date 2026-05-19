import Link from "next/link";
import { StatusPill } from "@/components/ui/StatusPill";

const deploySteps = [
  ["Backend on Render", ["Create Python web service", "Build with requirements.txt", "Start FastAPI with uvicorn", "Set only required non-secret runtime config"]],
  ["Frontend on Vercel", ["Import frontend folder", "Set NEXT_PUBLIC_API_BASE_URL", "Run production build", "Verify /feature-status and /local-qa after deploy"]],
  ["Public beta checks", ["/health/readiness passes", "Run real unified URL scan", "Verify direct exports", "Confirm no payment or audit claim is shown as live"]],
];

const launchPlan = [
  ["Days 1-3", "Private beta review", "Test with your own projects, sample reports, and known public URLs you are authorized to review."],
  ["Days 4-10", "Founder feedback", "Collect usability feedback, confusing copy, missing evidence cases, and mobile layout issues."],
  ["Days 11-30", "Public beta iteration", "Improve checklists, report clarity, and onboarding before enabling paid workflows."],
];

export default function LaunchPackPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <div className="quantum-stage p-6 sm:p-8">
        <div className="max-w-4xl">
          <p className="section-label">Deploy + launch pack</p>
          <h1 className="mt-3 text-4xl font-black sm:text-5xl">Launch Web3Guard AI without fake promises.</h1>
          <p className="mt-4 text-sm leading-7 text-slate-400 sm:text-base">
            Use this as the public beta operating checklist for local QA, Render/Vercel deployment, scanner verification, report exports, and safe public wording.
          </p>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <Link href="/local-qa" className="btn-primary">Run stability console</Link>
            <Link href="/scanner/unified-url" className="btn-secondary">Test URL scanner</Link>
          </div>
        </div>
      </div>

      <section className="mt-10 grid gap-5 lg:grid-cols-3">
        {[
          ["Live", "Contract, website, checklist scanners, report builder, lead capture, and direct report exports."],
          ["Manual", "Scope review, founder feedback, public copy review, and pre-audit package preparation."],
          ["Not enabled", "Payment activation, provider-only badges, external worker claims, certified audit claims, and fake verification."],
        ].map(([status, detail]) => (
          <div key={status} className="glass-tile p-6">
            <StatusPill status={status} />
            <p className="mt-4 text-sm leading-6 text-slate-400">{detail}</p>
          </div>
        ))}
      </section>

      <section className="mt-10 grid gap-6 lg:grid-cols-3">
        {deploySteps.map(([title, steps]) => (
          <div key={title as string} className="glass-tile p-6">
            <h2 className="text-xl font-black text-white">{title}</h2>
            <ol className="mt-4 space-y-3 text-sm text-slate-300">
              {(steps as string[]).map((step, index) => <li key={step}><span className="text-cyan">{index + 1}.</span> {step}</li>)}
            </ol>
          </div>
        ))}
      </section>

      <section className="glass-tile mt-10 p-6 sm:p-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="section-label">30-day beta playbook</p>
            <h2 className="mt-3 text-3xl font-black">Growth-focused but honest.</h2>
          </div>
          <Link href="/pricing" className="btn-secondary">View pricing status</Link>
        </div>
        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          {launchPlan.map(([days, goal, detail]) => (
            <div key={days} className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
              <p className="text-sm font-black text-cyan">{days}</p>
              <h3 className="mt-2 text-xl font-black text-white">{goal}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-400">{detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-10 rounded-3xl border border-amber-300/20 bg-amber-300/10 p-6 text-sm leading-6 text-amber-50">
        <strong>Required public wording:</strong> “AI-assisted preliminary Web3 launch readiness review.” Do not use “certified audit,” “100% secure,” or “payment successful” unless real verified processes exist.
      </section>
    </main>
  );
}
