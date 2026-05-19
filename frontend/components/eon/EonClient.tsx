"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { getCurrentUserId } from "@/lib/supabase";
import { CommandEmptyState, CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";

type EonNode = {
  id: string;
  label: string;
  type: string;
  required?: boolean;
  status: string;
  severity: string;
  confidence: number;
  evidence_count: number;
  alert_count?: number;
  last_checked_at: string;
  next_action: string;
  verify?: string;
};

type EonBlocker = {
  module: string;
  title: string;
  severity: string;
  reason: string;
  verify: string;
};

type EonTask = {
  id: string;
  module: string;
  title: string;
  priority: string;
  severity: string;
  action: string;
  verify: string;
  status: string;
  evidence_required: boolean;
  owner_suggestion: string;
  safe_boundary: string;
};

type EvidenceEntry = {
  id: string;
  kind: string;
  title: string;
  source: string;
  project_id?: string | null;
  module?: string | null;
  evidence_hash: string;
  captured_at: string;
  integrity_note: string;
};

type RiskGraphResponse = {
  ok: boolean;
  summary: {
    project_count: number;
    scan_count: number;
    report_count: number;
    sentinel_alert_count: number;
    required_evidence_coverage: number;
    overall_launch_confidence: number;
    launch_blockers: number;
  };
  nodes: EonNode[];
  edges: Array<{ from: string; to: string; label: string }>;
  launch_blockers: EonBlocker[];
  next_best_action: EonBlocker;
  safe_boundary: string;
  real_only_note: string;
};

type FixPlanResponse = {
  ok: boolean;
  tasks: EonTask[];
  counts: Record<string, number>;
  next_best_action: EonBlocker;
  workflow_note: string;
  real_only_note: string;
};

type LedgerResponse = {
  ok: boolean;
  entries: EvidenceEntry[];
  counts: Record<string, number>;
  real_only_note: string;
};

function severityClass(severity: string) {
  const clean = severity.toLowerCase();
  if (clean === "critical") return "sev-critical";
  if (clean === "high") return "sev-high";
  if (clean === "medium") return "sev-medium";
  if (clean === "low") return "sev-low";
  if (clean === "safe") return "sev-safe";
  return "sev-info";
}

function nodeBorder(severity: string) {
  const clean = severity.toLowerCase();
  if (clean === "critical") return "border-red-400/35 bg-red-500/10";
  if (clean === "high") return "border-orange-400/30 bg-orange-500/10";
  if (clean === "medium") return "border-yellow-300/25 bg-yellow-300/10";
  if (clean === "low") return "border-emerald-400/25 bg-emerald-500/10";
  return "border-white/10 bg-white/[0.03]";
}

function StatCard({ label, value, note }: { label: string; value: string | number; note?: string }) {
  return (
    <div className="stat-slab p-5">
      <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-black text-white">{value}</p>
      {note ? <p className="mt-2 text-xs leading-5 text-slate-400">{note}</p> : null}
    </div>
  );
}

function PageShell({ children, projectId }: { children: React.ReactNode; projectId?: string }) {
  return (
    <main className="relative overflow-hidden">
      <section className="trust-shell border-b border-white/10">
        <div className="pointer-events-none absolute inset-0 w3g-cyber-grid opacity-60" />
        <div className="relative mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
          <p className="section-label">Web3Guard EON</p>
          <h1 className="mt-4 max-w-5xl text-4xl font-black sm:text-6xl">
            Risk Graph + Autonomous Fix Plan
          </h1>
          <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
            EON converts stored scans, reports, Sentinel alerts, and evidence ledger records into a project risk graph, launch blocker queue, and defensive fix plan. It never invents evidence or claims a certified audit.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link href="/eon" className="btn-secondary">EON overview</Link>
            <Link href="/sentinel" className="btn-secondary">Sentinel</Link>
            <Link href="/dashboard/workflow" className="btn-secondary">Workflow board</Link>
            <Link href="/scanner/unified-url" className="btn-primary">Run scan</Link>
          </div>
          {projectId ? <p className="mt-4 break-all text-xs text-slate-500">Project scope: {projectId}</p> : null}
        </div>
      </section>
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">{children}</div>
    </main>
  );
}

export function EonClient({ projectId }: { projectId?: string }) {
  const [userId, setUserId] = useState("local-demo-user");
  const [graph, setGraph] = useState<RiskGraphResponse | null>(null);
  const [fixPlan, setFixPlan] = useState<FixPlanResponse | null>(null);
  const [ledger, setLedger] = useState<LedgerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const taskSummary = useMemo(() => {
    const tasks = fixPlan?.tasks || [];
    return tasks.reduce<Record<string, number>>((acc, task) => {
      const key = task.priority.split(" ")[0] || "P4";
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
  }, [fixPlan]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const resolvedUserId = await getCurrentUserId().catch(() => "local-demo-user");
      setUserId(resolvedUserId);
      const suffix = `user_id=${encodeURIComponent(resolvedUserId)}${projectId ? `&project_id=${encodeURIComponent(projectId)}` : ""}`;
      const [graphData, fixPlanData, ledgerData] = await Promise.all([
        apiGet<RiskGraphResponse>(`/eon/risk-graph?${suffix}`),
        apiGet<FixPlanResponse>(`/eon/fix-plan?${suffix}`),
        apiGet<LedgerResponse>(`/eon/evidence-ledger?${suffix}`),
      ]);
      setGraph(graphData);
      setFixPlan(fixPlanData);
      setLedger(ledgerData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "EON data load failed.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [projectId]);

  if (loading) {
    return (
      <PageShell projectId={projectId}>
        <CommandLoadingState label="Building EON risk graph from stored evidence..." />
      </PageShell>
    );
  }

  return (
    <PageShell projectId={projectId}>
      {error ? <CommandNotice tone="danger" title="EON data issue" text={error} /> : null}

      <section className="grid gap-4 md:grid-cols-4">
        <StatCard label="Launch confidence" value={`${graph?.summary.overall_launch_confidence ?? 0}%`} note="Derived from assessed evidence only." />
        <StatCard label="Evidence coverage" value={`${graph?.summary.required_evidence_coverage ?? 0}%`} note="Required modules with stored evidence." />
        <StatCard label="Launch blockers" value={graph?.summary.launch_blockers ?? 0} note="Critical/high or required missing evidence." />
        <StatCard label="Evidence ledger" value={ledger?.entries.length ?? 0} note="Hashed captured records." />
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="glass-tile p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-2xl font-black">Project risk graph</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">Node status is generated from stored project, scan, report, and Sentinel alert records only.</p>
            </div>
            <span className="badge badge-cyan">User: {userId}</span>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {(graph?.nodes || []).map((node) => (
              <div key={node.id} className={`rounded-2xl border p-4 ${nodeBorder(node.severity)}`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-black text-white">{node.label}</p>
                    <p className="mt-1 text-xs text-slate-500">{node.status} · evidence {node.evidence_count}</p>
                  </div>
                  <span className={severityClass(node.severity)}>{node.severity}</span>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-cyan shadow-[0_0_16px_rgba(6,182,212,.55)]" style={{ width: `${Math.max(0, Math.min(100, node.confidence || 0))}%` }} />
                </div>
                <p className="mt-3 text-xs leading-5 text-slate-400">{node.next_action}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-6">
          <div className="glass-tile p-6">
            <h2 className="text-2xl font-black">Next best action</h2>
            {graph?.next_best_action ? (
              <div className="mt-4 rounded-2xl border border-cyan/20 bg-cyan/[0.05] p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <p className="font-black text-white">{graph.next_best_action.title}</p>
                  <span className={severityClass(graph.next_best_action.severity)}>{graph.next_best_action.severity}</span>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{graph.next_best_action.reason}</p>
                <p className="mt-3 text-xs leading-5 text-cyan">Verify: {graph.next_best_action.verify}</p>
              </div>
            ) : (
              <CommandEmptyState title="No action available" text="Run scans or save reports to build real next actions." />
            )}
          </div>

          <div className="glass-tile p-6">
            <h2 className="text-2xl font-black">Launch blockers</h2>
            <div className="mt-4 grid gap-3">
              {graph?.launch_blockers.length ? graph.launch_blockers.slice(0, 8).map((blocker) => (
                <div key={`${blocker.module}-${blocker.title}`} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <p className="font-black text-white">{blocker.title}</p>
                    <span className={severityClass(blocker.severity)}>{blocker.severity}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{blocker.reason}</p>
                </div>
              )) : <CommandEmptyState title="No launch blockers from stored records" text="Keep re-running scans and verifying reports before launch." />}
            </div>
          </div>
        </section>
      </div>

      <section className="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="glass-tile p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-2xl font-black">Autonomous defensive fix plan</h2>
            <div className="flex flex-wrap gap-2">
              {Object.entries(taskSummary).map(([key, value]) => <span key={key} className="badge badge-amber">{key}: {value}</span>)}
            </div>
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-400">Every task must be closed with new evidence. This is not exploit automation or an audit certification workflow.</p>
          <div className="mt-5 grid gap-3">
            {fixPlan?.tasks.length ? fixPlan.tasks.slice(0, 14).map((task) => (
              <div key={task.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-black text-white">{task.title}</p>
                    <p className="mt-1 text-xs text-slate-500">{task.priority} · {task.module} · {task.status}</p>
                  </div>
                  <span className={severityClass(task.severity)}>{task.severity}</span>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-400">{task.action}</p>
                <p className="mt-3 text-xs leading-5 text-cyan">Verify: {task.verify}</p>
              </div>
            )) : <CommandEmptyState title="No fix tasks yet" text="EON does not generate fake work. Run scans, save reports, or ingest advisories to produce real tasks." />}
          </div>
        </div>

        <div className="glass-tile p-6">
          <h2 className="text-2xl font-black">Evidence ledger</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">Each entry has a hash for integrity of the captured payload. It does not prove the project is safe.</p>
          <div className="mt-5 grid gap-3">
            {ledger?.entries.length ? ledger.entries.slice(0, 14).map((entry) => (
              <div key={entry.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-black text-white">{entry.title}</p>
                    <p className="mt-1 text-xs text-slate-500">{entry.kind} · {entry.source} · {entry.module || "global"}</p>
                  </div>
                  <span className="badge badge-cyan">hash</span>
                </div>
                <p className="mt-3 break-all mono text-[11px] leading-5 text-cyan/80">{entry.evidence_hash}</p>
                <p className="mt-3 text-xs leading-5 text-slate-500">{entry.integrity_note}</p>
              </div>
            )) : <CommandEmptyState title="No evidence entries yet" text="Save a project, run a scan, or generate a report to create ledger entries." />}
          </div>
        </div>
      </section>

      <CommandNotice tone="info" title="EON safety boundary" text={graph?.safe_boundary || "Defensive launch-readiness workflow only."} />
    </PageShell>
  );
}
