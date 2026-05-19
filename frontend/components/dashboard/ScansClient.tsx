"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { ScanHistoryRecord } from "@/lib/types";
import { currentDashboardUser, fmtDate, scoreText } from "./DashboardDataHelpers";

export function ScansClient() {
  const [scans, setScans] = useState<ScanHistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const ctx = await currentDashboardUser();
        const data = await apiGet<{ scans: ScanHistoryRecord[] }>(`/scan-history?user_id=${encodeURIComponent(ctx.userId)}&limit=100`, { headers: ctx.headers });
        setScans(data.scans);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load scans");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Dashboard scan history</p>
          <h1 className="mt-2 text-4xl font-black">Scan history</h1>
          <p className="mt-3 max-w-3xl text-slate-400">Only scans explicitly saved from scanner or dashboard APIs appear here. No demo rows are generated.</p>
        </div>
        <Link className="btn-primary" href="/scanner/unified-url">Run scan</Link>
      </div>
      {loading && <LoadingPanel />}
      {error && <p className="rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}
      <div className="grid gap-4 lg:grid-cols-2">
        {scans.map((scan) => (
          <Link key={scan.id} href={`/dashboard/scans/${scan.id}`} className="status-node block p-5 transition hover:-translate-y-0.5 hover:border-cyan/35 hover:bg-cyan/[0.05]">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-cyan">{scan.module}</p>
                <h2 className="mt-2 text-xl font-black">{scan.project_name || "Unnamed project"}</h2>
              </div>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm font-bold text-white">{scoreText(scan.score)}</span>
            </div>
            <p className="mt-3 text-sm text-slate-400">{scan.risk_label || "No risk label"} • {scan.findings_count} finding(s) • {scan.status || "saved"}</p>
            <p className="mt-2 text-xs text-slate-500">{fmtDate(scan.created_at)}</p>
          </Link>
        ))}
      </div>
      {!loading && scans.length === 0 && !error && <EmptyScans />}
    </main>
  );
}


function LoadingPanel() {
  return (
    <div className="tool-console mb-6 p-5">
      <div className="relative z-[1] grid gap-3">
        <div className="skeleton-line h-4 w-48" />
        <div className="skeleton-line h-4 w-full" />
        <div className="skeleton-line h-4 w-2/3" />
      </div>
    </div>
  );
}

function EmptyScans() {
  return (
    <div className="tool-console p-8 text-center">
      <div className="relative z-[1] mx-auto max-w-md">
        <div className="empty-state-orb mx-auto mono text-cyan">SCAN</div>
        <h2 className="mt-6 text-2xl font-black text-white">No saved scans yet</h2>
        <p className="mt-3 text-sm leading-6 text-slate-400">Run a real scan and save it to your dashboard. The list will stay empty until real data exists.</p>
        <Link className="btn-primary mt-5" href="/scanner/unified-url">Run first scan</Link>
      </div>
    </div>
  );
}
