"use client";

import { useEffect, useState } from "react";
import { apiPost } from "@/lib/api";
import type { BillingCycle, PackagePlan, PaymentGatewayStatus, PaymentIntent } from "@/lib/types";

type Props = { plan: PackagePlan };

type IntentResponse = {
  ok: boolean;
  intent: PaymentIntent;
  payment_status: PaymentGatewayStatus;
  razorpay_steps: string[];
  manual_steps: string[];
  disclaimer: string;
};

type RazorpaySuccess = {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
};

type RazorpayOptions = {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  prefill?: { name?: string; email?: string };
  notes?: Record<string, string>;
  handler: (response: RazorpaySuccess) => void;
  modal?: { ondismiss?: () => void };
};

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => { open: () => void };
  }
}

function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window === "undefined") return resolve(false);
    if (window.Razorpay) return resolve(true);
    const existing = document.querySelector<HTMLScriptElement>("script[data-razorpay-checkout]");
    if (existing) {
      existing.addEventListener("load", () => resolve(true), { once: true });
      existing.addEventListener("error", () => resolve(false), { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.dataset.razorpayCheckout = "true";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export function UpiCheckout({ plan }: Props) {
  const defaultCycle: BillingCycle = plan.billing_cycles?.[0] || "one_time";
  const [billingCycle, setBillingCycle] = useState<BillingCycle>(defaultCycle);
  const [providerPreference, setProviderPreference] = useState<"auto" | "razorpay" | "upi_manual">("auto");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [project, setProject] = useState("");
  const [intent, setIntent] = useState<PaymentIntent | null>(null);
  const [gateway, setGateway] = useState<PaymentGatewayStatus | null>(null);
  const [manualSteps, setManualSteps] = useState<string[]>([]);
  const [razorpaySteps, setRazorpaySteps] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [verifyLoading, setVerifyLoading] = useState(false);

  useEffect(() => { setIntent(null); setSuccess(null); setError(null); }, [plan.id]);

  async function createIntent() {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const data = await apiPost<IntentResponse>("/payment-intent", {
        package_id: plan.id,
        billing_cycle: billingCycle,
        customer_name: name || null,
        customer_email: email || null,
        project_name: project || null,
        provider_preference: providerPreference,
      });
      setIntent(data.intent);
      setGateway(data.payment_status);
      setManualSteps(data.manual_steps || []);
      setRazorpaySteps(data.razorpay_steps || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment intent failed");
    } finally {
      setLoading(false);
    }
  }

  async function openRazorpay() {
    if (!intent?.razorpay_order_id || !intent.razorpay_key_id) {
      setError("Razorpay order is not available. Generate a Razorpay intent first or use manual UPI fallback.");
      return;
    }
    setVerifyLoading(true);
    setError(null);
    setSuccess(null);
    const loaded = await loadRazorpayScript();
    if (!loaded || !window.Razorpay) {
      setVerifyLoading(false);
      setError("Razorpay Checkout script failed to load. Use manual UPI fallback or check internet connection.");
      return;
    }
    const options: RazorpayOptions = {
      key: intent.razorpay_key_id,
      amount: intent.amount_paise || intent.amount_inr * 100,
      currency: intent.currency || "INR",
      name: "Web3Guard AI by RAADHANEX",
      description: intent.package_name,
      order_id: intent.razorpay_order_id,
      prefill: { name: name || intent.customer_name || "", email: email || intent.customer_email || "" },
      notes: { payment_intent_id: intent.id, package_id: intent.package_id },
      handler: async (response) => {
        try {
          const data = await apiPost<{ ok: boolean; payment_intent: PaymentIntent; message: string }>("/payments/razorpay/verify", {
            payment_intent_id: intent.id,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          setIntent(data.payment_intent);
          setSuccess(data.message || "Payment verified by backend signature check.");
        } catch (err) {
          setError(err instanceof Error ? err.message : "Razorpay verification failed");
        } finally {
          setVerifyLoading(false);
        }
      },
      modal: { ondismiss: () => setVerifyLoading(false) },
    };
    new window.Razorpay(options).open();
  }

  if (plan.price_inr <= 0) return <a href="/scanner" className="btn-primary mt-6">Start Free Scan</a>;

  const razorpayReady = gateway?.razorpay_configured || intent?.provider === "razorpay";

  return (
    <div className="mt-6 rounded-2xl border border-white/10 bg-black/20 p-4">
      {plan.billing_cycles && plan.billing_cycles.length > 1 && (
        <select className="select mb-3" value={billingCycle} onChange={(e) => setBillingCycle(e.target.value as BillingCycle)}>
          {plan.billing_cycles.map((cycle) => <option key={cycle} value={cycle}>{cycle.replace("_", " ")}</option>)}
        </select>
      )}
      <div className="mb-3 grid gap-2 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-xs text-slate-300">
        <label className="font-bold text-slate-100">Payment mode</label>
        <select className="select" value={providerPreference} onChange={(e) => setProviderPreference(e.target.value as "auto" | "razorpay" | "upi_manual")}>
          <option value="auto">Auto: Razorpay if configured, otherwise UPI manual</option>
          <option value="razorpay">Razorpay Checkout only</option>
          <option value="upi_manual">UPI manual fallback</option>
        </select>
        <p>No fake success: payment/subscription is active only after backend verification or manual admin approval.</p>
      </div>
      <div className="grid gap-2">
        <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Name optional" />
        <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email optional" />
        <input className="input" value={project} onChange={(e) => setProject(e.target.value)} placeholder="Project optional" />
      </div>
      <button className="btn-primary mt-3 w-full" onClick={createIntent} disabled={loading}>
        {loading ? "Creating Payment Intent..." : "Create Payment Intent"}
      </button>
      {error && <p className="mt-3 rounded-xl border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-100">{error}</p>}
      {success && <p className="mt-3 rounded-xl border border-emerald-400/30 bg-emerald-500/10 p-3 text-sm text-emerald-100">{success}</p>}
      {intent && (
        <div className="mt-4 space-y-3 rounded-2xl border border-cyan/20 bg-cyan/10 p-4 text-sm text-cyan-50">
          <p className="font-bold">Payment intent: {intent.id}</p>
          <p>Amount: ₹{intent.amount_inr.toLocaleString("en-IN")} · Mode: {intent.provider || "upi_manual"} · Status: {intent.status}</p>
          {intent.razorpay_order_id && <p className="text-xs text-cyan-100/80">Razorpay order: {intent.razorpay_order_id}</p>}
          {intent.razorpay_order_id && intent.razorpay_key_id && (
            <button className="btn-primary inline-flex" onClick={openRazorpay} disabled={verifyLoading}>
              {verifyLoading ? "Waiting for Checkout..." : "Pay with Razorpay Checkout"}
            </button>
          )}
          {intent.upi_deep_link && <a className="btn-secondary inline-flex" href={intent.upi_deep_link}>Open UPI App Manual Fallback</a>}
          {razorpayReady && razorpaySteps.length > 0 && <ol className="list-decimal space-y-1 pl-5 text-cyan-100/90">{razorpaySteps.map((step) => <li key={step}>{step}</li>)}</ol>}
          <details className="rounded-xl border border-white/10 p-3">
            <summary className="cursor-pointer font-bold">Manual UPI fallback steps</summary>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-cyan-100/90">{manualSteps.map((step) => <li key={step}>{step}</li>)}</ol>
          </details>
          <p className="text-xs text-cyan-100/70">Manual UPI requires reference submission. Razorpay requires backend signature/webhook verification. Subscription access is never activated from frontend-only state.</p>
        </div>
      )}
    </div>
  );
}
