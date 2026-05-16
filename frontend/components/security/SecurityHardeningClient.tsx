"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

type Status = { readiness: string; score: number; passed: number; total: number; checks: Array<{ key: string; label: string; passed: boolean; severity: string; evidence: string; fix: string }> };
type Headers = { recommended_headers: Record<string, string>; deployment_note: string; report_only: boolean };
type Retention = { retention_days: Record<string, number>; delete_request_sla_days: number; manual_actions_required: string[] };

export function SecurityHardeningClient() {
  const [status, setStatus] = useState<Status | null>(null);
  const [headers, setHeaders] = useState<Headers | null>(null);
  const [retention, setRetention] = useState<Retention | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiGet<Status>("/security/status"),
      apiGet<Headers>("/security/headers-policy"),
      apiGet<Retention>("/security/data-retention"),
    ])
      .then(([s, h, r]) => { setStatus(s); setHeaders(h); setRetention(r); })
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <main className="section"><div className="card border-red-500/30 text-red-100">{error}</div></main>;
  if (!status) return <main className="section"><div className="card">Loading security hardening status...</div></main>;

  return (
    <main className="section space-y-8">
      <section className="hero-grid rounded-[2rem] border border-white/10 bg-white/[0.03] p-8">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Web3Guard AI</p>
        <h1 className="mt-3 text-4xl font-black text-white md:text-5xl">Platform Security Hardening</h1>
        <p className="mt-4 max-w-3xl text-slate-300">Production readiness checks for admin token, CORS, Supabase, Razorpay, AI privacy, deep-tool sandboxing, retention, backups, and monitoring. This page does not fake readiness; missing production config is shown as action required.</p>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="card"><p className="text-sm text-slate-400">Readiness</p><p className="mt-1 text-2xl font-black text-white">{status.readiness}</p></div>
          <div className="card"><p className="text-sm text-slate-400">Hardening score</p><p className="mt-1 text-2xl font-black text-cyan">{status.score}/100</p></div>
          <div className="card"><p className="text-sm text-slate-400">Checks passed</p><p className="mt-1 text-2xl font-black text-white">{status.passed}/{status.total}</p></div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {status.checks.map((check) => (
          <article key={check.key} className={`card border ${check.passed ? "border-emerald-400/20" : "border-amber-400/30"}`}>
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-bold text-white">{check.label}</h2>
              <span className={`rounded-full px-3 py-1 text-xs font-bold ${check.passed ? "bg-emerald-400/10 text-emerald-200" : "bg-amber-400/10 text-amber-200"}`}>{check.passed ? "PASS" : "ACTION"}</span>
            </div>
            <p className="mt-3 text-sm text-slate-400">Severity: {check.severity}</p>
            <p className="mt-2 text-sm text-slate-300">Evidence: {check.evidence}</p>
            <p className="mt-2 text-sm text-cyan">Fix: {check.fix}</p>
          </article>
        ))}
      </section>

      {headers && <section className="card">
        <h2 className="text-2xl font-black text-white">Recommended security headers</h2>
        <p className="mt-2 text-sm text-slate-400">{headers.deployment_note} CSP report-only: {String(headers.report_only)}</p>
        <pre className="mt-4 overflow-auto rounded-2xl bg-black/40 p-4 text-xs text-slate-200">{JSON.stringify(headers.recommended_headers, null, 2)}</pre>
      </section>}

      {retention && <section className="card">
        <h2 className="text-2xl font-black text-white">Data retention controls</h2>
        <pre className="mt-4 overflow-auto rounded-2xl bg-black/40 p-4 text-xs text-slate-200">{JSON.stringify(retention.retention_days, null, 2)}</pre>
        <ul className="mt-4 space-y-2 text-sm text-slate-300">
          {retention.manual_actions_required.map((item) => <li key={item}>• {item}</li>)}
        </ul>
      </section>}
    </main>
  );
}
