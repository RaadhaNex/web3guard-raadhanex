import Link from "next/link";

const pendingItems = [
  "UPI QR / UTR submission flow",
  "Admin manual verification panel",
  "Razorpay test checkout + webhook verification",
  "Payment audit log review",
  "Subscription activation only after verified payment",
];

export default function BillingPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-amber-700">Billing deferred</p>
      <h1 className="mt-3 text-4xl font-black text-slate-950 sm:text-5xl">Payments are pending until the final payment phase.</h1>
      <p className="mt-4 max-w-3xl text-slate-600">
        Web3Guard AI currently keeps paid access honest: no frontend-only paid status, no fake subscription activation, and no unverified payment success. Free scanner and report export remain available.
      </p>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5">
          <p className="text-sm font-bold text-emerald-700">Live now</p>
          <p className="mt-2 text-2xl font-black text-emerald-950">Free scan</p>
          <p className="mt-2 text-sm leading-6 text-emerald-900">URL scan, saved reports, and direct PDF/HTML/Markdown/JSON export.</p>
        </div>
        <div className="rounded-3xl border border-amber-200 bg-amber-50 p-5">
          <p className="text-sm font-bold text-amber-700">Pending</p>
          <p className="mt-2 text-2xl font-black text-amber-950">UPI manual</p>
          <p className="mt-2 text-sm leading-6 text-amber-900">Will require UTR/reference submission and admin verification before access activation.</p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5">
          <p className="text-sm font-bold text-slate-500">Later</p>
          <p className="mt-2 text-2xl font-black text-slate-950">Razorpay</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">Will be enabled only after test checkout, signature verification, and webhook audit pass.</p>
        </div>
      </div>

      <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-black text-slate-950">Final payment phase checklist</h2>
        <ul className="mt-5 grid gap-3 md:grid-cols-2">
          {pendingItems.map((item) => (
            <li key={item} className="rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm font-semibold text-slate-700">
              {item}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-8 rounded-3xl border border-red-200 bg-red-50 p-6 text-red-900">
        <h2 className="text-xl font-black">Blocked until payment phase</h2>
        <p className="mt-2 text-sm leading-6">
          Do not display “Paid”, “Subscription active”, “Payment successful”, or “Premium unlocked” unless payment is verified by admin or a real payment provider webhook/signature.
        </p>
      </div>

      <div className="mt-8 flex flex-wrap gap-3">
        <Link href="/scanner/unified-url" className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-black text-white hover:bg-slate-800">Run free scan</Link>
        <Link href="/pricing" className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-800 hover:bg-slate-50">View planning prices</Link>
        <Link href="/launch-readiness" className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-800 hover:bg-slate-50">Launch readiness</Link>
      </div>
    </div>
  );
}
