import Link from "next/link";
import { BillingFinalClient } from "@/components/billing/BillingFinalClient";

export default function BillingPage() {
  return (
    <main className="command-page">
      <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <section className="command-hero p-6 sm:p-8">
          <div className="relative z-[1] max-w-4xl">
            <p className="section-label">Payment final</p>
            <h1 className="mt-3 text-4xl font-black sm:text-5xl">Razorpay + UPI billing is live only when backend verification is ready.</h1>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
              Billing moves Web3Guard from deferred billing to a real payment workflow: backend-created Razorpay orders, server-side checkout signature verification, signed webhook verification, manual UPI fallback, audit logs, and plan-limit visibility.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/pricing" className="btn-primary">Choose plan</Link>
              <Link href="/feature-status" className="btn-secondary">Feature status</Link>
              <Link href="/production-deployment-qa" className="btn-secondary">Deployment QA</Link>
            </div>
            <p className="mt-4 text-xs text-slate-500">No frontend-only paid state · no fake subscription unlock · no key secrets exposed to the browser</p>
          </div>
        </section>

        <section className="mt-8">
          <BillingFinalClient />
        </section>
      </div>
    </main>
  );
}
