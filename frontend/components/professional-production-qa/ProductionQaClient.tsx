"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type JsonMap = Record<string, unknown>;

function isRecord(value: unknown): value is JsonMap {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asRecord(value: unknown): JsonMap {
  return isRecord(value) ? value : {};
}

function asArray(value: unknown): JsonMap[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function asText(value: unknown, fallback = "—") {
  if (value === undefined || value === null || value === "") return fallback;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return fallback;
  }
}

function jsonText(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function tone(value: unknown) {
  const text = asText(value, "").toLowerCase();
  if (text.includes("ready") || text.includes("allowed") || text.includes("pass") || text === "true") return "badge-green";
  if (text.includes("missing") || text.includes("blocked") || text.includes("hold") || text.includes("fail") || text === "false") return "badge-red";
  if (text.includes("manual") || text.includes("warning") || text.includes("setup")) return "badge-amber";
  return "badge-cyan";
}

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mt-4 max-h-[420px] overflow-auto rounded-2xl border border-white/10 bg-black/40 p-4 text-xs leading-5 text-slate-300">{jsonText(value)}</pre>;
}

function MetricCard({ label, value, state }: { label: string; value: unknown; state?: unknown }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-black text-white">{asText(value, "0")}</p>
      {state !== undefined && <span className={`badge mt-3 ${tone(state)}`}>{asText(state)}</span>}
    </div>
  );
}

function ChecklistTable({ checks }: { checks: JsonMap[] }) {
  return (
    <div className="mt-4 overflow-x-auto rounded-2xl border border-white/10">
      <table className="w-full min-w-[840px] text-left text-sm">
        <thead className="bg-white/[0.04] text-xs uppercase tracking-[0.16em] text-slate-500">
          <tr>
            <th className="px-4 py-3">Check</th>
            <th className="px-4 py-3">State</th>
            <th className="px-4 py-3">Required</th>
            <th className="px-4 py-3">Source</th>
            <th className="px-4 py-3">Fix</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/10">
          {checks.map((check, index) => (
            <tr key={`${asText(check.key, "check")}-${index}`}>
              <td className="px-4 py-3 font-semibold text-white">{asText(check.label)}</td>
              <td className="px-4 py-3"><span className={`badge ${tone(check.state)}`}>{asText(check.state)}</span></td>
              <td className="px-4 py-3 text-slate-300">{asText(check.required)}</td>
              <td className="px-4 py-3 font-mono text-xs text-slate-400">{asText(check.source)}</td>
              <td className="max-w-[360px] px-4 py-3 text-slate-400">{asText(check.fix)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StepList({ items }: { items: JsonMap[] }) {
  return (
    <div className="mt-4 grid gap-3">
      {items.map((item, index) => {
        const stepUrl = asText(item.url, "");
        const command = asText(item.command, "");
        const hasUrl = stepUrl.length > 0;
        const hasCommand = command.length > 0;
        return (
          <div key={`${asText(item.order, String(index))}-${asText(item.area, "step")}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="font-black text-white">{asText(item.order, String(index + 1))}. {asText(item.area, asText(item.title, "Step"))}</h3>
              {hasUrl ? <span className="badge badge-cyan">Live check</span> : null}
            </div>
            {hasCommand ? <pre className="mt-3 overflow-auto rounded-xl bg-black/40 p-3 text-xs text-slate-300">{command}</pre> : null}
            {hasUrl ? <p className="mt-3 break-all font-mono text-xs text-cyan">{stepUrl}</p> : null}
            <p className="mt-2 text-sm leading-6 text-slate-400">{asText(item.expected, asText(item.pass_signal, ""))}</p>
          </div>
        );
      })}
    </div>
  );
}

export function ProductionQaClient() {
  const [status, setStatus] = useState<JsonMap | null>(null);
  const [localPlan, setLocalPlan] = useState<JsonMap | null>(null);
  const [smoke, setSmoke] = useState<JsonMap | null>(null);
  const [release, setRelease] = useState<JsonMap | null>(null);
  const [competitor, setCompetitor] = useState<JsonMap | null>(null);
  const [decision, setDecision] = useState<JsonMap | null>(null);
  const [runs, setRuns] = useState<JsonMap | null>(null);
  const [activeJson, setActiveJson] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadAll() {
    setLoading(true);
    setError(null);
    try {
      const [nextStatus, nextLocal, nextSmoke, nextRelease, nextCompetitor, nextDecision, nextRuns] = await Promise.all([
        apiGet<JsonMap>("/professional-production-qa/status"),
        apiGet<JsonMap>("/professional-production-qa/local-test-plan"),
        apiGet<JsonMap>("/professional-production-qa/live-smoke-checklist"),
        apiGet<JsonMap>("/professional-production-qa/release-checklist"),
        apiGet<JsonMap>("/professional-production-qa/competitor-position"),
        apiGet<JsonMap>("/professional-production-qa/launch-decision"),
        apiGet<JsonMap>("/professional-production-qa/runs"),
      ]);
      setStatus(nextStatus);
      setLocalPlan(nextLocal);
      setSmoke(nextSmoke);
      setRelease(nextRelease);
      setCompetitor(nextCompetitor);
      setDecision(nextDecision);
      setRuns(nextRuns);
      setActiveJson(nextDecision);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function recordPassedWithWarnings() {
    setRecording(true);
    setError(null);
    try {
      await apiPost<JsonMap>("/professional-production-qa/runs", {
        project_name: "Web3Guard AI",
        environment: "production",
        overall_status: "passed_with_warnings",
        checked_by: "manual-admin",
        summary: "Manual Phase U QA checkpoint recorded from production QA dashboard. Replace with actual local/build/live evidence after running commands.",
        checks: [
          { name: "backend_pytest", status: "warning", note: "Record real command output before public launch." },
          { name: "frontend_typecheck", status: "warning", note: "Record real command output before public launch." },
          { name: "frontend_build", status: "warning", note: "Record real command output before public launch." },
        ],
      });
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRecording(false);
    }
  }

  useEffect(() => {
    void loadAll();
  }, []);

  const checks = useMemo(() => asArray(release?.checks), [release]);
  const smokeSteps = useMemo(() => asArray(smoke?.steps), [smoke]);
  const localCommands = useMemo(() => asArray(localPlan?.commands), [localPlan]);
  const scores = asRecord(competitor?.scores_out_of_100);
  const whatWeMatch = Array.isArray(competitor?.what_we_match_now) ? competitor?.what_we_match_now as unknown[] : [];
  const gaps = Array.isArray(competitor?.what_we_do_not_match_yet) ? competitor?.what_we_do_not_match_yet as unknown[] : [];
  const runList = asArray(runs?.runs);

  return (
    <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="glass-tile p-6 sm:p-8">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="section-label">Phase U</p>
            <h1 className="mt-3 text-4xl font-black tracking-[-0.06em] sm:text-6xl">First real production QA.</h1>
            <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400">
              Final local test plan, live smoke checklist, release decision gate, QA evidence log, and honest competitor-level positioning before public beta. No certified-audit claim is enabled here.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button onClick={loadAll} disabled={loading} className="rounded-2xl border border-cyan/30 bg-cyan/10 px-5 py-3 text-sm font-black text-cyan transition hover:bg-cyan/15 disabled:opacity-60">
              {loading ? "Checking..." : "Refresh QA"}
            </button>
            <button onClick={recordPassedWithWarnings} disabled={recording} className="rounded-2xl border border-amber-400/30 bg-amber-500/10 px-5 py-3 text-sm font-black text-amber-100 transition hover:bg-amber-500/15 disabled:opacity-60">
              {recording ? "Recording..." : "Record manual checkpoint"}
            </button>
          </div>
        </div>
        <div className="mt-6 flex flex-wrap gap-2">
          <span className="badge badge-green">Real-only QA</span>
          <span className="badge badge-cyan">Pre-audit readiness claim only</span>
          <span className="badge badge-amber">Manual evidence required</span>
          <span className="badge badge-purple">No replacement claim</span>
        </div>
        {error && <div className="mt-5 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</div>}
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Launch decision" value={decision?.decision} state={decision?.decision} />
        <MetricCard label="Safe public beta" value={asText(decision?.safe_for_public_beta)} state={decision?.safe_for_public_beta} />
        <MetricCard label="QA runs" value={status?.qa_runs_recorded} state={status?.qa_runs_recorded} />
        <MetricCard label="Certified audit claim" value={asText(decision?.certified_audit_claim_allowed)} state={decision?.certified_audit_claim_allowed} />
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="glass-tile p-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-2xl font-black text-white">Release checklist</h2>
            <button onClick={() => setActiveJson(release)} className="badge badge-cyan">View JSON</button>
          </div>
          <ChecklistTable checks={checks} />
        </div>
        <div className="glass-tile p-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-2xl font-black text-white">Launch decision</h2>
            <span className={`badge ${tone(decision?.decision)}`}>{asText(decision?.decision)}</span>
          </div>
          <p className="mt-3 text-sm leading-7 text-slate-400">Allowed claim: {asText(decision?.allowed_claim)}</p>
          <JsonBlock value={{ blockers: decision?.blockers, next_actions: decision?.next_actions }} />
        </div>
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-2">
        <div className="glass-tile p-5">
          <h2 className="text-2xl font-black text-white">Local commands</h2>
          <StepList items={localCommands} />
        </div>
        <div className="glass-tile p-5">
          <h2 className="text-2xl font-black text-white">Live smoke checklist</h2>
          <StepList items={smokeSteps} />
        </div>
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="glass-tile p-5">
          <h2 className="text-2xl font-black text-white">Competitor level</h2>
          <div className="mt-4 grid gap-3">
            {Object.entries(scores).map(([key, value]) => (
              <div key={key} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">{key.replaceAll("_", " ")}</p>
                <p className="mt-1 text-3xl font-black text-white">{asText(value)}<span className="text-base text-slate-500">/100</span></p>
              </div>
            ))}
          </div>
        </div>
        <div className="glass-tile p-5">
          <h2 className="text-2xl font-black text-white">Honest gap matrix</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-emerald-400/15 bg-emerald-500/10 p-4">
              <h3 className="font-black text-emerald-100">We match now</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-300">{whatWeMatch.map((item, index) => <li key={index}>{asText(item)}</li>)}</ul>
            </div>
            <div className="rounded-2xl border border-amber-400/15 bg-amber-500/10 p-4">
              <h3 className="font-black text-amber-100">Still missing</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-300">{gaps.map((item, index) => <li key={index}>{asText(item)}</li>)}</ul>
            </div>
          </div>
          <p className="mt-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm leading-7 text-slate-400">{asText(competitor?.direct_competition_summary)}</p>
        </div>
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-2">
        <div className="glass-tile p-5">
          <h2 className="text-2xl font-black text-white">QA evidence log</h2>
          <div className="mt-4 grid gap-3">
            {runList.length === 0 && <p className="text-sm text-slate-400">No QA runs recorded yet. Run real local/build/live checks first, then record evidence.</p>}
            {runList.map((run) => (
              <button key={asText(run.id)} onClick={() => setActiveJson(run)} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left transition hover:border-cyan/30 hover:bg-cyan/5">
                <div className="flex flex-wrap items-center justify-between gap-3"><span className="font-black text-white">{asText(run.project_name)}</span><span className={`badge ${tone(run.overall_status)}`}>{asText(run.overall_status)}</span></div>
                <p className="mt-2 text-xs text-slate-500">{asText(run.created_at)} · {asText(run.checked_by)}</p>
                <p className="mt-2 text-sm text-slate-400">{asText(run.summary)}</p>
              </button>
            ))}
          </div>
        </div>
        <div className="glass-tile p-5">
          <h2 className="text-2xl font-black text-white">Selected JSON</h2>
          <JsonBlock value={activeJson ?? decision} />
        </div>
      </section>
    </main>
  );
}
