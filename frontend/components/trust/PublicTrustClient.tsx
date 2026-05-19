"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiGet } from "@/lib/api";

type PublicTrustProject = {
  id: string;
  name: string;
  website_url?: string | null;
  project_type?: string | null;
  chain?: string | null;
  assessed_modules: number;
  total_modules: number;
  latest_report_hash?: string | null;
  public_path: string;
  status: string;
};

type ProjectsResponse = {
  ok: boolean;
  user_id: string;
  items: PublicTrustProject[];
  empty_state: string;
  real_only_note: string;
};

const statusClass: Record<string, string> = {
  ready_to_preview: "badge-green",
  needs_evidence: "badge-amber",
};

export function PublicTrustClient() {
  const [userId, setUserId] = useState("");
  const [data, setData] = useState<ProjectsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canLoad = userId.trim().length > 0;

  async function loadProjects() {
    const cleanUserId = userId.trim();
    if (!cleanUserId) {
      setError("Enter your dashboard user ID to generate trust-page previews from real stored records.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<ProjectsResponse>(`/public-trust/projects?user_id=${encodeURIComponent(cleanUserId)}`);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load public trust projects.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <div className="glass-tile p-6 sm:p-8">
          <p className="section-label">Public trust generator</p>
          <h1 className="mt-3 text-4xl font-black tracking-[-0.06em] sm:text-5xl">
            Generate shareable launch-readiness pages without fake audit claims.
          </h1>
          <p className="mt-5 text-sm leading-7 text-slate-400">
            Public trust pages show assessed modules, Not Assessed modules, report hash status, fix workflow summary, Sentinel alerts, and evidence ledger references from stored project data only.
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <span className="badge badge-green">Pre-audit readiness only</span>
            <span className="badge badge-cyan">No certified audit claim</span>
            <span className="badge badge-amber">Not Assessed stays visible</span>
            <span className="badge badge-purple">Evidence hashes included</span>
          </div>
          <div className="mt-6 rounded-2xl border border-amber-400/20 bg-amber-500/10 p-4 text-sm leading-6 text-amber-100">
            <strong>Safe wording:</strong> “Pre-audit launch-readiness reviewed.” Never use “audited,” “certified secure,” or “100% secure” unless a separate verified process exists.
          </div>
        </div>

        <div className="auth-shell p-5 sm:p-6">
          <div className="relative z-[1]">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-cyan">Load real projects</p>
            <label className="mt-4 grid gap-2 text-sm font-bold text-slate-300">
              Dashboard user ID
              <input
                className="input"
                value={userId}
                onChange={(event) => setUserId(event.target.value)}
                placeholder="Paste user_id from dashboard context"
              />
            </label>
            <button className="btn-primary mt-4" onClick={() => void loadProjects()} disabled={!canLoad || loading}>
              {loading ? "Loading..." : "Load trust pages"}
            </button>
            <p className="mt-4 text-xs leading-5 text-slate-500">
              This preview uses your stored project records. It does not publish anything automatically and does not send disclosure emails.
            </p>
            {error ? <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p> : null}
          </div>
        </div>
      </section>

      <section className="mt-10">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="section-label">Project trust pages</p>
            <h2 className="mt-2 text-3xl font-black">Stored projects ready for public summary.</h2>
          </div>
          <Link href="/report/verify" className="btn-secondary">Verify report hash</Link>
        </div>

        {!data && !loading ? (
          <div className="glass-tile p-6 text-sm leading-7 text-slate-400">
            Enter a user ID to list trust-page previews. No demo projects are generated.
          </div>
        ) : null}

        {data && data.items.length === 0 ? (
          <div className="glass-tile p-6 text-sm leading-7 text-slate-400">
            {data.empty_state}
          </div>
        ) : null}

        {data ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {data.items.map((project) => (
              <Link key={project.id} href={project.public_path} className="glass-tile group block p-5 transition hover:-translate-y-1 hover:border-cyan/25">
                <div className="flex items-start justify-between gap-3">
                  <div className="grid h-12 w-12 place-items-center rounded-2xl border border-cyan/20 bg-cyan/10 mono text-cyan">TG</div>
                  <span className={`badge ${statusClass[project.status] || "badge-cyan"}`}>{project.status.replace(/_/g, " ")}</span>
                </div>
                <h3 className="mt-4 text-xl font-black text-white">{project.name}</h3>
                <p className="mt-2 text-sm text-slate-400">{project.project_type || "Project type not set"} · {project.chain || "Chain not set"}</p>
                <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                    <p className="text-slate-500">Assessed</p>
                    <p className="mt-1 text-lg font-black text-white">{project.assessed_modules}/{project.total_modules}</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                    <p className="text-slate-500">Report hash</p>
                    <p className="mt-1 truncate font-black text-white">{project.latest_report_hash ? "Available" : "Missing"}</p>
                  </div>
                </div>
                <p className="mt-5 text-sm font-bold text-cyan opacity-80 transition group-hover:translate-x-1 group-hover:opacity-100">Open public trust preview →</p>
              </Link>
            ))}
          </div>
        ) : null}

        {data?.real_only_note ? (
          <p className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-xs leading-6 text-slate-500">{data.real_only_note}</p>
        ) : null}
      </section>
    </main>
  );
}

function labelClass(status: string) {
  if (status === "reviewed") return "badge-green";
  if (status === "needs_fix") return "badge-red";
  if (status === "evidence_needed") return "badge-amber";
  return "badge-cyan";
}

export function PublicTrustProjectClient({ projectId }: { projectId: string }) {
  const [userId, setUserId] = useState("");
  const [page, setPage] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get("user_id") || "";
    if (fromQuery) setUserId(fromQuery);
  }, []);

  async function loadPage(nextUserId = userId) {
    const cleanUserId = nextUserId.trim();
    if (!cleanUserId) {
      setError("Enter user_id to load this project trust page from real stored records.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<any>(`/public-trust/project/${encodeURIComponent(projectId)}?user_id=${encodeURIComponent(cleanUserId)}`);
      setPage(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load trust page.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get("user_id") || "";
    if (fromQuery) void loadPage(fromQuery);
  }, [projectId]);

  const publicSummary = useMemo(() => page?.summary || {}, [page]);

  return (
    <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
        <div className="quantum-stage p-6 sm:p-8">
          <p className="section-label">Public trust page</p>
          <h1 className="mt-3 text-4xl font-black tracking-[-0.06em] sm:text-6xl">
            {page?.project?.name || "Project readiness preview"}
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400">
            {page?.public_wording || "Pre-audit launch-readiness reviewed"}. This page summarizes stored evidence and limitations. It is not a certified audit and not a guarantee of security.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            <span className="badge badge-green">{page?.public_wording || "Pre-audit readiness"}</span>
            <span className="badge badge-amber">Not a certified audit</span>
            <span className="badge badge-cyan">Evidence-first</span>
            <span className="badge badge-purple">Hash referenced</span>
          </div>
        </div>

        <div className="auth-shell p-5 sm:p-6">
          <div className="relative z-[1]">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-cyan">Load preview</p>
            <label className="mt-4 grid gap-2 text-sm font-bold text-slate-300">
              User ID
              <input className="input" value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="user_id" />
            </label>
            <button className="btn-primary mt-4" onClick={() => void loadPage()} disabled={!userId.trim() || loading}>
              {loading ? "Loading..." : "Load trust page"}
            </button>
            {error ? <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p> : null}
          </div>
        </div>
      </section>

      {page ? (
        <>
          <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <Metric label="Assessed" value={publicSummary.assessed_modules ?? 0} />
            <Metric label="Not Assessed" value={publicSummary.not_assessed_modules ?? 0} />
            <Metric label="Needs Attention" value={publicSummary.needs_attention_modules ?? 0} />
            <Metric label="Evidence" value={publicSummary.evidence_entries ?? 0} />
            <Metric label="Open Tasks" value={publicSummary.open_fix_tasks ?? 0} />
          </section>

          <section className="mt-8 grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="glass-tile p-6">
              <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="section-label">Module coverage</p>
                  <h2 className="mt-2 text-2xl font-black">Assessed vs Not Assessed</h2>
                </div>
                <span className="badge badge-amber">Limitations visible</span>
              </div>
              <div className="grid gap-3">
                {page.modules.map((module: any) => (
                  <div key={module.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="font-black text-white">{module.label}</p>
                        <p className="mt-1 text-sm leading-6 text-slate-400">{module.description}</p>
                      </div>
                      <span className={`badge ${labelClass(module.status)}`}>{module.public_label}</span>
                    </div>
                    <p className="mt-3 text-xs text-slate-500">Evidence entries: {module.evidence_count}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-6">
              <div className="glass-tile p-6">
                <p className="section-label">Latest report</p>
                <h2 className="mt-2 text-2xl font-black">Hash verification</h2>
                <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 p-4 text-sm leading-6 text-slate-300">
                  <p><strong className="text-white">Report ID:</strong> {page.latest_report.report_id || "Not generated"}</p>
                  <p className="break-all"><strong className="text-white">Report hash:</strong> {page.latest_report.report_hash || "Missing"}</p>
                  <p><strong className="text-white">Status:</strong> {page.latest_report.status}</p>
                </div>
                <p className="mt-3 text-xs leading-5 text-slate-500">{page.latest_report.integrity_note}</p>
                <Link href="/report/verify" className="btn-secondary mt-4">Open verifier</Link>
              </div>

              <div className="glass-tile p-6">
                <p className="section-label">Responsible disclosure</p>
                <h2 className="mt-2 text-2xl font-black">Disclosure-ready path</h2>
                <p className="mt-3 text-sm leading-6 text-slate-400">{page.responsible_disclosure.public_note}</p>
                <Link href={page.responsible_disclosure.recommended_link} className="btn-secondary mt-4">Open disclosure draft</Link>
              </div>
            </div>
          </section>

          <section className="mt-8 grid gap-6 lg:grid-cols-2">
            <div className="glass-tile p-6">
              <p className="section-label">Fix status</p>
              <h2 className="mt-2 text-2xl font-black">Open action queue</h2>
              <div className="mt-4 grid gap-3">
                {page.fix_status.open_tasks.length ? page.fix_status.open_tasks.map((task: any) => (
                  <div key={task.id || task.title} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <p className="font-black text-white">{task.title}</p>
                    <p className="mt-1 text-sm text-slate-400">{task.module || "workflow"} · {task.status}</p>
                  </div>
                )) : <p className="text-sm text-slate-500">No open stored fix tasks found. Do not show fake fixed status.</p>}
              </div>
            </div>

            <div className="glass-tile p-6">
              <p className="section-label">Evidence ledger</p>
              <h2 className="mt-2 text-2xl font-black">Integrity references</h2>
              <div className="mt-4 grid gap-3">
                {page.evidence_ledger_summary.entries.length ? page.evidence_ledger_summary.entries.slice(0, 8).map((entry: any) => (
                  <div key={entry.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <p className="font-black text-white">{entry.title}</p>
                    <p className="mt-1 break-all mono text-xs text-slate-500">{entry.evidence_hash}</p>
                  </div>
                )) : <p className="text-sm text-slate-500">No evidence ledger entries yet.</p>}
              </div>
            </div>
          </section>

          <section className="mt-8 glass-tile p-6">
            <p className="section-label">Share card</p>
            <h2 className="mt-2 text-2xl font-black">Safe public wording</h2>
            <p className="mt-3 text-lg font-black text-white">{page.share_card.title}</p>
            <p className="mt-2 text-sm text-slate-400">{page.share_card.subtitle}</p>
            <ul className="mt-4 grid gap-2 text-sm text-slate-300 sm:grid-cols-2">
              {page.share_card.bullets.map((bullet: string) => <li key={bullet}>• {bullet}</li>)}
            </ul>
            <p className="mt-5 rounded-2xl border border-red-400/20 bg-red-500/10 p-4 text-xs leading-6 text-red-100">
              Blocked wording: {page.blocked_claims.join(", ")}
            </p>
          </section>
        </>
      ) : null}
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat-slab p-4">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-black text-white">{value}</p>
    </div>
  );
}
