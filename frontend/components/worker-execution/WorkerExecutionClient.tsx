"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { CommandEmptyState, CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";
import { StatusPill } from "@/components/ui/StatusPill";

type WorkerTool = {
  key: string;
  name: string;
  category: string;
  purpose: string;
  status: string;
  installed: boolean;
  path?: string | null;
  group_enabled: boolean;
  enabled_by_env: boolean;
  will_run: boolean;
  binary_default: string;
  command_template: string;
  next_action: string;
  real_only_note: string;
};

type WorkerStatus = {
  ok: boolean;
  version: string;
  worker_execution_enabled: boolean;
  ready_count: number;
  total_count: number;
  readiness_label: string;
  tools: WorkerTool[];
  phase_27_scope: string[];
  safety_boundaries: Record<string, boolean>;
  production_notes: string[];
};

type WorkerPlanStep = {
  order: number;
  tool: string;
  status: string;
  command_template: string;
  evidence_policy: string;
  when_missing: string;
  next_action: string;
};

type WorkerPlan = {
  ok: boolean;
  version: string;
  project_type: string;
  requested_tools: string[];
  steps: WorkerPlanStep[];
  queue_design: Record<string, string>;
  blocked_actions: string[];
};

type ProbeResult = {
  tool: string;
  status: string;
  returncode?: number | null;
  stdout?: string;
  stderr?: string;
  reason?: string;
  real_findings?: number;
  probe_only: boolean;
};

type ProbeResponse = {
  ok: boolean;
  version: string;
  probe_status: string;
  results: Record<string, ProbeResult>;
  real_only_note?: string;
  note?: string;
};

const defaultSelected: Record<string, boolean> = {
  slither: true,
  aderyn: true,
  semgrep: true,
  foundry: true,
  echidna: true,
  mythril: true,
};

function badgeClass(status: string) {
  const value = status.toLowerCase();
  if (value.includes("ready")) return "badge-green";
  if (value.includes("not installed")) return "badge-amber";
  if (value.includes("manual") || value.includes("not configured")) return "badge-purple";
  return "badge-cyan";
}

function safeJson(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function ToolCard({ tool, checked, onToggle }: { tool: WorkerTool; checked: boolean; onToggle: (checked: boolean) => void }) {
  return (
    <article className="glass-tile p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.22em] text-slate-500">{tool.category.replaceAll("_", " ")}</p>
          <h3 className="mt-2 text-xl font-black text-white">{tool.name}</h3>
        </div>
        <span className={`badge ${badgeClass(tool.status)}`}>{tool.status}</span>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-400">{tool.purpose}</p>
      <div className="mt-4 grid gap-2 text-xs text-slate-400 sm:grid-cols-2">
        <p><strong className="text-white">Installed:</strong> {tool.installed ? "yes" : "no"}</p>
        <p><strong className="text-white">Will run:</strong> {tool.will_run ? "yes" : "no"}</p>
        <p><strong className="text-white">Group enabled:</strong> {tool.group_enabled ? "yes" : "no"}</p>
        <p><strong className="text-white">Tool enabled:</strong> {tool.enabled_by_env ? "yes" : "no"}</p>
        <p className="sm:col-span-2"><strong className="text-white">Default binary:</strong> <span className="mono">{tool.binary_default}</span></p>
        {tool.path ? <p className="sm:col-span-2"><strong className="text-white">Resolved path:</strong> <span className="break-all">{tool.path}</span></p> : null}
      </div>
      <pre className="mono mt-4 overflow-x-auto rounded-2xl border border-white/10 bg-black/30 p-3 text-xs text-slate-300">{tool.command_template}</pre>
      <p className="mt-3 text-xs leading-5 text-amber-100">{tool.next_action}</p>
      <label className="mt-4 flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm font-bold text-slate-200">
        <input type="checkbox" checked={checked} onChange={(event) => onToggle(event.target.checked)} />
        Include in plan/probe
      </label>
    </article>
  );
}

export function WorkerExecutionClient() {
  const [status, setStatus] = useState<WorkerStatus | null>(null);
  const [plan, setPlan] = useState<WorkerPlan | null>(null);
  const [probe, setProbe] = useState<ProbeResponse | null>(null);
  const [selected, setSelected] = useState<Record<string, boolean>>(defaultSelected);
  const [projectType, setProjectType] = useState("Founder-owned Solidity workspace");
  const [realOnly, setRealOnly] = useState(true);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadStatus() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<WorkerStatus>("/worker-execution/status");
      setStatus(data);
      setSelected((current) => {
        const next = { ...current };
        for (const tool of data.tools) {
          if (typeof next[tool.key] !== "boolean") next[tool.key] = true;
        }
        return next;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load worker execution status.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadStatus();
  }, []);

  const selectedTools = useMemo(
    () => Object.entries(selected).filter(([, enabled]) => enabled).map(([tool]) => tool),
    [selected]
  );

  async function buildPlan() {
    setActionLoading("plan");
    setError(null);
    setPlan(null);
    try {
      const data = await apiPost<WorkerPlan>("/worker-execution/plan", {
        project_type: projectType,
        tools: selectedTools,
        real_only_acknowledged: realOnly,
      });
      setPlan(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create worker plan.");
    } finally {
      setActionLoading(null);
    }
  }

  async function runProbe() {
    setActionLoading("probe");
    setError(null);
    setProbe(null);
    try {
      const data = await apiPost<ProbeResponse>("/worker-execution/probe", {
        tools: selectedTools,
        real_only_acknowledged: realOnly,
      });
      setProbe(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not run worker probe.");
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) return <CommandLoadingState label="Loading worker execution matrix..." />;
  if (error && !status) {
    return (
      <div className="mt-8 grid gap-4">
        <CommandNotice tone="warning" title="Worker status could not be loaded" text={error} />
        <button type="button" className="btn-secondary w-fit" onClick={() => void loadStatus()}>Retry</button>
      </div>
    );
  }
  if (!status) return <CommandEmptyState title="No worker status available" text="The backend did not return worker execution data." />;

  return (
    <section className="mt-8 space-y-8">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Ready probes</p>
          <p className="mt-2 text-3xl font-black text-white">{status.ready_count}/{status.total_count}</p>
          <p className="mt-2 text-sm text-slate-400">{status.readiness_label}</p>
        </div>
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Execution flag</p>
          <p className="mt-2 text-2xl font-black text-white">{status.worker_execution_enabled ? "Enabled" : "Disabled"}</p>
          <p className="mt-2 text-sm text-slate-400">Disabled is safe default until isolated workers are deployed.</p>
        </div>
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Rule</p>
          <p className="mt-2 text-2xl font-black text-white">No fake output</p>
          <p className="mt-2 text-sm text-slate-400">Missing tools stay status-only, not vulnerability evidence.</p>
        </div>
      </div>

      {error ? <CommandNotice tone="warning" title="Action warning" text={error} /> : null}

      <div className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
        <div className="glass-tile p-6">
          <p className="section-label">Control panel</p>
          <h2 className="mt-2 text-2xl font-black text-white">Worker plan + version probe</h2>
          <label className="mt-5 block text-sm font-bold text-slate-300">Project type
            <input className="input mt-2" value={projectType} onChange={(event) => setProjectType(event.target.value)} />
          </label>
          <label className="mt-4 flex gap-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50">
            <input type="checkbox" checked={realOnly} onChange={(event) => setRealOnly(event.target.checked)} />
            <span>I understand this is real-only worker readiness. Missing tools must show Tool Not Installed / Provider Not Configured / Manual / Not Assessed.</span>
          </label>
          <div className="mt-5 flex flex-wrap gap-3">
            <button type="button" className="btn-primary" disabled={!realOnly || actionLoading === "plan"} onClick={() => void buildPlan()}>
              {actionLoading === "plan" ? "Building..." : "Build worker plan"}
            </button>
            <button type="button" className="btn-secondary" disabled={!realOnly || actionLoading === "probe"} onClick={() => void runProbe()}>
              {actionLoading === "probe" ? "Probing..." : "Run version probe"}
            </button>
          </div>
          <div className="mt-6 rounded-2xl border border-white/10 bg-black/20 p-4">
            <p className="text-sm font-black text-white">Worker scope</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {status.phase_27_scope.map((item) => <span key={item} className="badge badge-cyan">{item}</span>)}
            </div>
          </div>
        </div>

        <div className="glass-tile p-6">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="section-label">Safety boundaries</p>
              <h2 className="mt-2 text-2xl font-black text-white">Worker rules before launch</h2>
            </div>
            <Link href="/engine-depth" className="btn-secondary">Engine depth</Link>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {Object.entries(status.safety_boundaries).map(([key, value]) => (
              <span key={key} className={`badge ${value ? "badge-green" : "badge-amber"}`}>{key.replaceAll("_", " ")}: {value ? "yes" : "no"}</span>
            ))}
          </div>
          <div className="mt-5 grid gap-3">
            {status.production_notes.map((note) => <p key={note} className="command-line text-sm text-slate-300"><span className="kbd-chip">NOTE</span>{note}</p>)}
          </div>
        </div>
      </div>

      <div>
        <p className="section-label">Worker tool matrix</p>
        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          {status.tools.map((tool) => (
            <ToolCard
              key={tool.key}
              tool={tool}
              checked={selected[tool.key] ?? true}
              onToggle={(checked) => setSelected((current) => ({ ...current, [tool.key]: checked }))}
            />
          ))}
        </div>
      </div>

      {plan ? (
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="glass-tile p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="section-label">Worker execution plan</p>
                <h2 className="mt-2 text-2xl font-black text-white">{plan.project_type}</h2>
              </div>
              <StatusPill status="Plan only" />
            </div>
            <div className="mt-5 space-y-4">
              {plan.steps.map((step) => (
                <div key={`${step.order}-${step.tool}`} className="rounded-3xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="kbd-chip">{step.order}</span>
                    <span className={`badge ${badgeClass(step.status)}`}>{step.status}</span>
                    <span className="text-sm font-black uppercase text-white">{step.tool}</span>
                  </div>
                  <pre className="mono mt-3 overflow-x-auto rounded-2xl bg-black/30 p-3 text-xs text-slate-300">{step.command_template}</pre>
                  <p className="mt-3 text-sm text-slate-400"><strong className="text-white">Evidence:</strong> {step.evidence_policy}</p>
                  <p className="mt-2 text-sm text-amber-100"><strong>Missing:</strong> {step.when_missing}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="glass-tile p-6">
            <p className="section-label">Queue design</p>
            <div className="mt-4 grid gap-3">
              {Object.entries(plan.queue_design).map(([key, value]) => (
                <p key={key} className="text-sm leading-6 text-slate-400"><strong className="text-white">{key.replaceAll("_", " ")}:</strong> {value}</p>
              ))}
            </div>
            <p className="section-label mt-6">Blocked actions</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {plan.blocked_actions.map((item) => <span key={item} className="badge badge-amber">{item}</span>)}
            </div>
          </div>
        </div>
      ) : null}

      {probe ? (
        <div className="glass-tile p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Real probe output</p>
              <h2 className="mt-2 text-2xl font-black text-white">Installed tool version checks</h2>
            </div>
            <StatusPill status={probe.probe_status} />
          </div>
          {probe.real_only_note ? <p className="mt-3 text-sm text-slate-400">{probe.real_only_note}</p> : null}
          {probe.note ? <p className="mt-3 text-sm text-amber-100">{probe.note}</p> : null}
          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            {Object.entries(probe.results).map(([tool, result]) => (
              <article key={tool} className="rounded-3xl border border-white/10 bg-black/20 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h3 className="text-lg font-black capitalize text-white">{tool}</h3>
                  <span className={`badge ${badgeClass(result.status)}`}>{result.status}</span>
                </div>
                {result.reason ? <p className="mt-3 text-sm text-amber-100">{result.reason}</p> : null}
                <pre className="mono mt-3 max-h-72 overflow-auto rounded-2xl bg-black/40 p-3 text-xs text-slate-300">{safeJson(result)}</pre>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
