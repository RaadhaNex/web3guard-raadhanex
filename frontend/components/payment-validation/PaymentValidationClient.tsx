"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";

type Gate = {
  key: string;
  label: string;
  passed: boolean;
  status: string;
  fix: string;
};

type EnvCheck = {
  name: string;
  configured: boolean;
  status: string;
  secret: boolean;
  required_for: string;
  value_preview?: string | null;
};

type PaymentValidationStatus = {
  ok: boolean;
  phase: string;
  checked_at: string;
  detected_mode: string;
  status: string;
  test_mode_ready: boolean;
  live_mode_ready: boolean;
  checkout_ready: boolean;
  webhook_ready: boolean;
  env_checks: EnvCheck[];
  gates: Gate[];
  counts: Record<string, number>;
  blocked_claims: string[];
  real_only_note: string;
};

type FirstPaidFlow = {
  ok: boolean;
  recommended_first_offer?: {
    id: string;
    name: string;
    price_inr: number;
    description: string;
    turnaround_time: string;
  };
  flow: Array<{ step: number; title: string; status: string; note: string }>;
  first_paid_cta: string;
  blocked_shortcuts: string[];
};

type RevenueReadiness = {
  ok: boolean;
  ready_for_first_paid_user: boolean;
  recommended_first_plan_id: string;
  recommended_first_price_inr: number;
  checklist: Array<{ item: string; status: string }>;
  outreach_offer: string;
  real_only_note: string;
};

type CheckoutDryRun = {
  ok: boolean;
  dry_run: boolean;
  package: { id: string; name: string; price_inr: number };
  selected_provider: string;
  status: string;
  amount_inr: number;
  will_create_real_order: boolean;
  next_steps: string[];
  real_only_note: string;
};

type ClaimCheck = {
  ok: boolean;
  allowed: boolean;
  blocked_terms: string[];
  safe_replacement: string;
};

const statusClass: Record<string, string> = {
  Assessed: "badge-green",
  Ready: "badge-green",
  "Test Ready": "badge-green",
  "Live Ready": "badge-green",
  "Needs API Key": "badge-amber",
  "Needs Setup": "badge-amber",
  "Provider Not Configured": "badge-amber",
  "Manual review required": "badge-amber",
};

function badge(label: string) {
  return <span className={`badge ${statusClass[label] || ""}`}>{label}</span>;
}

function money(value: number) {
  return value <= 0 ? "₹0" : `₹${value.toLocaleString("en-IN")}`;
}

export function PaymentValidationClient() {
  const [status, setStatus] = useState<PaymentValidationStatus | null>(null);
  const [flow, setFlow] = useState<FirstPaidFlow | null>(null);
  const [revenue, setRevenue] = useState<RevenueReadiness | null>(null);
  const [dryRun, setDryRun] = useState<CheckoutDryRun | null>(null);
  const [claimText, setClaimText] = useState("₹999 report unlocked after verified backend payment. Not a certified audit.");
  const [claimResult, setClaimResult] = useState<ClaimCheck | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [statusData, flowData, revenueData] = await Promise.all([
        apiGet<PaymentValidationStatus>("/payment-validation/status"),
        apiGet<FirstPaidFlow>("/payment-validation/first-paid-flow"),
        apiGet<RevenueReadiness>("/payment-validation/revenue-readiness"),
      ]);
      setStatus(statusData);
      setFlow(flowData);
      setRevenue(revenueData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load payment validation");
    } finally {
      setLoading(false);
    }
  }

  async function runDryRun() {
    setBusy(true);
    setError(null);
    try {
      const data = await apiPost<CheckoutDryRun>("/payment-validation/checkout-dry-run", {
        package_id: "quick-risk-report",
        provider_preference: "auto",
      });
      setDryRun(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dry run failed");
    } finally {
      setBusy(false);
    }
  }

  async function checkClaim() {
    setBusy(true);
    setError(null);
    try {
      const data = await apiPost<ClaimCheck>("/payment-validation/claim-check", { text: claimText });
      setClaimResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim check failed");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const passedGates = useMemo(() => status?.gates.filter((item) => item.passed).length || 0, [status]);

  if (loading) {
    return <CommandLoadingState label="Loading verified payment validation gates..." />;
  }

  if (error && !status) {
    return <CommandNotice tone="danger" title="Payment validation could not load" text={error} />;
  }

  return (
    <div className="grid gap-8">
      {error ? <CommandNotice tone="danger" title="Payment validation warning" text={error} /> : null}

      <section className="grid gap-4 md:grid-cols-4">
        <div className="command-card p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Mode</p>
          <p className="mt-2 text-2xl font-black capitalize text-white">{status?.detected_mode?.replaceAll("_", " ")}</p>
        </div>
        <div className="command-card p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Readiness</p>
          <p className="mt-2 text-2xl font-black text-white">{status?.status}</p>
        </div>
        <div className="command-card p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Gates passed</p>
          <p className="mt-2 text-2xl font-black text-white">{passedGates}/{status?.gates.length || 0}</p>
        </div>
        <div className="command-card p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Verified payments</p>
          <p className="mt-2 text-2xl font-black text-white">{status?.counts.verified_payments ?? 0}</p>
        </div>
      </section>

      <section className="command-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="section-label">Phase 34 payment validation</p>
            <h2 className="mt-3 text-2xl font-black text-white">First paid flow without fake payment success.</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">{status?.real_only_note}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn-secondary" onClick={() => void load()}>Refresh</button>
            <button type="button" className="btn-primary" disabled={busy} onClick={() => void runDryRun()}>{busy ? "Checking..." : "Dry-run ₹999 flow"}</button>
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <p className="text-sm font-black text-white">Verification gates</p>
            <div className="mt-4 grid gap-3">
              {(status?.gates || []).map((item) => (
                <div key={item.key} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-black text-white">{item.label}</p>
                    {badge(item.status)}
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{item.fix}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
            <p className="text-sm font-black text-white">Backend environment checklist</p>
            <div className="mt-4 grid gap-2">
              {(status?.env_checks || []).map((item) => (
                <div key={item.name} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm">
                  <span className="mono font-bold text-cyan">{item.name}</span>
                  <span className="text-xs text-slate-400">{item.secret ? "secret" : item.value_preview || "config"} · {item.required_for}</span>
                  {badge(item.status)}
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs leading-5 text-slate-500">Secrets are never shown in the browser. A configured public key may be masked for readiness only.</p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="command-card p-6">
          <p className="section-label">First paid offer</p>
          <h2 className="mt-3 text-2xl font-black text-white">{flow?.first_paid_cta}</h2>
          <p className="mt-3 text-sm leading-7 text-slate-400">Recommended first validation offer: {flow?.recommended_first_offer?.name} for {money(flow?.recommended_first_offer?.price_inr || 0)}. Keep it preliminary and manually reviewed.</p>
          <div className="mt-5 grid gap-3">
            {(flow?.flow || []).map((item) => (
              <div key={item.step} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-black text-white">{item.step}. {item.title}</p>
                  {badge(item.status)}
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-400">{item.note}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="command-card p-6">
          <p className="section-label">Revenue readiness</p>
          <h2 className="mt-3 text-2xl font-black text-white">{revenue?.ready_for_first_paid_user ? "Ready for controlled first sale" : "Needs setup before first sale"}</h2>
          <p className="mt-3 text-sm leading-7 text-slate-400">{revenue?.real_only_note}</p>
          <div className="mt-5 grid gap-2">
            {(revenue?.checklist || []).map((item) => (
              <div key={item.item} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm">
                <span className="font-bold text-slate-200">{item.item}</span>
                {badge(item.status)}
              </div>
            ))}
          </div>
          <div className="mt-5 rounded-2xl border border-cyan/20 bg-cyan/[0.06] p-4 text-sm leading-6 text-cyan-50">
            <p className="font-black">Outreach copy</p>
            <p className="mt-2">{revenue?.outreach_offer}</p>
          </div>
        </div>
      </section>

      {dryRun ? (
        <section className="command-card p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="section-label">Checkout dry run</p>
              <h2 className="mt-3 text-2xl font-black text-white">{dryRun.package.name} · {money(dryRun.amount_inr)}</h2>
              <p className="mt-3 text-sm leading-7 text-slate-400">Selected provider: <strong className="text-white">{dryRun.selected_provider.replaceAll("_", " ")}</strong>. {dryRun.real_only_note}</p>
            </div>
            {badge(dryRun.status)}
          </div>
          <ol className="mt-5 list-decimal space-y-2 pl-5 text-sm leading-6 text-slate-300">
            {dryRun.next_steps.map((step) => <li key={step}>{step}</li>)}
          </ol>
        </section>
      ) : null}

      <section className="command-card p-6">
        <p className="section-label">Payment claim checker</p>
        <h2 className="mt-3 text-2xl font-black text-white">Block risky payment/audit wording before launch.</h2>
        <textarea
          value={claimText}
          onChange={(event) => setClaimText(event.target.value)}
          className="mt-5 min-h-28 w-full rounded-2xl border border-white/10 bg-black/30 p-4 text-sm text-slate-100 outline-none ring-cyan/30 focus:ring-2"
        />
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="button" className="btn-primary" disabled={busy} onClick={() => void checkClaim()}>{busy ? "Checking..." : "Check wording"}</button>
          <Link href="/billing" className="btn-secondary">Open billing readiness</Link>
        </div>
        {claimResult ? (
          <div className={`mt-5 rounded-2xl border p-4 text-sm leading-6 ${claimResult.allowed ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-50" : "border-red-400/20 bg-red-500/10 text-red-50"}`}>
            <p className="font-black">{claimResult.allowed ? "Allowed" : "Blocked wording"}</p>
            {claimResult.blocked_terms.length ? <p className="mt-2">Blocked terms: {claimResult.blocked_terms.join(", ")}</p> : null}
            <p className="mt-2">{claimResult.safe_replacement}</p>
          </div>
        ) : null}
      </section>
    </div>
  );
}
