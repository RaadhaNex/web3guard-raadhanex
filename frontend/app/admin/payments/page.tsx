"use client";

import { useMemo, useState } from "react";
import { API_BASE, apiPatch } from "@/lib/api";
import type { PaymentIntent, PaymentStatus, SubscriptionRecord } from "@/lib/types";

const paymentStatuses: PaymentStatus[] = [
  "created",
  "manual_verification_pending",
  "verified",
  "failed",
  "cancelled",
  "refunded",
  "webhook_verified",
];

const subscriptionStatuses = [
  "pending",
  "active",
  "past_due",
  "cancelled",
  "expired",
  "manual_review",
];

function statusTone(value: string) {
  const status = value.toLowerCase();

  if (["verified", "webhook_verified", "razorpay_paid", "active"].includes(status)) {
    return "border-emerald-400/30 bg-emerald-500/10 text-emerald-200";
  }

  if (status.includes("pending") || status.includes("manual")) {
    return "border-amber-400/30 bg-amber-500/10 text-amber-100";
  }

  if (["failed", "cancelled", "refunded", "expired"].includes(status)) {
    return "border-red-400/30 bg-red-500/10 text-red-100";
  }

  return "border-white/10 bg-white/[0.04] text-slate-200";
}

function amount(value: number | undefined | null) {
  return `₹${(value || 0).toLocaleString("en-IN")}`;
}

export default function AdminPaymentsPage() {
  const [token, setToken] = useState("");
  const [payments, setPayments] = useState<PaymentIntent[]>([]);
  const [subscriptions, setSubscriptions] = useState<SubscriptionRecord[]>([]);
  const [summary, setSummary] = useState<{
    total: number;
    verified_revenue_inr: number;
    pending_amount_inr: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [referenceByPayment, setReferenceByPayment] = useState<Record<string, string>>({});

  const authHeaders = useMemo(() => ({ "x-admin-token": token.trim() }), [token]);
  const canLoad = token.trim().length > 0;

  async function readJson(response: Response) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) return response.json();
    return { detail: await response.text() };
  }

  async function load() {
    setError(null);
    setMessage(null);

    if (!canLoad) {
      setError("Admin token required. Use the ADMIN_TOKEN configured in Render backend environment.");
      return;
    }

    const [paymentsRes, subsRes] = await Promise.all([
      fetch(`${API_BASE}/admin/payments`, { headers: authHeaders }),
      fetch(`${API_BASE}/admin/subscriptions`, { headers: authHeaders }),
    ]);

    const paymentsData = await readJson(paymentsRes);
    const subsData = await readJson(subsRes);

    if (!paymentsRes.ok) {
      setError(paymentsData.detail || paymentsData.error || "Failed to load payments");
      return;
    }

    if (!subsRes.ok) {
      setError(subsData.detail || subsData.error || "Failed to load subscriptions");
      return;
    }

    setPayments(paymentsData.payment_intents || []);
    setSummary(paymentsData.summary || null);
    setSubscriptions(subsData.subscriptions || []);
  }

  async function updatePayment(id: string, status: PaymentStatus, note?: string) {
    setBusy(id);
    setError(null);
    setMessage(null);

    try {
      await apiPatch(
        `/admin/payments/${id}`,
        {
          status,
          payment_reference: referenceByPayment[id]?.trim() || undefined,
          note: note || `Updated from admin payments UI to ${status}`,
        },
        { headers: authHeaders }
      );

      setMessage(`Payment ${id} updated to ${status}.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment update failed");
    } finally {
      setBusy(null);
    }
  }

  async function verifyManualPayment(payment: PaymentIntent) {
    const reference = referenceByPayment[payment.id]?.trim();

    if (!reference) {
      setError("Manual UPI verification requires a transaction/reference ID before marking verified.");
      return;
    }

    await updatePayment(
      payment.id,
      "verified",
      `Manual UPI verified by admin. Reference: ${reference}`
    );
  }

  async function updateSubscription(id: string, status: string) {
    setBusy(id);
    setError(null);
    setMessage(null);

    try {
      await apiPatch(
        `/admin/subscriptions/${id}`,
        { status, note: `Updated from admin payments UI to ${status}` },
        { headers: authHeaders }
      );

      setMessage(`Subscription ${id} updated to ${status}.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Subscription update failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-white/10 bg-white/[0.03] p-6 shadow-2xl shadow-black/20">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">
          Admin payments
        </p>
        <h1 className="mt-3 text-4xl font-black">
          Payment verification command center
        </h1>
        <p className="mt-3 max-w-3xl text-slate-400">
          Razorpay payments are trusted only after checkout signature or webhook verification. UPI fallback requires manual admin approval with a transaction reference. No fake payment success state is used.
        </p>

        <div className="mt-6 grid gap-3 md:grid-cols-[1fr_auto]">
          <input
            className="input"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="Admin token from Render ADMIN_TOKEN env"
          />
          <button className="btn-primary" onClick={load} disabled={!canLoad}>
            Load payments
          </button>
        </div>
      </section>

      {summary ? (
        <section className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="card p-5">
            <p className="text-sm text-slate-400">Total payments</p>
            <p className="mt-2 text-3xl font-black">{summary.total}</p>
          </div>
          <div className="card p-5">
            <p className="text-sm text-slate-400">Verified revenue</p>
            <p className="mt-2 text-3xl font-black text-emerald-200">
              {amount(summary.verified_revenue_inr)}
            </p>
          </div>
          <div className="card p-5">
            <p className="text-sm text-slate-400">Pending amount</p>
            <p className="mt-2 text-3xl font-black text-amber-100">
              {amount(summary.pending_amount_inr)}
            </p>
          </div>
        </section>
      ) : null}

      {error ? (
        <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">
          {error}
        </p>
      ) : null}

      {message ? (
        <p className="mt-4 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-emerald-100">
          {message}
        </p>
      ) : null}

      <section className="mt-6 grid gap-5">
        {payments.length === 0 ? (
          <div className="card p-6 text-slate-400">
            Load payments to review Razorpay and manual UPI verification status.
          </div>
        ) : null}

        {payments.map((payment) => {
          const isManual = payment.provider === "upi_manual" || payment.manual_verification_required;
          const verified = ["verified", "webhook_verified", "razorpay_paid"].includes(payment.status);

          return (
            <article key={payment.id} className="card p-5">
              <div className="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <p className="break-all text-lg font-black">{payment.id}</p>
                    <span className={`rounded-full border px-3 py-1 text-xs font-black ${statusTone(payment.status)}`}>
                      {payment.status}
                    </span>
                    <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-bold text-slate-300">
                      {payment.provider || "upi_manual"}
                    </span>
                  </div>

                  <div className="mt-4 grid gap-2 text-sm text-slate-300 sm:grid-cols-2">
                    <p><span className="text-slate-500">Package:</span> {payment.package_name}</p>
                    <p><span className="text-slate-500">Amount:</span> {amount(payment.amount_inr)}</p>
                    <p><span className="text-slate-500">Customer:</span> {payment.customer_email || payment.customer_name || "—"}</p>
                    <p><span className="text-slate-500">Billing:</span> {payment.billing_cycle}</p>
                    <p><span className="text-slate-500">Razorpay order:</span> {payment.razorpay_order_id || "—"}</p>
                    <p><span className="text-slate-500">Payment ID:</span> {payment.razorpay_payment_id || "—"}</p>
                    <p><span className="text-slate-500">Verified at:</span> {payment.verified_at || payment.webhook_verified_at || "—"}</p>
                    <p><span className="text-slate-500">Subscription:</span> {payment.subscription_id || "—"}</p>
                  </div>

                  <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-300">
                    <p className="font-black text-white">Verification checklist</p>
                    <ul className="mt-2 space-y-1">
                      <li>• Razorpay: verify checkout signature or webhook signature before marking paid.</li>
                      <li>• Manual UPI: require transaction/reference ID and admin review.</li>
                      <li>• Subscription activates only after verified payment state.</li>
                      <li>• Never mark success from frontend-only callback.</li>
                    </ul>
                  </div>
                </div>

                <div className="rounded-3xl border border-white/10 bg-white/[0.02] p-4">
                  <label className="text-sm font-bold text-slate-300">
                    Update status
                    <select
                      className="select mt-2 w-full"
                      value={payment.status}
                      disabled={busy === payment.id}
                      onChange={(event) => updatePayment(payment.id, event.target.value as PaymentStatus)}
                    >
                      {paymentStatuses.map((status) => (
                        <option key={status}>{status}</option>
                      ))}
                    </select>
                  </label>

                  {isManual && !verified ? (
                    <div className="mt-4 rounded-2xl border border-amber-400/30 bg-amber-500/10 p-4">
                      <p className="text-sm font-black text-amber-100">
                        Manual UPI verification required
                      </p>
                      <input
                        className="input mt-3"
                        value={referenceByPayment[payment.id] || ""}
                        onChange={(event) =>
                          setReferenceByPayment((current) => ({
                            ...current,
                            [payment.id]: event.target.value,
                          }))
                        }
                        placeholder="UPI transaction/reference ID"
                      />
                      <button
                        className="btn-secondary mt-3 w-full"
                        disabled={busy === payment.id}
                        onClick={() => verifyManualPayment(payment)}
                      >
                        Verify manual UPI payment
                      </button>
                    </div>
                  ) : null}

                  <button
                    className="btn-secondary mt-4 w-full"
                    disabled={busy === payment.id}
                    onClick={() => updatePayment(payment.id, "failed", "Marked failed/cancelled from admin payments UI")}
                  >
                    Mark failed
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </section>

      <section className="card mt-8 overflow-x-auto">
        <div className="p-5">
          <h2 className="text-2xl font-black">Subscriptions</h2>
          <p className="mt-2 text-sm text-slate-400">
            Subscription status should be active only after payment verification.
          </p>
        </div>
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="bg-white/[0.04]">
            <tr>
              <th className="p-4">Subscription</th>
              <th className="p-4">Plan</th>
              <th className="p-4">Amount</th>
              <th className="p-4">Status</th>
              <th className="p-4">Period</th>
            </tr>
          </thead>
          <tbody>
            {subscriptions.map((subscription) => (
              <tr key={subscription.id} className="border-t border-white/10">
                <td className="p-4 font-bold">
                  {subscription.id}
                  <br />
                  <span className="text-xs font-normal text-slate-500">
                    {subscription.payment_intent_id}
                  </span>
                </td>
                <td className="p-4">
                  {subscription.plan_name}
                  <br />
                  <span className="text-xs text-slate-500">{subscription.billing_cycle}</span>
                </td>
                <td className="p-4">{amount(subscription.amount_inr)}</td>
                <td className="p-4">
                  <select
                    className="select"
                    value={subscription.status}
                    disabled={busy === subscription.id}
                    onChange={(event) => updateSubscription(subscription.id, event.target.value)}
                  >
                    {subscriptionStatuses.map((status) => (
                      <option key={status}>{status}</option>
                    ))}
                  </select>
                </td>
                <td className="p-4 text-slate-400">
                  {subscription.current_period_start || "—"}
                  <br />
                  {subscription.current_period_end || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
