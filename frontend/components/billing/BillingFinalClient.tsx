"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";

type PlanLimitRow = {
  package_id: string;
  name: string;
  category: string;
  price_inr: number;
  billing_cycles: string[];
  popular: boolean;
  limits: Record<string, unknown>;
  activation_rule: string;
};

type BillingStatus = {
  ok: boolean;
  phase: string;
  checked_at: string;
  razorpay_live_ready: boolean;
  checkout_ready: boolean;
  webhook_ready: boolean;
  upi_manual_ready: boolean;
  counts: Record<string, number>;
  required_env: Array<{ name: string; required_for: string; secret: boolean }>;
  webhook_endpoint: string;
  checkout_flow: string[];
  blocked_states: string[];
  real_only_note: string;
  provider_status: {
    payment_mode: string;
    razorpay_enabled: boolean;
    razorpay_configured: boolean;
    razorpay_webhook_configured: boolean;
    upi_manual_enabled: boolean;
    upi_id_configured: boolean;
    real_only_note: string;
  };
};

type PlanLimitsResponse = { ok: boolean; plans: PlanLimitRow[] };

function boolBadge(label: string, value: boolean) {
  return (
    <span className={`badge ${value ? "badge-green" : "badge-amber"}`}>
      {value ? "✓" : "Needs setup"} {label}
    </span>
  );
}

function money(value: number) {
  if (value <= 0) return "₹0";
  return `₹${value.toLocaleString("en-IN")}`;
}

function limitText(value: unknown) {
  if (value === true) return "Yes";
  if (value === false) return "No";
  if (typeof value === "string") return value.replaceAll("_", " ");
  if (typeof value === "number") return value.toLocaleString("en-IN");
  if (value === null || value === undefined) return "—";
  return String(value);
}

export function BillingFinalClient() {
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [plans, setPlans] = useState<PlanLimitRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [statusData, limitsData] = await Promise.all([
        apiGet<BillingStatus>("/billing/status"),
        apiGet<PlanLimitsResponse>("/billing/plan-limits"),
      ]);
      setStatus(statusData);
      setPlans(limitsData.plans || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load billing status");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const modeLabel = useMemo(() => status?.provider_status?.payment_mode?.replaceAll("_", " ") || "loading", [status]);

  if (loading) {
    return <CommandLoadingState label="Loading payment verification status..." />;
  }

  if (error) {
    return <CommandNotice tone="danger" title="Billing status could not load" text={error} />;
  }

  return (
    <div className="grid gap-8">
      <section className="grid gap-4 md:grid-cols-4">
        <div className="command-card p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Mode</p>
          <p className="mt-2 text-2xl font-black capitalize text-white">{modeLabel}</p>
        </div>
        <div className="command-card p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Checkout</p>
          <p className="mt-2 text-2xl font-black text-white">{status?.checkout_ready ? "Ready" : "Needs keys"}</p>
        </div>
        <div className="command-card p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Webhook</p>
          <p className="mt-2 text-2xl font-black text-white">{status?.webhook_ready ? "Ready" : "Needs secret"}</p>
        </div>
        <div className="command-card p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Active subs</p>
          <p className="mt-2 text-2xl font-black text-white">{status?.counts?.active_subscriptions ?? 0}</p>
        </div>
      </section>

      <section className="command-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="section-label">Payment verification status</p>
            <h2 className="mt-3 text-2xl font-black text-white">Real checkout is allowed only after backend verification.</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">{status?.real_only_note}</p>
          </div>
          <button type="button" className="btn-secondary" onClick={() => void load()}>Refresh status</button>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {boolBadge("Razorpay configured", Boolean(status?.provider_status?.razorpay_configured))}
          {boolBadge("Webhook configured", Boolean(status?.provider_status?.razorpay_webhook_configured))}
          {boolBadge("UPI configured", Boolean(status?.provider_status?.upi_id_configured))}
          {boolBadge("Full live ready", Boolean(status?.razorpay_live_ready))}
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <p className="text-sm font-black text-white">Verified checkout flow</p>
            <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm leading-6 text-slate-300">
              {(status?.checkout_flow || []).map((step) => <li key={step}>{step}</li>)}
            </ol>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <p className="text-sm font-black text-white">Required backend environment</p>
            <div className="mt-4 grid gap-2">
              {(status?.required_env || []).map((item) => (
                <div key={item.name} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm">
                  <span className="mono font-bold text-cyan">{item.name}</span>
                  <span className="text-xs text-slate-400">{item.secret ? "backend secret" : "public/config"} · {item.required_for}</span>
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs text-slate-500">Webhook endpoint: <span className="mono text-slate-300">{status?.webhook_endpoint}</span></p>
          </div>
        </div>

        <div className="mt-5 rounded-2xl border border-red-400/20 bg-red-500/10 p-4 text-sm leading-6 text-red-100">
          <p className="font-black">Blocked payment states</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {(status?.blocked_states || []).map((item) => <span key={item} className="badge badge-red">{item}</span>)}
          </div>
        </div>
      </section>

      <section className="command-card p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="section-label">Plan limits</p>
            <h2 className="mt-3 text-2xl font-black text-white">Verified access levels and product limits.</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">
              These limits are displayed from package metadata. Premium access still requires verified payment or manual admin approval.
            </p>
          </div>
          <Link href="/pricing" className="btn-secondary">Open pricing</Link>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {plans.map((plan) => (
            <div key={plan.package_id} className="glass-tile p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-lg font-black text-white">{plan.name}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">{plan.category} · {plan.billing_cycles.join(", ")}</p>
                </div>
                {plan.popular ? <span className="badge badge-cyan">Popular</span> : null}
              </div>
              <p className="mt-4 text-3xl font-black text-cyan">{money(plan.price_inr)}</p>
              <div className="mt-4 grid gap-2 text-sm text-slate-300">
                <p><strong className="text-white">Scans:</strong> {limitText(plan.limits.scan_runs_per_month)}</p>
                <p><strong className="text-white">Saved reports:</strong> {limitText(plan.limits.saved_reports_per_month)}</p>
                <p><strong className="text-white">Manual slots:</strong> {limitText(plan.limits.manual_review_slots)}</p>
                <p><strong className="text-white">Team:</strong> {limitText(plan.limits.team_members)}</p>
                <p><strong className="text-white">Activation:</strong> {plan.activation_rule.replaceAll("_", " ")}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
