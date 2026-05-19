
"use client";

import { useMemo, useState } from "react";
import { API_BASE, apiPost } from "@/lib/api";

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

async function postBlob(path: string, payload: unknown, accept: string) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: accept },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Export failed");
  }
  return response.blob();
}

type PublicationRecord = {
  id: string;
  visibility: "public" | "private";
  report_id?: string;
  report_hash?: string;
  public_wording?: string;
};

function prettyJson(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function getReportSummary(report: Record<string, any> | null) {
  if (!report) {
    return {
      reportId: "—",
      hash: "—",
      score: "—",
      project: "No report loaded",
      risk: "Waiting for JSON",
      generated: "—",
    };
  }

  const combined = report.combined || {};
  return {
    reportId: report.report_id || "Missing",
    hash: report.report_hash || "Missing",
    score: combined.overall_score ?? combined.available_score ?? report.overall_score ?? report.available_score ?? "N/A",
    project: report.project_name || "Unnamed project",
    risk: combined.risk_label || report.risk_label || "Not Assessed",
    generated: report.generated_at || "Not provided",
  };
}

export function ProfessionalReportClient() {
  const [raw, setRaw] = useState("");
  const [status, setStatus] = useState("Paste a real combined report JSON with report_id and report_hash.");
  const [htmlPreview, setHtmlPreview] = useState("");
  const [publication, setPublication] = useState<PublicationRecord | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const parsed = useMemo(() => {
    if (!raw.trim()) return null;
    try {
      const value = JSON.parse(raw);
      return (value.report ?? value) as Record<string, any>;
    } catch {
      return null;
    }
  }, [raw]);

  const hasRealReport = Boolean(parsed?.report_hash && parsed?.report_id);
  const summary = getReportSummary(parsed);
  const missingKeys = ["report_id", "report_hash"].filter((key) => !parsed?.[key]);

  async function buildArtifacts() {
    if (!hasRealReport) return setStatus("A report object with report_id and report_hash is required before artifacts can be generated.");
    setBusy("preview");
    setStatus("Building professional artifacts from the supplied report...");
    try {
      const data = await apiPost<{ html_preview: string; pdf_size_bytes: number }>("/report/artifacts", { report: parsed });
      setHtmlPreview(data.html_preview);
      setStatus(`Preview ready. Server PDF size preview: ${data.pdf_size_bytes} bytes.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Artifact build failed.");
    } finally {
      setBusy(null);
    }
  }

  async function download(format: "pdf" | "html" | "markdown" | "json") {
    if (!hasRealReport) return setStatus("A report object with report_id and report_hash is required before export.");
    setBusy(format);
    const accept = format === "pdf" ? "application/pdf" : format === "html" ? "text/html" : format === "markdown" ? "text/markdown" : "application/json";
    try {
      const blob = await postBlob(`/report/export/${format}`, { report: parsed }, accept);
      downloadBlob(blob, `${parsed?.report_id || "web3guard-report"}.${format === "markdown" ? "md" : format}`);
      setStatus(`${format.toUpperCase()} downloaded. Keep the pre-audit disclaimer visible when sharing.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Export failed.");
    } finally {
      setBusy(null);
    }
  }

  async function publish(visibility: "public" | "private") {
    if (!hasRealReport) return setStatus("A report object with report_id and report_hash is required before publication.");
    setBusy(visibility);
    setStatus(`Creating ${visibility} report record...`);
    try {
      const data = await apiPost<{ record: PublicationRecord }>("/report/publication", { report: parsed, visibility });
      setPublication(data.record);
      setStatus(`${visibility} report record created with pre-audit wording.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Publication failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
      <section className="card p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="section-label">Report input</p>
            <h2 className="mt-2 text-2xl font-black text-white">Combined report JSON</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Paste a report payload generated by the scanner or combined-report endpoint. Exports stay blocked until traceability fields are present.
            </p>
          </div>
          <span className={`badge ${hasRealReport ? "badge-green" : "badge-amber"}`}>{hasRealReport ? "Ready" : "Needs report data"}</span>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
            <p className="mono text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Project</p>
            <p className="mt-2 truncate text-sm font-black text-white">{summary.project}</p>
          </div>
          <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
            <p className="mono text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Confidence</p>
            <p className="mt-2 text-sm font-black text-white">{String(summary.score)} · {summary.risk}</p>
          </div>
          <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
            <p className="mono text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Report ID</p>
            <p className="mt-2 truncate text-sm font-black text-white">{summary.reportId}</p>
          </div>
        </div>

        <textarea
          className="textarea mt-5 min-h-[360px]"
          value={raw}
          onChange={(event) => setRaw(event.target.value)}
          placeholder='Paste JSON containing "report_id" and "report_hash" here.'
        />

        {!parsed && raw.trim() ? (
          <p className="mt-3 rounded-xl border border-red-400/20 bg-red-500/10 p-3 text-sm text-red-100">JSON is not valid yet.</p>
        ) : null}

        {parsed && missingKeys.length ? (
          <p className="mt-3 rounded-xl border border-amber-300/20 bg-amber-300/10 p-3 text-sm text-amber-100">
            Missing required field(s): {missingKeys.join(", ")}.
          </p>
        ) : null}

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <button className="btn-primary" onClick={() => void buildArtifacts()} disabled={busy !== null}>Build preview</button>
          <button className="btn-secondary" onClick={() => void download("pdf")} disabled={busy !== null}>Download PDF</button>
          <button className="btn-secondary" onClick={() => void download("html")} disabled={busy !== null}>Download HTML</button>
          <button className="btn-secondary" onClick={() => void download("markdown")} disabled={busy !== null}>Download MD</button>
          <button className="btn-secondary" onClick={() => void download("json")} disabled={busy !== null}>Download JSON</button>
          <button className="btn-secondary" onClick={() => void publish("private")} disabled={busy !== null}>Save private record</button>
        </div>
        <div className="mt-3 flex flex-wrap gap-3">
          <button className="btn-secondary sm:w-auto" onClick={() => void publish("public")} disabled={busy !== null}>Publish public record</button>
          <button className="btn-ghost" onClick={() => setRaw(prettyJson(parsed))} disabled={!parsed}>Format JSON</button>
        </div>

        <p className={`mt-5 rounded-2xl border p-4 text-sm leading-6 ${hasRealReport ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-100" : "border-amber-300/20 bg-amber-300/10 text-amber-100"}`}>
          {busy ? `Working on ${busy}...` : status}
        </p>

        {publication ? (
          <div className="mt-4 rounded-2xl border border-cyan/15 bg-cyan/10 p-4 text-sm leading-6 text-cyan-50">
            <p><strong>Record:</strong> {publication.id}</p>
            <p><strong>Visibility:</strong> {publication.visibility}</p>
            <p><strong>Verify:</strong> /report/public/{publication.id}/verify?report_hash={publication.report_hash}</p>
          </div>
        ) : null}
      </section>

      <section className="card overflow-hidden p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="section-label">Preview</p>
            <h2 className="mt-2 text-2xl font-black text-white">Audit-style delivery view</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Preview appears only after the backend processes a valid report payload.</p>
          </div>
          <span className="badge badge-cyan">HTML preview</span>
        </div>

        <div className="mt-5 h-[620px] overflow-hidden rounded-2xl border border-white/[0.08] bg-black/40">
          {htmlPreview ? (
            <iframe title="Professional report preview" srcDoc={htmlPreview} className="h-full w-full bg-white" />
          ) : (
            <div className="flex h-full items-center justify-center p-8 text-center">
              <div>
                <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl border border-cyan/20 bg-cyan/10 mono text-cyan">PDF</div>
                <p className="mt-4 text-sm font-bold text-white">No preview built yet</p>
                <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">Paste report JSON with traceability fields, then build preview.</p>
              </div>
            </div>
          )}
        </div>

        <div className="mt-5 grid gap-3 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4 text-xs leading-5 text-slate-400 sm:grid-cols-2">
          <p><strong className="text-white">Hash:</strong> {summary.hash}</p>
          <p><strong className="text-white">Generated:</strong> {String(summary.generated)}</p>
        </div>
      </section>
    </div>
  );
}
