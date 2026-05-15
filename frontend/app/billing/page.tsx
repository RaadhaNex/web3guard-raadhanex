"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { PaymentGatewayStatus, PaymentIntent, SubscriptionRecord } from "@/lib/types";

export default function BillingPage() {
  const [gateway, setGateway] = useState<PaymentGatewayStatus | null>(null);
  const [paymentId, setPaymentId] = useState("");
  const [payment, setPayment] = useState<PaymentIntent | null>(null);
  const [subscriptions, setSubscriptions] = useState<SubscriptionRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<PaymentGatewayStatus>("/payments/status").then(setGateway).catch((err) => setError(err.message));
    apiGet<{ subscriptions: SubscriptionRecord[] }>("/subscriptions").then((data) => setSubscriptions(data.subscriptions || [])).catch(() => undefined);
  }, []);

  async function checkPayment() {
    setError(null);
    setPayment(null);
    try {
      const data = await apiGet<{ payment_intent: PaymentIntent }>(`/payments/${encodeURIComponent(paymentId)}`);
      setPayment(data.payment_intent);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment lookup failed");
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Billing</p>
      <h1 className="mt-3 text-4xl font-black sm:text-5xl">Real payment status, no fake subscription activation.</h1>
      <p className="mt-4 max-w-3xl text-slate-400">Razorpay payments are verified only by backend signature or webhook checks. UPI fallback remains manual and needs admin verification.</p>

      {gateway && (
        <div className="mt-8 grid gap-4 md:grid-cols-4">
          <div className="card p-5"><p className="text-sm text-slate-400">Mode</p><p className="mt-2 font-black">{gateway.payment_mode}</p></div>
          <div className="card p-5"><p className="text-sm text-slate-400">Razorpay</p><p className="mt-2 font-black">{gateway.razorpay_configured ? "Configured" : "Not configured"}</p></div>
          <div className="card p-5"><p className="text-sm text-slate-400">Webhook</p><p className="mt-2 font-black">{gateway.razorpay_webhook_configured ? "Configured" : "Missing"}</p></div>
          <div className="card p-5"><p className="text-sm text-slate-400">UPI fallback</p><p className="mt-2 font-black">{gateway.upi_manual_enabled ? "Available" : "Disabled"}</p></div>
        </div>
      )}

      <div className="card mt-8 grid gap-3 p-5 md:grid-cols-[1fr_auto]">
        <input className="input" value={paymentId} onChange={(e) => setPaymentId(e.target.value)} placeholder="Payment intent ID, e.g. pay_xxxxx" />
        <button className="btn-primary" onClick={checkPayment}>Check Status</button>
      </div>
      {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}
      {payment && (
        <div className="card mt-6 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div><p className="text-xl font-black">{payment.package_name}</p><p className="text-sm text-slate-400">{payment.id}</p></div>
            <span className="rounded-full border border-cyan/30 bg-cyan/10 px-3 py-1 text-sm font-bold text-cyan">{payment.status}</span>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <p className="rounded-2xl bg-white/[0.03] p-4">Amount<br/><b>₹{payment.amount_inr.toLocaleString("en-IN")}</b></p>
            <p className="rounded-2xl bg-white/[0.03] p-4">Provider<br/><b>{payment.provider}</b></p>
            <p className="rounded-2xl bg-white/[0.03] p-4">Subscription<br/><b>{payment.subscription_id || "Not activated"}</b></p>
          </div>
        </div>
      )}

      <div className="card mt-8 overflow-x-auto">
        <div className="p-5"><h2 className="text-2xl font-black">Subscription records</h2><p className="mt-1 text-sm text-slate-400">Only real records created after verified/admin-approved payments are shown.</p></div>
        <table className="w-full min-w-[850px] text-left text-sm">
          <thead className="bg-white/[0.04]"><tr><th className="p-4">Plan</th><th className="p-4">Status</th><th className="p-4">Amount</th><th className="p-4">Provider</th><th className="p-4">Period</th></tr></thead>
          <tbody>{subscriptions.map((sub) => <tr key={sub.id} className="border-t border-white/10"><td className="p-4 font-bold">{sub.plan_name}<br/><span className="text-xs font-normal text-slate-500">{sub.id}</span></td><td className="p-4">{sub.status}</td><td className="p-4">₹{sub.amount_inr.toLocaleString("en-IN")}</td><td className="p-4">{sub.provider}</td><td className="p-4 text-slate-400">{sub.current_period_start || "—"}<br/>{sub.current_period_end || "—"}</td></tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}
