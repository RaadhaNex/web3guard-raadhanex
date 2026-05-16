"use client";

import { useMemo, useState } from "react";
import { API_BASE, apiPatch } from "@/lib/api";
import type { PaymentIntent, PaymentStatus, SubscriptionRecord } from "@/lib/types";

const paymentStatuses: PaymentStatus[] = ["created", "manual_verification_pending", "verified", "failed", "cancelled", "refunded", "webhook_verified"];
const subscriptionStatuses = ["pending", "active", "past_due", "cancelled", "expired", "manual_review"];

export default function AdminPaymentsPage() {
  const [token, setToken] = useState("");
  const [payments, setPayments] = useState<PaymentIntent[]>([]);
  const [subscriptions, setSubscriptions] = useState<SubscriptionRecord[]>([]);
  const [summary, setSummary] = useState<{ total: number; verified_revenue_inr: number; pending_amount_inr: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const authHeaders = useMemo(() => ({ "x-admin-token": token }), [token]);

  async function load() {
    setError(null);
    const [paymentsRes, subsRes] = await Promise.all([
      fetch(`${API_BASE}/admin/payments`, { headers: authHeaders }),
      fetch(`${API_BASE}/admin/subscriptions`, { headers: authHeaders }),
    ]);
    const paymentsData = await paymentsRes.json().catch(() => ({}));
    const subsData = await subsRes.json().catch(() => ({}));
    if (!paymentsRes.ok) { setError(paymentsData.detail || "Failed to load payments"); return; }
    if (!subsRes.ok) { setError(subsData.detail || "Failed to load subscriptions"); return; }
    setPayments(paymentsData.payment_intents || []);
    setSummary(paymentsData.summary || null);
    setSubscriptions(subsData.subscriptions || []);
  }

  async function updatePayment(id: string, status: PaymentStatus) {
    setBusy(id); setError(null);
    try { await apiPatch(`/admin/payments/${id}`, { status, note: "Updated from admin payments UI" }, { headers: authHeaders }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Payment update failed"); }
    finally { setBusy(null); }
  }

  async function updateSubscription(id: string, status: string) {
    setBusy(id); setError(null);
    try { await apiPatch(`/admin/subscriptions/${id}`, { status, note: "Updated from admin payments UI" }, { headers: authHeaders }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Subscription update failed"); }
    finally { setBusy(null); }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Admin payments</p>
      <h1 className="mt-3 text-4xl font-black">Razorpay + UPI payment verification dashboard</h1>
      <p className="mt-3 max-w-3xl text-slate-400">Razorpay payment is trusted only after signature/webhook verification. UPI fallback requires manual admin approval.</p>
      <div className="card mt-8 grid gap-3 p-5 md:grid-cols-[1fr_auto]">
        <input className="input" value={token} onChange={(e) => setToken(e.target.value)} placeholder="Admin token from backend .env" />
        <button className="btn-primary" onClick={load}>Load Payments</button>
      </div>
      {summary && <div className="mt-6 grid gap-4 md:grid-cols-3"><div className="card p-4"><p className="text-sm text-slate-400">Total payments</p><p className="text-3xl font-black">{summary.total}</p></div><div className="card p-4"><p className="text-sm text-slate-400">Verified revenue</p><p className="text-3xl font-black">₹{summary.verified_revenue_inr.toLocaleString("en-IN")}</p></div><div className="card p-4"><p className="text-sm text-slate-400">Pending amount</p><p className="text-3xl font-black">₹{summary.pending_amount_inr.toLocaleString("en-IN")}</p></div></div>}
      {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}

      <div className="card mt-6 overflow-x-auto"><table className="w-full min-w-[1100px] text-left text-sm"><thead className="bg-white/[0.04]"><tr><th className="p-4">Intent</th><th className="p-4">Package</th><th className="p-4">Amount</th><th className="p-4">Provider</th><th className="p-4">Razorpay Order</th><th className="p-4">Status</th><th className="p-4">Subscription</th></tr></thead><tbody>{payments.map((p) => <tr key={p.id} className="border-t border-white/10 align-top"><td className="p-4 font-bold">{p.id}<br/><span className="text-xs font-normal text-slate-500">{p.created_at}</span></td><td className="p-4">{p.package_name}<br/><span className="text-xs text-slate-500">{p.billing_cycle}</span></td><td className="p-4">₹{p.amount_inr.toLocaleString("en-IN")}</td><td className="p-4">{p.provider}</td><td className="p-4 text-xs text-slate-400">{p.razorpay_order_id || "—"}<br/>{p.razorpay_payment_id || ""}</td><td className="p-4"><select className="select min-w-[190px]" value={p.status} disabled={busy === p.id} onChange={(e) => updatePayment(p.id, e.target.value as PaymentStatus)}>{paymentStatuses.map((status) => <option key={status}>{status}</option>)}</select></td><td className="p-4">{p.subscription_id || "—"}</td></tr>)}</tbody></table></div>

      <div className="card mt-8 overflow-x-auto"><div className="p-5"><h2 className="text-2xl font-black">Subscriptions</h2></div><table className="w-full min-w-[900px] text-left text-sm"><thead className="bg-white/[0.04]"><tr><th className="p-4">Subscription</th><th className="p-4">Plan</th><th className="p-4">Amount</th><th className="p-4">Status</th><th className="p-4">Period</th></tr></thead><tbody>{subscriptions.map((s) => <tr key={s.id} className="border-t border-white/10"><td className="p-4 font-bold">{s.id}<br/><span className="text-xs font-normal text-slate-500">{s.payment_intent_id}</span></td><td className="p-4">{s.plan_name}<br/><span className="text-xs text-slate-500">{s.billing_cycle}</span></td><td className="p-4">₹{s.amount_inr.toLocaleString("en-IN")}</td><td className="p-4"><select className="select" value={s.status} disabled={busy === s.id} onChange={(e) => updateSubscription(s.id, e.target.value)}>{subscriptionStatuses.map((status) => <option key={status}>{status}</option>)}</select></td><td className="p-4 text-slate-400">{s.current_period_start || "—"}<br/>{s.current_period_end || "—"}</td></tr>)}</tbody></table></div>
    </div>
  );
}
