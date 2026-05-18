import type { PackagePlan } from "@/lib/types";
import Link from "next/link";

const plans: PackagePlan[] = [
  { id: "free-scan", name: "Free Scan", category: "free", price_inr: 0, description: "Instant automated launch-surface scan with honest Not assessed handling.", deliverables: ["Website URL scan", "Partial score", "Top findings", "PDF/HTML/Markdown/JSON export"], turnaround_time: "Instant", cta: "Start Free", billing_cycles: ["one_time"] },
  { id: "quick-risk-report", name: "Quick Risk Report", category: "service", price_inr: 999, description: "Manual review request for a saved scan. Payment collection is intentionally deferred until verification flow is live.", deliverables: ["Priority risks", "Founder summary", "Fix direction", "Manual confirmation"], turnaround_time: "24–48 hrs", cta: "Request Review", billing_cycles: ["one_time"] },
  { id: "detailed-launch", name: "Launch Readiness Report", category: "service", price_inr: 2999, description: "Multi-surface readiness review across website, dApp, API, wallet, admin evidence, and contract input.", deliverables: ["Multi-surface review", "Full readiness checklist", "Evidence gaps", "Fix guidance"], turnaround_time: "2–4 days", cta: "Request Scope", billing_cycles: ["one_time"], popular: true },
  { id: "fix-suggestion-pack", name: "Fix Suggestion Pack", category: "service", price_inr: 7999, description: "Finding-specific fix patterns and verification checklist. No automatic paid access until payment module is finished.", deliverables: ["Fix per finding", "Safer code patterns", "Retest checklist", "Scope notes"], turnaround_time: "3–5 days", cta: "Request Fix Pack", billing_cycles: ["one_time"] },
  { id: "manual-pre-audit", name: "Manual Pre-Audit Review", category: "service", price_inr: 14999, description: "Manual review package for launch teams that need deeper guidance before a formal audit.", deliverables: ["Manual review", "Risk matrix", "Evidence checklist", "Founder notes"], turnaround_time: "5–7 days", cta: "Request Review", billing_cycles: ["one_time"] },
  { id: "full-launch-readiness", name: "Full Launch Readiness", category: "service", price_inr: 29999, description: "End-to-end launch readiness support. Payment activation remains pending until the final payment phase.", deliverables: ["Complete report", "OpSec checklist", "Final readiness notes", "Manual handoff"], turnaround_time: "7–10 days", cta: "Request Full", billing_cycles: ["one_time"] },
];

function PlanAction({ plan }: { plan: PackagePlan }) {
  if (plan.price_inr <= 0) {
    return <Link href="/scanner/unified-url" className="btn-primary mt-6 inline-flex w-full justify-center">Start Free Scan</Link>;
  }

  return (
    <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
      <p className="font-black">Payment module pending</p>
      <p className="mt-1 leading-6">
        This plan is visible for launch planning only. UPI/Razorpay collection will be enabled in the final payment phase after verification and audit logs are complete.
      </p>
      <Link href="/contact" className="mt-3 inline-flex w-full justify-center rounded-2xl bg-slate-950 px-4 py-3 text-sm font-black text-white transition hover:bg-slate-800">
        {plan.cta}
      </Link>
    </div>
  );
}

export function PricingSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="section-label">Transparent pricing</p>
          <h2 className="mt-3 text-3xl font-black sm:text-4xl">Pricing is visible. Payments are intentionally deferred.</h2>
          <p className="mt-3 max-w-xl text-sm leading-7 text-slate-600">
            Start with a free scan now. Paid review packages are shown for planning, but UPI/Razorpay checkout is pending until the final payment phase. No fake paid status or frontend-only subscription activation.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/launch-readiness" className="btn-secondary shrink-0">Launch checklist →</Link>
          <Link href="/contact" className="btn-secondary shrink-0">Talk to us →</Link>
        </div>
      </div>

      <div className="mt-6 rounded-3xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
        <b>Payment status:</b> pending by design. Until the final payment phase, users can scan/export reports, and paid plans are request-only.
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {plans.map((plan) => (
          <div key={plan.id} className={`card flex flex-col p-6 transition hover:-translate-y-0.5 ${plan.popular ? "border-amber-300" : ""}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="badge text-xs">{plan.category === "free" ? "Live" : "Payment pending"}</span>
                <h3 className="mt-2 text-base font-black leading-tight text-slate-950">{plan.name}</h3>
              </div>
              {plan.popular && <span className="shrink-0 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-bold text-amber-800">Popular</span>}
            </div>

            <div className="mt-4 flex items-baseline gap-1">
              {plan.price_inr === 0 ? (
                <span className="text-4xl font-black text-slate-950">Free</span>
              ) : (
                <>
                  <span className="text-lg font-bold text-slate-500">₹</span>
                  <span className="text-4xl font-black text-slate-950">{plan.price_inr.toLocaleString("en-IN")}</span>
                </>
              )}
            </div>

            <p className="mt-3 text-sm leading-6 text-slate-600">{plan.description}</p>
            <ul className="mt-4 flex-1 space-y-2">
              {plan.deliverables.map((item) => (
                <li key={item} className="flex items-center gap-2 text-sm text-slate-700">
                  <span className="grid h-4 w-4 shrink-0 place-items-center rounded-full border border-emerald-200 bg-emerald-50 text-[10px] font-black text-emerald-700">✓</span>
                  {item}
                </li>
              ))}
            </ul>

            <p className="mt-4 text-xs font-medium uppercase tracking-wider text-slate-500">Turnaround: {plan.turnaround_time}</p>
            <PlanAction plan={plan} />
          </div>
        ))}
      </div>

      <p className="mt-8 text-center text-xs text-slate-500">
        No payment/subscription success is shown until final payment integration is verified. See {" "}
        <Link href="/feature-status" className="underline hover:text-slate-700">Feature Status</Link>.
      </p>
    </section>
  );
}
