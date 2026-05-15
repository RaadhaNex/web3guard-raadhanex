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

export function ProfessionalReportClient() {
  const [raw, setRaw] = useState("");
  const [status, setStatus] = useState("Paste a real combined report JSON from /report/combined or dashboard saved report.");
  const [htmlPreview, setHtmlPreview] = useState("");
  const [publication, setPublication] = useState<PublicationRecord | null>(null);

  const parsed = useMemo(() => {
    if (!raw.trim()) return null;
    try {
      const value = JSON.parse(raw);
      return value.report ?? value;
    } catch {
      return null;
    }
  }, [raw]);

  const hasRealReport = Boolean(parsed?.report_hash && parsed?.report_id);

  async function buildArtifacts() {
    if (!hasRealReport) return setStatus("A real combined report object with report_id and report_hash is required. No fake report generated.");
    setStatus("Building professional artifacts from your pasted report...");
    const data = await apiPost<{ html_preview: string; pdf_size_bytes: number }>("/report/artifacts", { report: parsed });
    setHtmlPreview(data.html_preview);
    setStatus(`Artifacts ready. Server PDF size preview: ${data.pdf_size_bytes} bytes.`);
  }

  async function downloadPdf() {
    if (!hasRealReport) return setStatus("A real combined report object is required before PDF export.");
    setStatus("Generating server-side PDF...");
    const blob = await postBlob("/report/export/pdf", { report: parsed }, "application/pdf");
    downloadBlob(blob, `${parsed.report_id || "web3guard-report"}.pdf`);
    setStatus("PDF downloaded. This is a generated report, not a certified audit.");
  }

  async function downloadHtml() {
    if (!hasRealReport) return setStatus("A real combined report object is required before HTML export.");
    const blob = await postBlob("/report/export/html", { report: parsed }, "text/html");
    downloadBlob(blob, `${parsed.report_id || "web3guard-report"}.html`);
    setStatus("HTML report downloaded.");
  }

  async function downloadMarkdown() {
    if (!hasRealReport) return setStatus("A real combined report object is required before Markdown export.");
    const blob = await postBlob("/report/export/markdown", { report: parsed }, "text/markdown");
    downloadBlob(blob, `${parsed.report_id || "web3guard-report"}.md`);
    setStatus("Markdown report downloaded.");
  }

  async function downloadJson() {
    if (!hasRealReport) return setStatus("A real combined report object is required before JSON export.");
    const blob = await postBlob("/report/export/json", { report: parsed }, "application/json");
    downloadBlob(blob, `${parsed.report_id || "web3guard-report"}.json`);
    setStatus("JSON report downloaded.");
  }

  async function publish(visibility: "public" | "private") {
    if (!hasRealReport) return setStatus("A real combined report object is required before publication.");
    setStatus(`Creating ${visibility} report record...`);
    const data = await apiPost<{ record: PublicationRecord }>("/report/publication", { report: parsed, visibility });
    setPublication(data.record);
    setStatus(`${visibility} report record created. Public wording remains pre-audit readiness only.`);
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
      <section className="card p-6">
        <p className="text-sm font-black uppercase tracking-[0.28em] text-cyan">Real report input</p>
        <h2 className="mt-2 text-2xl font-black text-white">Paste combined report JSON</h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          This tool does not generate fake reports. First create a real combined report from scanner output, then paste it here for PDF/HTML/Markdown/JSON/public record export.
        </p>
        <textarea
          className="mt-4 min-h-[300px] w-full rounded-3xl border border-white/10 bg-black/30 p-4 font-mono text-xs text-slate-200 outline-none focus:border-cyan/50"
          value={raw}
          onChange={(event) => setRaw(event.target.value)}
          placeholder='Paste output from POST /report/combined here. It must contain "report_id" and "report_hash".'
        />
        <div className="mt-4 flex flex-wrap gap-3">
          <button className="btn-primary" onClick={buildArtifacts}>Build preview</button>
          <button className="btn-secondary" onClick={downloadPdf}>Download PDF</button>
          <button className="btn-secondary" onClick={downloadHtml}>Download HTML</button>
          <button className="btn-secondary" onClick={downloadMarkdown}>Download Markdown</button>
          <button className="btn-secondary" onClick={downloadJson}>Download JSON</button>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <button className="btn-secondary" onClick={() => publish("private")}>Save private report record</button>
          <button className="btn-secondary" onClick={() => publish("public")}>Publish public report record</button>
        </div>
        <p className={`mt-4 rounded-2xl border p-4 text-sm ${hasRealReport ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-100" : "border-amber-400/20 bg-amber-400/10 text-amber-100"}`}>{status}</p>
        {publication ? (
          <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-300">
            <p><strong className="text-white">Record:</strong> {publication.id}</p>
            <p><strong className="text-white">Visibility:</strong> {publication.visibility}</p>
            <p><strong className="text-white">Verify:</strong> /report/public/{publication.id}/verify?report_hash={publication.report_hash}</p>
          </div>
        ) : null}
      </section>
      <section className="card overflow-hidden p-6">
        <p className="text-sm font-black uppercase tracking-[0.28em] text-cyan">Professional preview</p>
        <h2 className="mt-2 text-2xl font-black text-white">HTML report preview</h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">Preview appears only after valid report JSON is processed by backend.</p>
        <div className="mt-4 h-[620px] overflow-auto rounded-3xl border border-white/10 bg-black/40">
          {htmlPreview ? (
            <iframe title="Professional report preview" srcDoc={htmlPreview} className="h-full w-full" />
          ) : (
            <div className="flex h-full items-center justify-center p-8 text-center text-sm text-slate-500">No professional preview yet.</div>
          )}
        </div>
      </section>
    </div>
  );
}
