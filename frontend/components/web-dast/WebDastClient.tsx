"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { StatusPill } from "@/components/ui/StatusPill";
import { CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";

type Status = {
  ok: boolean;
  version: string;
  public_default: string;
  light_active: string;
  full_active: string;
  allowed_public_checks: string[];
  allowed_light_active_checks: string[];
  blocked_dangerous_tests: string[];
  required_disclaimer: string;
};

type FormState = {
  target_url: string;
  allowed_domains: string;
  contact_email: string;
  permission_type: string;
  authorized_acknowledged: boolean;
  run_live: boolean;
  verification_passed: boolean;
  request_destructive_tests: boolean;
};

const defaultForm: FormState = {
  target_url: "",
  allowed_domains: "",
  contact_email: "",
  permission_type: "owner",
  authorized_acknowledged: false,
  run_live: false,
  verification_passed: false,
  request_destructive_tests: false,
};

function toPayload(form: FormState) {
  return {
    ...form,
    allowed_domains: form.allowed_domains.split(",").map((item) => item.trim()).filter(Boolean),
  };
}

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mono max-h-96 overflow-auto rounded-2xl border border-white/10 bg-black/35 p-4 text-xs text-slate-300">{JSON.stringify(value, null, 2)}</pre>;
}

export function WebDastClient() {
  const [status, setStatus] = useState<Status | null>(null);
  const [form, setForm] = useState<FormState>(defaultForm);
  const [result, setResult] = useState<any>(null);
  const [token, setToken] = useState("");
  const [claim, setClaim] = useState("Authorized passive web security scan for verified owned scopes. Not a certified audit.");
  const [claimResult, setClaimResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        setStatus(await apiGet<Status>("/web-dast/status"));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load Web DAST status");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const payload = useMemo(() => toPayload(form), [form]);

  async function run(action: "safe" | "start" | "check" | "passive" | "light") {
    setError(null);
    try {
      if (action === "safe") setResult(await apiPost("/web-dast/safe-url-check", payload));
      if (action === "start") {
        const data: any = await apiPost("/web-dast/verify/start", payload);
        setResult(data);
        if (data?.token) setToken(data.token);
      }
      if (action === "check") {
        const data: any = await apiPost("/web-dast/verify/check", { ...payload, supplied_token: token, method: "manual_proof" });
        setResult(data);
        if (data?.verified) setForm((current) => ({ ...current, verification_passed: true }));
      }
      if (action === "passive") setResult(await apiPost("/web-dast/passive-baseline", payload));
      if (action === "light") setResult(await apiPost("/web-dast/light-active", payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    }
  }

  async function checkClaim() {
    setError(null);
    try {
      setClaimResult(await apiPost("/web-dast/claim-check", { text: claim, real_only_acknowledged: true }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim check failed");
    }
  }

  if (loading) return <CommandLoadingState label="Loading authorized DAST status..." />;

  return (
    <section className="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <div className="space-y-6">
        {error ? <CommandNotice tone="danger" title="Web DAST error" text={error} /> : null}
        <article className="clean-panel p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Authorized scan setup</p>
              <h2 className="mt-2 text-2xl font-black text-white">Lock scope before checks</h2>
            </div>
            <StatusPill status={status?.full_active || "Full Active Disabled"} />
          </div>
          <div className="mt-5 grid gap-3">
            <label className="grid gap-2 text-sm font-semibold text-slate-300">Target URL<input className="form-input" placeholder="https://your-owned-domain.com" value={form.target_url} onChange={(e) => setForm({ ...form, target_url: e.target.value })} /></label>
            <label className="grid gap-2 text-sm font-semibold text-slate-300">Allowed exact domains<input className="form-input" placeholder="your-owned-domain.com, app.your-owned-domain.com" value={form.allowed_domains} onChange={(e) => setForm({ ...form, allowed_domains: e.target.value })} /></label>
            <label className="grid gap-2 text-sm font-semibold text-slate-300">Contact email<input className="form-input" placeholder="security@yourcompany.com" value={form.contact_email} onChange={(e) => setForm({ ...form, contact_email: e.target.value })} /></label>
            <label className="grid gap-2 text-sm font-semibold text-slate-300">Permission type<select className="form-input" value={form.permission_type} onChange={(e) => setForm({ ...form, permission_type: e.target.value })}><option value="owner">I own this domain</option><option value="written_permission">I have written permission</option><option value="company_permission">Company permission verified</option></select></label>
            <label className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-300"><input type="checkbox" checked={form.authorized_acknowledged} onChange={(e) => setForm({ ...form, authorized_acknowledged: e.target.checked })} /> I confirm I own this target or have written authorization.</label>
            <label className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-300"><input type="checkbox" checked={form.run_live} onChange={(e) => setForm({ ...form, run_live: e.target.checked })} /> Run live passive HTTP checks after permission confirmation.</label>
          </div>
          <div className="mt-5 flex flex-wrap gap-3">
            <button className="btn-secondary" onClick={() => run("safe")}>Check scope</button>
            <button className="btn-secondary" onClick={() => run("start")}>Start verification</button>
            <button className="btn-primary" onClick={() => run("passive")}>Run passive baseline</button>
          </div>
        </article>

        <article className="clean-panel p-6">
          <p className="section-label">Verification proof</p>
          <p className="mt-2 text-sm leading-6 text-slate-400">Use the generated token from verification start, or paste your DNS/HTML/meta proof token here.</p>
          <textarea className="form-input mt-4 min-h-24" value={token} onChange={(e) => setToken(e.target.value)} />
          <div className="mt-4 flex flex-wrap gap-3">
            <button className="btn-secondary" onClick={() => run("check")}>Verify proof</button>
            <button className="btn-secondary" onClick={() => run("light")}>Run light authorized checks</button>
          </div>
          <label className="mt-4 flex items-start gap-3 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100"><input type="checkbox" checked={form.request_destructive_tests} onChange={(e) => setForm({ ...form, request_destructive_tests: e.target.checked })} /> Request destructive tests. This should be blocked.</label>
        </article>
      </div>

      <div className="space-y-6">
        <article className="clean-panel p-6">
          <p className="section-label">Policy status</p>
          <h2 className="mt-2 text-2xl font-black text-white">Safe states, not attack automation</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">{status?.required_disclaimer}</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {status?.allowed_public_checks.map((item) => <div key={item} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300">{item}</div>)}
          </div>
          <h3 className="mt-6 text-sm font-black uppercase tracking-[0.18em] text-red-200">Blocked tests</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {status?.blocked_dangerous_tests.map((item) => <span key={item} className="rounded-full border border-red-500/20 bg-red-500/10 px-3 py-1 text-xs font-bold text-red-100">{item}</span>)}
          </div>
        </article>
        <article className="clean-panel p-6">
          <p className="section-label">Result</p>
          {result ? <JsonBlock value={result} /> : <p className="mt-3 text-sm text-slate-400">Run a scope check, verification, or baseline scan to see evidence-first output.</p>}
        </article>
        <article className="clean-panel p-6">
          <p className="section-label">Claim check</p>
          <textarea className="form-input mt-3 min-h-24" value={claim} onChange={(e) => setClaim(e.target.value)} />
          <button className="btn-secondary mt-3" onClick={checkClaim}>Check wording</button>
          {claimResult ? <div className="mt-4"><JsonBlock value={claimResult} /></div> : null}
        </article>
      </div>
    </section>
  );
}
