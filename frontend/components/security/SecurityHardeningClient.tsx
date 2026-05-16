"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "@/lib/api";

type Check = {
  key: string;
  label: string;
  passed: boolean;
  severity: string;
  evidence: string;
  fix: string;
};

type Status = {
  readiness: string;
  score: number;
  passed: number;
  total: number;
  checks: Check[];
};

type HeadersPolicy = {
  recommended_headers: Record<string, string>;
  deployment_note: string;
  report_only: boolean;
};

type Retention = {
  retention_days: Record<string, number>;
  delete_request_sla_days: number;
  manual_actions_required: string[];
};

type FixGuidanceItem = {
  key: string;
  label: string;
  severity: string;
  module: string;
  where_to_fix: string;
  why_it_matters: string;
  how_to_fix: string;
  verify: string;
  safe_test: string;
  status: string;
};

type FixGuidance = {
  items: FixGuidanceItem[];
  summary: { total: number; critical: number; high: number; by_severity: Record<string, number> };
  real_only_note: string;
};

type ActionPlanPhase = {
  phase: string;
  goal: string;
  items: FixGuidanceItem[];
};

type ActionPlan = {
  phases: ActionPlanPhase[];
  next_recommended_patch: string;
  safe_testing_targets: string[];
  blocked_testing: string[];
  real_only_note: string;
};

function severityTone(severity: string) {
  const value = severity.toLowerCase();
  if (value === "critical") return "border-rose-300 bg-rose-50 text-rose-800";
  if (value === "high") return "border-orange-300 bg-orange-50 text-orange-800";
  if (value === "medium") return "border-amber-300 bg-amber-50 text-amber-800";
  return "border-slate-200 bg-slate-50 text-slate-700";
}

function readinessTone(readiness: string) {
  if (readiness.includes("blocked")) return "text-rose-600";
  if (readiness.includes("not_ready")) return "text-orange-600";
  if (readiness.includes("needs")) return "text-amber-600";
  return "text-emerald-600";
}

function copyToClipboard(text: string) {
  if (typeof navigator === "undefined" || !navigator.clipboard) return;
  void navigator.clipboard.writeText(text);
}

export function SecurityHardeningClient() {
  const [status, setStatus] = useState<Status | null>(null);
  const [headers, setHeaders] = useState<HeadersPolicy | null>(null);
  const [retention, setRetention] = useState<Retention | null>(null);
  const [guidance, setGuidance] = useState<FixGuidance | null>(null);
  const [actionPlan, setActionPlan] = useState<ActionPlan | null>(null);
  const [activeTab, setActiveTab] = useState<"checks" | "guidance" | "headers" | "testing">("checks");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiGet<Status>("/security/status"),
      apiGet<HeadersPolicy>("/security/headers-policy"),
      apiGet<Retention>("/security/data-retention"),
      apiGet<FixGuidance>("/security/fix-guidance"),
      apiGet<ActionPlan>("/security/action-plan"),
    ])
      .then(([statusData, headersData, retentionData, guidanceData, planData]) => {
        setStatus(statusData);
        setHeaders(headersData);
        setRetention(retentionData);
        setGuidance(guidanceData);
        setActionPlan(planData);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Security hardening status failed"));
  }, []);

  const failedChecks = useMemo(() => {
    return status?.checks.filter((item) => !item.passed) || [];
  }, [status?.checks]);

  if (error) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-rose-900">
          <p className="font-black">Security hardening status could not load.</p>
          <p className="mt-2 text-sm">{error}</p>
        </div>
      </main>
    );
  }

  if (!status) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">Loading security hardening status...</div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#f8fafc] text-slate-950">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <p className="text-xs font-black uppercase tracking-[0.32em] text-cyan-500">Web3Guard production hardening</p>
          <div className="mt-4 grid gap-6 lg:grid-cols-[1fr_0.75fr] lg:items-end">
            <div>
              <h1 className="max-w-4xl text-4xl font-black tracking-tight sm:text-6xl">Real-only launch readiness center</h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">
                This page turns scanner findings into implementation work: checks, exact fix locations, verification commands, and safe testing boundaries. It does not claim certified audit status.
              </p>
            </div>
            <div className="grid gap-3 rounded-3xl border border-slate-200 bg-slate-50 p-5 sm:grid-cols-3 lg:grid-cols-1">
              <Metric label="Readiness" value={status.readiness} valueClass={readinessTone(status.readiness)} />
              <Metric label="Score" value={`${status.score}/100`} valueClass="text-cyan-600" />
              <Metric label="Passed" value={`${status.passed}/${status.total}`} valueClass="text-slate-950" />
            </div>
          </div>
        </section>

        <section className="mt-6 grid gap-4 md:grid-cols-4">
          <SummaryCard label="Action required" value={failedChecks.length} tone="text-amber-600" />
          <SummaryCard label="Critical guidance" value={guidance?.summary.critical ?? 0} tone="text-rose-600" />
          <SummaryCard label="High guidance" value={guidance?.summary.high ?? 0} tone="text-orange-600" />
          <SummaryCard label="Next patch" value={actionPlan?.next_recommended_patch || "loading"} small />
        </section>

        <nav className="mt-8 flex flex-wrap gap-3">
          {[
            ["checks", "Checks"],
            ["guidance", "Fix guidance"],
            ["headers", "Headers + retention"],
            ["testing", "Safe testing"],
          ].map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveTab(key as typeof activeTab)}
              className={`rounded-full border px-5 py-3 text-sm font-black transition ${activeTab === key ? "border-cyan-300 bg-cyan-100 text-cyan-900" : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}`}
            >
              {label}
            </button>
          ))}
        </nav>

        {activeTab === "checks" ? (
          <section className="mt-6 grid gap-4 lg:grid-cols-2">
            {status.checks.map((check) => (
              <article key={check.key} className={`rounded-3xl border bg-white p-5 shadow-sm ${check.passed ? "border-emerald-200" : "border-amber-200"}`}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h2 className="font-black text-slate-950">{check.label}</h2>
                  <span className={`rounded-full border px-3 py-1 text-xs font-black ${check.passed ? "border-emerald-200 bg-emerald-50 text-emerald-700" : severityTone(check.severity)}`}>
                    {check.passed ? "PASS" : "ACTION"}
                  </span>
                </div>
                <p className="mt-3 text-sm text-slate-500">Severity: {check.severity}</p>
                <p className="mt-2 text-sm leading-6 text-slate-700"><strong>Evidence:</strong> {check.evidence}</p>
                <p className="mt-2 text-sm leading-6 text-cyan-700"><strong>Fix:</strong> {check.fix}</p>
              </article>
            ))}
          </section>
        ) : null}

        {activeTab === "guidance" ? (
          <section className="mt-6 space-y-6">
            {actionPlan?.phases.map((phase) => (
              <div key={phase.phase} className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-2xl font-black">{phase.phase}</h2>
                <p className="mt-2 text-sm text-slate-600">{phase.goal}</p>
                <div className="mt-5 grid gap-4 lg:grid-cols-2">
                  {phase.items.map((item) => (
                    <GuidanceCard key={item.key} item={item} />
                  ))}
                </div>
              </div>
            ))}
            {guidance ? <p className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{guidance.real_only_note}</p> : null}
          </section>
        ) : null}

        {activeTab === "headers" ? (
          <section className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-2xl font-black">Recommended security headers</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">{headers?.deployment_note} CSP report-only: {String(headers?.report_only)}</p>
              <pre className="mt-4 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(headers?.recommended_headers || {}, null, 2)}</pre>
              <button type="button" onClick={() => copyToClipboard(JSON.stringify(headers?.recommended_headers || {}, null, 2))} className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-black text-slate-900 hover:bg-white">Copy headers JSON</button>
            </div>
            <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-2xl font-black">Data retention controls</h2>
              <pre className="mt-4 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(retention?.retention_days || {}, null, 2)}</pre>
              <p className="mt-4 text-sm text-slate-600">Deletion SLA: {retention?.delete_request_sla_days ?? "Not set"} days</p>
              <ul className="mt-4 space-y-2 text-sm text-slate-700">
                {(retention?.manual_actions_required || []).map((item) => <li key={item}>• {item}</li>)}
              </ul>
            </div>
          </section>
        ) : null}

        {activeTab === "testing" ? (
          <section className="mt-6 grid gap-6 lg:grid-cols-2">
            <div className="rounded-[2rem] border border-emerald-200 bg-emerald-50 p-6">
              <h2 className="text-2xl font-black text-emerald-950">Safe testing targets</h2>
              <ul className="mt-4 space-y-3 text-sm font-semibold text-emerald-900">
                {(actionPlan?.safe_testing_targets || []).map((item) => <li key={item}>• {item}</li>)}
              </ul>
            </div>
            <div className="rounded-[2rem] border border-rose-200 bg-rose-50 p-6">
              <h2 className="text-2xl font-black text-rose-950">Blocked testing</h2>
              <ul className="mt-4 space-y-3 text-sm font-semibold text-rose-900">
                {(actionPlan?.blocked_testing || []).map((item) => <li key={item}>• {item}</li>)}
              </ul>
            </div>
          </section>
        ) : null}
      </div>
    </main>
  );
}

function Metric({ label, value, valueClass }: { label: string; value: string | number; valueClass?: string }) {
  return (
    <div>
      <p className="text-xs font-black uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 truncate text-lg font-black ${valueClass || "text-slate-950"}`}>{value}</p>
    </div>
  );
}

function SummaryCard({ label, value, tone, small }: { label: string; value: string | number; tone?: string; small?: boolean }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-black uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-2 ${small ? "text-sm leading-6" : "text-3xl"} font-black ${tone || "text-slate-950"}`}>{value}</p>
    </div>
  );
}

function GuidanceCard({ item }: { item: FixGuidanceItem }) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-black text-slate-950">{item.label}</h3>
        <span className={`rounded-full border px-3 py-1 text-xs font-black ${severityTone(item.severity)}`}>{item.severity}</span>
      </div>
      <div className="mt-4 grid gap-3 text-sm">
        <Info label="Where to fix" value={item.where_to_fix} />
        <Info label="Why it matters" value={item.why_it_matters} />
        <Info label="How to fix" value={item.how_to_fix} />
        <Info label="Verify" value={item.verify} mono />
        <Info label="Safe test" value={item.safe_test} />
      </div>
    </article>
  );
}

function Info({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-2xl bg-white p-4">
      <p className="text-xs font-black uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-slate-800 ${mono ? "font-mono text-xs" : "text-sm leading-6"}`}>{value}</p>
    </div>
  );
}
