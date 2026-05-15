"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPatch } from "@/lib/api";
import type { ProjectDetail } from "@/lib/types";
import { currentDashboardUser, fmtDate, scoreText } from "./DashboardDataHelpers";

export function ProjectDetailClient({ projectId }: { projectId: string }) {
  const [detail, setDetail] = useState<ProjectDetail | null>(null);
  const [description, setDescription] = useState("");
  const [ownerContact, setOwnerContact] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const ctx = await currentDashboardUser();
      const data = await apiGet<{ detail: ProjectDetail }>(`/projects/${projectId}?user_id=${encodeURIComponent(ctx.userId)}`, { headers: ctx.headers });
      setDetail(data.detail);
      setDescription(data.detail.project.description || "");
      setOwnerContact(data.detail.project.owner_contact || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load project");
    } finally {
      setLoading(false);
    }
  }

  async function saveNotes() {
    if (!detail) return;
    setMessage(null);
    setError(null);
    try {
      const ctx = await currentDashboardUser();
      await apiPatch(`/projects/${projectId}?user_id=${encodeURIComponent(ctx.userId)}`, { description, owner_contact: ownerContact }, { headers: ctx.headers });
      setMessage("Project notes updated as a real saved record.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update project");
    }
  }

  useEffect(() => { void load(); }, [projectId]);

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <Link className="text-sm font-bold text-cyan" href="/dashboard/projects">← Back to projects</Link>
      {loading && <p className="mt-8 text-slate-400">Loading...</p>}
      {error && <p className="mt-6 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}
      {detail && (
        <>
          <div className="mt-6 flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Project detail</p>
              <h1 className="mt-2 text-4xl font-black">{detail.project.name}</h1>
              <p className="mt-3 text-slate-400">{detail.project.chain || "Chain not set"} • {detail.project.project_type || "Project type not set"}</p>
            </div>
            <Link className="btn-primary" href="/scanner/unified-url">Run new scan</Link>
          </div>

          <section className="mt-8 grid gap-4 md:grid-cols-4">
            <Stat label="Scans" value={detail.totals.scans ?? 0} />
            <Stat label="Reports" value={detail.totals.reports ?? 0} />
            <Stat label="Critical/High" value={detail.totals.critical_high_findings ?? 0} />
            <Stat label="Avg score" value={scoreText(typeof detail.totals.average_score === "number" ? detail.totals.average_score : null)} />
          </section>

          <section className="mt-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
            <div className="card p-6">
              <h2 className="text-2xl font-black">Project notes</h2>
              <input className="input mt-4" value={ownerContact} onChange={(e) => setOwnerContact(e.target.value)} placeholder="Owner contact / Telegram / email" />
              <textarea className="textarea mt-4 min-h-[160px]" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Pre-audit notes, launch context, manual review notes..." />
              <button className="btn-secondary mt-4" onClick={saveNotes}>Save notes</button>
              {message && <p className="mt-3 text-sm text-emerald-200">{message}</p>}
            </div>
            <div className="card p-6">
              <h2 className="text-2xl font-black">Inputs</h2>
              <div className="mt-4 space-y-3 text-sm text-slate-300">
                <p><span className="text-slate-500">Website:</span> {detail.project.website_url || "Not provided"}</p>
                <p><span className="text-slate-500">Contract:</span> {detail.project.contract_address || "Not provided"}</p>
                <p><span className="text-slate-500">GitHub:</span> {detail.project.github_repo_url || "Not provided"}</p>
                <p><span className="text-slate-500">Created:</span> {fmtDate(detail.project.created_at)}</p>
              </div>
            </div>
          </section>

          <section className="mt-8 grid gap-6 lg:grid-cols-2">
            <List title="Project scans" empty="No scans saved for this project." rows={detail.scans.map((s) => ({ href: `/dashboard/scans/${s.id}`, title: `${s.module} • ${scoreText(s.score)}`, meta: `${s.risk_label || "No risk"} • ${s.findings_count} finding(s)` }))} />
            <List title="Project reports" empty="No reports saved for this project." rows={detail.reports.map((r) => ({ href: `/dashboard/reports/${r.id}`, title: r.title, meta: `${r.risk_label || "No risk"} • ${r.status || "saved"}` }))} />
          </section>
        </>
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return <div className="card p-5"><p className="text-xs uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-black text-white">{value}</p></div>;
}

function List({ title, empty, rows }: { title: string; empty: string; rows: Array<{ href: string; title: string; meta: string }> }) {
  return <div className="card p-6"><h3 className="text-xl font-black">{title}</h3><div className="mt-4 grid gap-3">{rows.length ? rows.map((r) => <Link key={r.href} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-cyan/40" href={r.href}><p className="font-bold text-white">{r.title}</p><p className="mt-1 text-xs text-slate-400">{r.meta}</p></Link>) : <p className="text-sm text-slate-500">{empty}</p>}</div></div>;
}
