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
          <p className="mt-3 max-w-3xl text-slate-400">Only scans explicitly saved from scanner/dashboard APIs appear here.</p>
        </div>
        <Link className="btn-primary" href="/scanner/unified-url">Run scan</Link>
      </div>
      {loading && <p className="text-slate-400">Loading...</p>}
      {error && <p className="rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}
      <div className="grid gap-4 lg:grid-cols-2">
        {scans.map((scan) => (
          <Link key={scan.id} href={`/dashboard/scans/${scan.id}`} className="card p-5 transition hover:border-cyan/40">
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
      {!loading && scans.length === 0 && <p className="text-slate-500">No saved scans yet.</p>}
    </main>
  );
}
