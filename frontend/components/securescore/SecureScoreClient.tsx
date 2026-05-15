"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { SecureScoreOverview } from "@/lib/types";
import { currentDashboardUser, fmtDate, scoreText } from "@/components/dashboard/DashboardDataHelpers";

export function SecureScoreClient() {
  const [overview, setOverview] = useState<SecureScoreOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const ctx = await currentDashboardUser();
        const data = await apiGet<{ overview: SecureScoreOverview }>(`/securescore/overview?user_id=${encodeURIComponent(ctx.userId)}`, { headers: ctx.headers });
        setOverview(data.overview);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load SecureScore dashboard");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const summary = overview?.summary;
  const score = summary?.average_score ?? null;
  const circumference = 2 * Math.PI * 54;
  const progress = score === null ? 0 : Math.max(0, Math.min(100, score));

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Phase 10 SecureScore Pro</p>
          <h1 className="mt-2 text-4xl font-black">SecureScore dashboard</h1>
          <p className="mt-3 max-w-3xl text-slate-400">Built from real saved scans only. No fake scan history, fake fixes, fake audit status, or fake score trend is generated.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link className="btn-secondary" href="/dashboard/findings">Findings workflow</Link>
          <Link className="btn-secondary" href="/dashboard/scans">Scan history</Link>
          <Link className="btn-primary" href="/scanner/unified-url">Run scan</Link>
        </div>
      </div>

      {loading && <p className="text-slate-400">Loading SecureScore...</p>}
      {error && <p className="rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}

      {overview && (
        <>
          <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="card p-6">
              <div className="flex flex-wrap items-center gap-6">
                <svg width="150" height="150" viewBox="0 0 140 140" role="img" aria-label="Average SecureScore">
                  <circle cx="70" cy="70" r="54" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="14" />
                  <circle cx="70" cy="70" r="54" fill="none" stroke="currentColor" strokeWidth="14" strokeLinecap="round" className="text-cyan" strokeDasharray={circumference} strokeDashoffset={circumference - (progress / 100) * circumference} transform="rotate(-90 70 70)" />
                  <text x="70" y="68" textAnchor="middle" className="fill-white text-3xl font-black">{scoreText(score)}</text>
                  <text x="70" y="92" textAnchor="middle" className="fill-slate-400 text-[10px] uppercase tracking-widest">avg score</text>
                </svg>
                <div className="min-w-0 flex-1">
                  <h2 className="text-2xl font-black">{summary?.risk_label}</h2>
                  <p className="mt-3 text-sm text-slate-400">{overview.real_only_note}</p>
                  <p className="mt-3 rounded-2xl border border-amber-400/20 bg-amber-500/10 p-3 text-xs text-amber-100">Auto-fix status: {overview.auto_fix_status.replaceAll("_", " ")}. Bugs are explained and tracked; code is not automatically changed without user approval.</p>
                </div>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <Stat label="Projects" value={summary?.projects ?? 0} />
              <Stat label="Saved scans" value={summary?.saved_scans ?? 0} />
              <Stat label="All findings" value={summary?.findings ?? 0} />
              <Stat label="Open findings" value={summary?.open_findings ?? 0} />
              <Stat label="Open critical/high" value={summary?.open_critical_high ?? 0} />
              <Stat label="Risk label" value={summary?.risk_label ?? "Not scored"} />
            </div>
          </section>

          <section className="mt-8 grid gap-6 lg:grid-cols-2">
            <Breakdown title="Severity breakdown" data={overview.severity_breakdown} />
            <Breakdown title="Workflow breakdown" data={overview.workflow_breakdown} />
          </section>

          <section className="mt-8 card p-6">
            <h2 className="text-2xl font-black">Module scorecards</h2>
            <div className="mt-5 grid gap-4 lg:grid-cols-3">
              {overview.module_scorecards.length === 0 ? <p className="text-sm text-slate-500">No saved module scans yet.</p> : overview.module_scorecards.map((card) => (
                <Link key={card.module} href={`/dashboard/scans/${card.latest_scan_id}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 transition hover:border-cyan/40">
                  <p className="text-xs font-bold uppercase tracking-wide text-cyan">{card.label}</p>
                  <div className="mt-3 flex items-center justify-between gap-3"><h3 className="text-xl font-black">{scoreText(card.average_score ?? null)}</h3><span className="text-xs text-slate-400">{card.scans_count} scan(s)</span></div>
                  <p className="mt-2 text-sm text-slate-400">{card.risk_label}</p>
                  <p className="mt-2 text-xs text-slate-500">{card.findings_count} findings • {card.critical_high_count} critical/high</p>
                </Link>
              ))}
            </div>
          </section>

          <section className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="card p-6">
              <h2 className="text-2xl font-black">Top open findings</h2>
              <div className="mt-5 grid gap-3">
                {overview.top_open_findings.length === 0 ? <p className="text-sm text-slate-500">No open saved findings yet.</p> : overview.top_open_findings.map((finding) => (
                  <Link key={`${finding.scan_id}-${finding.id}`} href={`/dashboard/findings?scan=${finding.scan_id}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-cyan/40">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="font-bold text-white">{finding.title}</p>
                      <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold uppercase text-slate-200">{finding.severity}</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{finding.module_label || finding.module} • {finding.workflow_status} • {finding.project_name || "Unnamed project"}</p>
                  </Link>
                ))}
              </div>
            </div>
            <div className="card p-6">
              <h2 className="text-2xl font-black">Score trend</h2>
              <div className="mt-5 grid gap-3">
                {overview.score_trend.length === 0 ? <p className="text-sm text-slate-500">No scored scans yet.</p> : overview.score_trend.map((point) => (
                  <Link key={point.scan_id} href={`/dashboard/scans/${point.scan_id}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <div className="flex justify-between gap-3"><p className="font-bold text-white">{point.module}</p><p className="font-black text-cyan">{scoreText(point.score ?? null)}</p></div>
                    <p className="mt-1 text-xs text-slate-500">{fmtDate(point.created_at)} • {point.risk_label}</p>
                  </Link>
                ))}
              </div>
            </div>
          </section>
        </>
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return <div className="card p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 truncate text-lg font-black text-white">{value}</p></div>;
}

function Breakdown({ title, data }: { title: string; data: Record<string, number> }) {
  const max = Math.max(1, ...Object.values(data));
  return <div className="card p-6"><h2 className="text-2xl font-black">{title}</h2><div className="mt-5 grid gap-3">{Object.entries(data).map(([key, value]) => <div key={key}><div className="flex justify-between text-sm"><span className="capitalize text-slate-300">{key.replaceAll("_", " ")}</span><span className="font-bold text-white">{value}</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-cyan" style={{ width: `${(value / max) * 100}%` }} /></div></div>)}</div></div>;
}
