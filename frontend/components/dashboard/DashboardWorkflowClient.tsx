"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { DashboardWorkflow } from "@/lib/types";
import { currentDashboardUser, fmtDate, scoreText } from "./DashboardDataHelpers";

type Props = {
  projectId?: string;
};

function riskTone(value: unknown) {
  const text = String(value || "").toLowerCase();
  if (text.includes("critical") || text.includes("high")) return "badge-red";
  if (text.includes("needed") || text.includes("partial") || text.includes("manual") || text.includes("not")) return "badge-amber";
  if (text.includes("strong") || text.includes("safe") || text.includes("pass")) return "badge-green";
  return "badge-cyan";
}

function metricValue(value: unknown) {
  if (typeof value === "number") return String(value);
  if (typeof value === "string" && value.trim()) return value;
  return "0";
}

export function DashboardWorkflowClient({ projectId }: Props) {
  const [workflow, setWorkflow] = useState<DashboardWorkflow | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);

    try {
      const ctx = await currentDashboardUser();
      const params = new URLSearchParams({ user_id: ctx.userId });
      if (projectId) params.set("project_id", projectId);
      const data = await apiGet<{ workflow: DashboardWorkflow }>(`/dashboard-workflow?${params.toString()}`, { headers: ctx.headers });
      setWorkflow(data.workflow);
    } catch (err) {
      setWorkflow(null);
      setError(err instanceof Error ? err.message : "Could not load workflow dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [projectId]);

  const summary = workflow?.summary || {};
  const maxTrendScore = useMemo(() => {
    const scores = workflow?.risk_trend.map((point) => (typeof point.score === "number" ? point.score : 0)) || [];
    return Math.max(100, ...scores);
  }, [workflow?.risk_trend]);

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="section-label">Dashboard workflow</p>
          <h1 className="mt-3 text-4xl font-black sm:text-5xl">
            {workflow?.scope.mode === "project" ? `${workflow.scope.project_name || "Project"} workflow` : "Projects, scans, reports, and findings in one command view."}
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400">
            This view is generated from saved records only. It never creates fake timelines, fake trend points, or fake finding tasks.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/dashboard" className="btn-secondary">Dashboard</Link>
          <Link href="/dashboard/projects" className="btn-secondary">Projects</Link>
          <Link href="/scanner/unified-url" className="btn-primary">Run scan</Link>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="stat-slab h-28 animate-pulse p-5" />
          ))}
        </div>
      ) : null}

      {error ? (
        <div className="rounded-3xl border border-red-400/25 bg-red-500/10 p-5 text-red-100">
          <p className="font-black">Workflow could not load.</p>
          <p className="mt-2 text-sm leading-6">{error}</p>
          <Link href="/auth/login" className="btn-primary mt-4 inline-flex">Login again</Link>
        </div>
      ) : null}

      {workflow && !error ? (
        <>
          <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Metric label="Projects" value={summary.projects} />
            <Metric label="Saved scans" value={summary.scans} />
            <Metric label="Saved reports" value={summary.reports} />
            <Metric label="Critical / high" value={summary.critical_high_count} tone="red" />
          </section>

          <section className="mt-6 grid gap-4 lg:grid-cols-[1fr_1.15fr]">
            <div className="glass-tile p-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="section-label">Risk trend</p>
                  <h2 className="mt-2 text-2xl font-black">Saved scan score movement</h2>
                </div>
                <span className={`badge ${riskTone(summary.score_bucket)}`}>{String(summary.score_bucket || "not_assessed")}</span>
              </div>

              {workflow.risk_trend.length ? (
                <div className="mt-6 flex h-56 items-end gap-2 rounded-3xl border border-white/10 bg-black/25 p-4">
                  {workflow.risk_trend.map((point) => {
                    const score = typeof point.score === "number" ? point.score : 0;
                    const height = Math.max(8, Math.round((score / maxTrendScore) * 100));
                    return (
                      <Link key={point.scan_id} href={point.href} className="group flex min-w-0 flex-1 flex-col items-center justify-end gap-2">
                        <span className="w-full rounded-t-xl bg-gradient-to-t from-cyan/70 to-purple-400/70 shadow-[0_0_18px_rgba(6,182,212,.18)] transition group-hover:from-cyan group-hover:to-cyan" style={{ height: `${height}%` }} />
                        <span className="mono max-w-full truncate text-[10px] text-slate-500">{point.module.slice(0, 6)}</span>
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <EmptyState title="No score trend yet" text="Run and save scans to build a real score trend. No placeholder chart is generated." />
              )}
            </div>

            <div className="glass-tile p-6">
              <p className="section-label">Module comparison</p>
              <h2 className="mt-2 text-2xl font-black">Which scan modules need attention?</h2>
              <div className="mt-5 grid gap-3">
                {workflow.module_comparison.length ? (
                  workflow.module_comparison.slice(0, 7).map((row) => (
                    <Link key={row.module} href={row.href} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-cyan/30 hover:bg-cyan/[0.05]">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <p className="font-black text-white">{row.module}</p>
                        <span className={`badge ${riskTone(row.latest_risk_label)}`}>{row.latest_risk_label}</span>
                      </div>
                      <div className="mt-3 grid gap-2 text-xs text-slate-400 sm:grid-cols-4">
                        <span>Latest {scoreText(row.latest_score)}</span>
                        <span>Average {scoreText(row.average_score)}</span>
                        <span>{row.findings_count} finding(s)</span>
                        <span>{row.scans_count} scan(s)</span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <EmptyState title="No module comparison yet" text="Saved scans will appear here grouped by module." />
                )}
              </div>
            </div>
          </section>

          <section className="mt-6 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
            <div className="glass-tile p-6">
              <p className="section-label">Project health</p>
              <h2 className="mt-2 text-2xl font-black">Project-level launch status</h2>
              <div className="mt-5 grid gap-3">
                {workflow.project_health.length ? (
                  workflow.project_health.slice(0, 8).map((project) => (
                    <Link key={project.project_id || project.name} href={project.href} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-cyan/30 hover:bg-cyan/[0.05]">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <p className="font-black text-white">{project.name}</p>
                        <span className={`badge ${riskTone(project.latest_risk_label)}`}>{project.latest_risk_label || "No scan yet"}</span>
                      </div>
                      <p className="mt-2 text-xs text-slate-500">{project.chain || "Chain not set"} · {project.website_url || "No URL"}</p>
                      <div className="mt-3 grid gap-2 text-xs text-slate-400 sm:grid-cols-4">
                        <span>{project.scans_count} scan(s)</span>
                        <span>{project.reports_count} report(s)</span>
                        <span>{scoreText(project.average_score)}</span>
                        <span>{project.critical_high_count} critical/high</span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <EmptyState title="No projects saved" text="Create a project or save a scan to start a real launch workflow." />
                )}
              </div>
            </div>

            <div className="glass-tile p-6">
              <p className="section-label">Finding workflow</p>
              <h2 className="mt-2 text-2xl font-black">Action queue from saved report payloads</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">{workflow.finding_workflow.note}</p>
              <div className="mt-5 grid gap-3">
                {workflow.finding_workflow.tasks.length ? (
                  workflow.finding_workflow.tasks.slice(0, 8).map((task) => (
                    <Link key={task.id} href={task.href} className="rounded-2xl border border-white/10 bg-black/25 p-4 transition hover:border-cyan/30 hover:bg-cyan/[0.05]">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <p className="font-black text-white">{task.title}</p>
                        <span className={`badge ${riskTone(task.severity)}`}>{task.severity}</span>
                      </div>
                      <p className="mt-2 text-xs text-slate-500">{task.module} · {task.status} · {fmtDate(task.created_at)}</p>
                      {task.recommendation ? <p className="mt-2 text-sm leading-6 text-slate-400">{task.recommendation}</p> : null}
                    </Link>
                  ))
                ) : (
                  <EmptyState title="No finding tasks yet" text="Saved scan/report payloads with real findings will appear here. No fake tasks are generated." />
                )}
              </div>
            </div>
          </section>

          <section className="mt-6 glass-tile p-6">
            <p className="section-label">Timeline</p>
            <h2 className="mt-2 text-2xl font-black">Latest real activity</h2>
            <div className="mt-5 grid gap-3">
              {workflow.timeline.length ? (
                workflow.timeline.slice(0, 12).map((event) => (
                  <Link key={`${event.type}-${event.id}`} href={event.href || "/dashboard"} className="flex gap-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-cyan/30 hover:bg-cyan/[0.05]">
                    <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl border border-cyan/20 bg-cyan/10 mono text-xs font-black text-cyan">{event.type.slice(0, 2).toUpperCase()}</span>
                    <span className="min-w-0">
                      <span className="block truncate font-black text-white">{event.title}</span>
                      <span className="mt-1 block truncate text-xs text-slate-500">{event.subtitle || "No extra details"} · {fmtDate(event.created_at)}</span>
                    </span>
                  </Link>
                ))
              ) : (
                <EmptyState title="No activity yet" text="Create projects, save scans, or save reports to build a real timeline." />
              )}
            </div>
          </section>

          <p className="mt-6 rounded-3xl border border-cyan/15 bg-cyan/[0.05] p-5 text-sm leading-7 text-slate-300">{workflow.real_only_note}</p>
        </>
      ) : null}
    </main>
  );
}

function Metric({ label, value, tone = "cyan" }: { label: string; value: unknown; tone?: "cyan" | "red" }) {
  return (
    <div className="stat-slab p-5">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className={`mt-2 text-3xl font-black ${tone === "red" ? "text-red-200" : "text-white"}`}>{metricValue(value)}</p>
    </div>
  );
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-black/20 p-6 text-center">
      <p className="font-black text-white">{title}</p>
      <p className="mt-2 text-sm leading-6 text-slate-500">{text}</p>
    </div>
  );
}
