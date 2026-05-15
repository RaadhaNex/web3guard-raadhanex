"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPatch } from "@/lib/api";
import type { ScanHistoryRecord } from "@/lib/types";
import { currentDashboardUser, fmtDate, scoreText } from "./DashboardDataHelpers";

export function ScanDetailClient({ scanId }: { scanId: string }) {
  const [scan, setScan] = useState<ScanHistoryRecord | null>(null);
  const [status, setStatus] = useState("saved");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    try {
      const ctx = await currentDashboardUser();
      const data = await apiGet<{ scan: ScanHistoryRecord }>(`/scan-history/${scanId}?user_id=${encodeURIComponent(ctx.userId)}`, { headers: ctx.headers });
      setScan(data.scan);
      setStatus(data.scan.status || "saved");
      setNotes(data.scan.notes || "");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not load scan"); }
  }

  async function save() {
    try {
      const ctx = await currentDashboardUser();
      const data = await apiPatch<{ scan: ScanHistoryRecord }>(`/scan-history/${scanId}?user_id=${encodeURIComponent(ctx.userId)}`, { status, notes }, { headers: ctx.headers });
      setScan(data.scan);
      setMessage("Scan workflow status saved.");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not update scan"); }
  }

  useEffect(() => { void load(); }, [scanId]);

  return <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
    <Link className="text-sm font-bold text-cyan" href="/dashboard/scans">← Back to scans</Link>
    {error && <p className="mt-6 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}
    {scan && <>
      <div className="mt-6 card p-6">
        <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Saved scan</p>
        <h1 className="mt-2 text-4xl font-black">{scan.module} scan</h1>
        <p className="mt-3 text-slate-400">{scan.project_name || "Unnamed project"} • {fmtDate(scan.created_at)}</p>
        <div className="mt-6 grid gap-4 sm:grid-cols-4">
          <Stat label="Score" value={scoreText(scan.score)} />
          <Stat label="Risk" value={scan.risk_label || "No label"} />
          <Stat label="Findings" value={scan.findings_count} />
          <Stat label="Critical/High" value={scan.critical_high_count} />
        </div>
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="card p-6">
          <h2 className="text-2xl font-black">Workflow</h2>
          <select className="select mt-4" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option>saved</option><option>open</option><option>in_review</option><option>fixed</option><option>false_positive</option><option>accepted_risk</option>
          </select>
          <textarea className="textarea mt-4 min-h-[140px]" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Reviewer notes" />
          <button className="btn-primary mt-4" onClick={save}>Save workflow</button>
          {message && <p className="mt-3 text-sm text-emerald-200">{message}</p>}
        </div>
        <div className="card p-6 overflow-hidden">
          <h2 className="text-2xl font-black">Saved payload</h2>
          <pre className="mt-4 max-h-[520px] overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify(scan.payload || {}, null, 2)}</pre>
        </div>
      </div>
    </>}
  </main>;
}

function Stat({ label, value }: { label: string; value: string | number }) { return <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><p className="text-xs text-slate-500">{label}</p><p className="mt-2 font-black text-white">{value}</p></div>; }
