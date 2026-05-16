"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { API_BASE, apiGet, apiPatch } from "@/lib/api";
import type { SavedReportRecord } from "@/lib/types";
import { currentDashboardUser, fmtDate, scoreText } from "./DashboardDataHelpers";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function downloadReportFile(path: string, headers: HeadersInit, filename: string) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Export failed with ${response.status}`);
  }

  const blob = await response.blob();
  downloadBlob(blob, filename);
}

export function ReportDetailClient({ reportId }: { reportId: string }) {
  const [report, setReport] = useState<SavedReportRecord | null>(null);
  const [visibility, setVisibility] = useState("private");
  const [status, setStatus] = useState("saved");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [exporting, setExporting] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const ctx = await currentDashboardUser();
      const userId = ctx.userId;
      const data = await apiGet<{ report: SavedReportRecord }>(
        `/saved-reports/${reportId}?user_id=${encodeURIComponent(userId)}`,
        { headers: ctx.headers }
      );
      setReport(data.report);
      setVisibility(data.report.visibility || "private");
      setStatus(data.report.status || "saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load report");
    }
  }

  async function save() {
    setMessage(null);
    setError(null);
    try {
      const ctx = await currentDashboardUser();
      const userId = ctx.userId;
      const data = await apiPatch<{ report: SavedReportRecord }>(
        `/saved-reports/${reportId}?user_id=${encodeURIComponent(userId)}`,
        { visibility, status },
        { headers: ctx.headers }
      );
      setReport(data.report);
      setMessage("Report metadata saved. Public wording remains pre-audit readiness only.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update report");
    }
  }

  async function exportReport(format: "pdf" | "html" | "markdown" | "json") {
    if (!report) return;

    setExporting(format);
    setMessage(null);
    setError(null);

    try {
      const ctx = await currentDashboardUser();
      const userId = ctx.userId;
      const extension = format === "markdown" ? "md" : format;
      const filename = `${report.report_id || report.id}.${extension}`;

      await downloadReportFile(
        `/saved-reports/${report.id}/export/${format}?user_id=${encodeURIComponent(userId)}`,
        ctx.headers,
        filename
      );

      setMessage(`${format.toUpperCase()} exported from the saved report. This is not a certified audit.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not export report");
    } finally {
      setExporting(null);
    }
  }

  useEffect(() => {
    void load();
  }, [reportId]);

  return (
    <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <Link className="text-sm font-bold text-cyan" href="/dashboard">
        ← Back to dashboard
      </Link>

      {error ? (
        <p className="mt-6 whitespace-pre-wrap rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">
          {error}
        </p>
      ) : null}

      {report ? (
        <>
          <div className="mt-6 card p-6">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Saved report</p>
            <h1 className="mt-2 text-4xl font-black">{report.title}</h1>
            <p className="mt-3 text-slate-400">
              {report.report_id} • {fmtDate(report.created_at)}
            </p>
            <div className="mt-6 grid gap-4 sm:grid-cols-4">
              <Stat label="Overall" value={scoreText(report.overall_score)} />
              <Stat label="Available" value={scoreText(report.available_score)} />
              <Stat label="Risk" value={report.risk_label || "No label"} />
              <Stat label="Status" value={report.status || "saved"} />
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
            <div className="card p-6">
              <h2 className="text-2xl font-black">Delivery metadata</h2>
              <label className="mt-4 block text-sm font-bold text-slate-300">Visibility</label>
              <select className="select mt-2" value={visibility} onChange={(event) => setVisibility(event.target.value)}>
                <option>private</option>
                <option>ready_for_public_registry_later</option>
              </select>
              <label className="mt-4 block text-sm font-bold text-slate-300">Status</label>
              <select className="select mt-2" value={status} onChange={(event) => setStatus(event.target.value)}>
                <option>saved</option>
                <option>draft</option>
                <option>in_review</option>
                <option>delivered</option>
                <option>superseded</option>
              </select>
              <button className="btn-primary mt-5" onClick={save}>
                Save report status
              </button>

              <div className="mt-6 rounded-3xl border border-white/10 bg-white/[0.03] p-4">
                <h3 className="font-black text-white">Export professional report</h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                  Exports are generated from this saved report payload only. Missing modules stay Not assessed.
                </p>
                <div className="mt-4 flex flex-wrap gap-3">
                  {(["pdf", "html", "markdown", "json"] as const).map((format) => (
                    <button
                      key={format}
                      className="btn-secondary"
                      onClick={() => void exportReport(format)}
                      disabled={Boolean(exporting)}
                    >
                      {exporting === format ? "Exporting..." : `Download ${format.toUpperCase()}`}
                    </button>
                  ))}
                </div>
              </div>

              {message ? <p className="mt-3 text-sm text-emerald-200">{message}</p> : null}
            </div>

            <div className="card overflow-hidden p-6">
              <h2 className="text-2xl font-black">Saved report payload</h2>
              <pre className="mt-4 max-h-[520px] overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">
                {JSON.stringify(report.payload || {}, null, 2)}
              </pre>
            </div>
          </div>
        </>
      ) : null}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-2 font-black text-white">{value}</p>
    </div>
  );
}
