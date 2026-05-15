"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPatch } from "@/lib/api";
import type { SecureScoreFinding } from "@/lib/types";
import { currentDashboardUser } from "@/components/dashboard/DashboardDataHelpers";

const statuses = ["open", "in_progress", "fixed", "false_positive", "accepted_risk", "needs_manual_review"];
const severities = ["", "critical", "high", "medium", "low", "info"];

export function FindingsWorkflowClient() {
  const [findings, setFindings] = useState<SecureScoreFinding[]>([]);
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [module, setModule] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const ctx = await currentDashboardUser();
      const params = new URLSearchParams({ user_id: ctx.userId, limit: "200" });
      if (severity) params.set("severity", severity);
      if (status) params.set("status", status);
      if (module) params.set("module", module);
      const data = await apiGet<{ findings: SecureScoreFinding[] }>(`/findings?${params.toString()}`, { headers: ctx.headers });
      setFindings(data.findings);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load findings");
    } finally {
      setLoading(false);
    }
  }

  async function updateFinding(finding: SecureScoreFinding, nextStatus: string) {
    setError(null);
    setMessage(null);
    try {
      const ctx = await currentDashboardUser();
      await apiPatch(`/findings/${encodeURIComponent(finding.id)}/workflow?user_id=${encodeURIComponent(ctx.userId)}`, {
        scan_id: finding.scan_id,
        status: nextStatus,
        notes: `Status changed to ${nextStatus} from Phase 10 findings workflow UI.`,
      }, { headers: ctx.headers });
      setMessage("Finding workflow status saved. This does not auto-change source code.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update finding");
    }
  }

  useEffect(() => { void load(); }, [severity, status, module]);

  const modules = Array.from(new Set(findings.map((finding) => finding.module))).sort();

  return <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
    <div className="mb-8">
      <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Phase 10 findings workflow</p>
      <h1 className="mt-2 text-4xl font-black">Findings workflow</h1>
      <p className="mt-3 max-w-3xl text-slate-400">Track real saved findings from scan payloads. Status changes are manual/reviewer actions; Web3Guard AI does not automatically edit production code.</p>
    </div>

    <section className="card mb-6 grid gap-4 p-4 md:grid-cols-4">
      <select className="select" value={severity} onChange={(e) => setSeverity(e.target.value)}>{severities.map((item) => <option key={item} value={item}>{item || "All severities"}</option>)}</select>
      <select className="select" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option>{statuses.map((item) => <option key={item}>{item}</option>)}</select>
      <select className="select" value={module} onChange={(e) => setModule(e.target.value)}><option value="">All modules</option>{modules.map((item) => <option key={item}>{item}</option>)}</select>
      <button className="btn-secondary" onClick={() => { setSeverity(""); setStatus(""); setModule(""); }}>Clear filters</button>
    </section>

    {loading && <p className="text-slate-400">Loading findings...</p>}
    {error && <p className="rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}
    {message && <p className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-emerald-100">{message}</p>}

    <div className="grid gap-4">
      {!loading && findings.length === 0 && <p className="text-slate-500">No saved findings match this filter. Run and save a scan first.</p>}
      {findings.map((finding) => <article key={`${finding.scan_id}-${finding.id}`} className="card p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap gap-2 text-xs font-bold uppercase tracking-wide"><span className="text-cyan">{finding.module_label || finding.module}</span><span className="text-slate-500">{finding.severity}</span><span className="text-slate-500">{finding.workflow_status}</span></div>
            <h2 className="mt-2 text-xl font-black">{finding.title}</h2>
            <p className="mt-2 text-sm text-slate-400">{finding.description}</p>
            <p className="mt-3 text-sm text-slate-300"><strong>Recommendation:</strong> {finding.recommendation || "Review before launch."}</p>
            {finding.workflow_notes && <p className="mt-2 text-xs text-slate-500">Notes: {finding.workflow_notes}</p>}
          </div>
          <select className="select max-w-[220px]" value={finding.workflow_status} onChange={(e) => updateFinding(finding, e.target.value)}>{statuses.map((item) => <option key={item}>{item}</option>)}</select>
        </div>
      </article>)}
    </div>
  </main>;
}
