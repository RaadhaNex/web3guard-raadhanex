"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type JsonMap = Record<string, unknown>;

type BoardResponse = {
  ok?: boolean;
  safe_review_note?: string;
  workflow_level?: string;
  request_summary?: JsonMap;
  finding_summary?: JsonMap;
  latest_requests?: JsonMap[];
  latest_findings?: JsonMap[];
  quality_gates?: JsonMap;
  next_steps?: string[];
};

type CreateRequestResponse = {
  ok?: boolean;
  request?: JsonMap;
  next_steps?: string[];
};

type ImportResponse = {
  ok?: boolean;
  imported?: number;
  items?: JsonMap[];
  note?: string;
};

function asText(value: unknown, fallback = "—") {
  if (value === null || value === undefined || value === "") return fallback;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return fallback;
  }
}

function jsonPreview(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

const sampleScanPayload = {
  bug_detection_coverage: {
    confirmed_exposures: [
      {
        title: "Public source map exposed",
        severity: "medium",
        confidence: "high",
        category: "public_exposure",
        summary: "A public JavaScript source map was observed and should be reviewed before launch.",
        fix_hint: "Disable source maps in production or restrict public access.",
        evidence: { checked_path: "/_next/static/app.js.map", status: 200 },
      },
    ],
  },
};

export function ManualReviewClient() {
  const [status, setStatus] = useState<JsonMap | null>(null);
  const [methodology, setMethodology] = useState<JsonMap | null>(null);
  const [board, setBoard] = useState<BoardResponse | null>(null);
  const [created, setCreated] = useState<CreateRequestResponse | null>(null);
  const [importResult, setImportResult] = useState<ImportResponse | null>(null);
  const [triageResult, setTriageResult] = useState<JsonMap | null>(null);
  const [decisionResult, setDecisionResult] = useState<JsonMap | null>(null);
  const [scanPayloadText, setScanPayloadText] = useState(jsonPreview(sampleScanPayload));
  const [projectName, setProjectName] = useState("Web3Guard pilot review");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const requestId = useMemo(() => asText(created?.request?.id, ""), [created]);
  const firstFindingId = useMemo(() => {
    const items = importResult?.items;
    if (!items || items.length === 0) return "";
    return asText(items[0]?.id, "");
  }, [importResult]);

  async function refreshBoard() {
    const data = await apiGet<BoardResponse>("/manual-review/board");
    setBoard(data);
  }

  useEffect(() => {
    apiGet<JsonMap>("/manual-review/status").then(setStatus).catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
    apiGet<JsonMap>("/manual-review/methodology").then(setMethodology).catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
    refreshBoard().catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  async function createManualRequest() {
    setError(null);
    setLoading(true);
    try {
      const data = await apiPost<CreateRequestResponse>("/manual-review/requests", {
        project_name: projectName,
        project_url: "https://example.com",
        review_type: "pre_audit_readiness",
        priority: "medium",
        scope_summary: "Authorized manual triage for supplied Web3Guard scan evidence only. No exploit automation.",
        evidence_sources: ["unified_scan", "static_artifact", "manual_reviewer_note"],
        authorized_scope_confirmed: true,
        payment_status: "verified",
      });
      setCreated(data);
      await refreshBoard();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function importScanFindings() {
    setError(null);
    setLoading(true);
    try {
      let scanPayload: JsonMap = {};
      try {
        scanPayload = JSON.parse(scanPayloadText) as JsonMap;
      } catch {
        throw new Error("Scan payload must be valid JSON.");
      }
      const data = await apiPost<ImportResponse>("/manual-review/findings/import", {
        request_id: requestId || null,
        scan_payload: scanPayload,
      });
      setImportResult(data);
      await refreshBoard();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function triageFirstFinding() {
    setError(null);
    if (!firstFindingId) {
      setError("Import at least one finding first.");
      return;
    }
    setLoading(true);
    try {
      const data = await apiPost<JsonMap>("/manual-review/findings/triage", {
        finding_id: firstFindingId,
        status: "confirmed",
        reviewer: "Internal reviewer",
        reviewer_note: "Evidence was reviewed and this finding should be treated as a confirmed pre-audit readiness issue.",
        confirmed_evidence_note: "Confirmed from supplied scanner evidence; no exploit automation was used.",
      });
      setTriageResult(data);
      await refreshBoard();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function prepareReviewedDecision() {
    setError(null);
    if (!requestId) {
      setError("Create a review request first.");
      return;
    }
    setLoading(true);
    try {
      const data = await apiPost<JsonMap>("/manual-review/reports/decision", {
        request_id: requestId,
        decision: "reviewed_report_ready",
        reviewer: "Internal reviewer",
        reviewer_reason: "Findings have been triaged under the authorized pre-audit readiness scope and payment/manual validation is verified.",
        payment_verified: true,
      });
      setDecisionResult(data);
      await refreshBoard();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-cyan-300/15 bg-slate-950/70 p-6 shadow-2xl shadow-cyan-950/20 sm:p-8">
        <p className="section-label">Manual review</p>
        <h1 className="mt-3 max-w-5xl text-4xl font-black tracking-[-0.05em] text-white sm:text-6xl">
          Manual Expert Review + Finding Triage Workflow
        </h1>
        <p className="mt-4 max-w-4xl text-sm leading-7 text-slate-300 sm:text-base">
          Adds an audit-company style workflow and audit-company level scanner foundation: review requests, finding triage, false-positive removal, severity override reasons, payment/manual validation gate, and reviewed pre-audit report decision. It still does not claim certified audit or 100% security.
        </p>
        {status ? (
          <div className="mt-6 grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
              <b className="text-white">Workflow</b>
              <p className="mt-2 text-sm text-slate-300">{asText(status.workflow_level)}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
              <b className="text-white">Certified audit?</b>
              <p className="mt-2 text-sm text-slate-300">{asText(status.certified_audit)}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
              <b className="text-white">Security guarantee?</b>
              <p className="mt-2 text-sm text-slate-300">{asText(status.security_guarantee)}</p>
            </div>
          </div>
        ) : null}
      </section>

      {error ? <p className="mt-5 rounded-2xl border border-red-400/20 bg-red-500/10 p-4 text-sm text-red-100">{error}</p> : null}

      <section className="mt-6 grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
        <article className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-2xl font-black text-white">Run the manual-review flow</h2>
          <label className="mt-4 block text-sm font-bold text-slate-200">
            Project name
            <input className="input mt-2" value={projectName} onChange={(event) => setProjectName(event.target.value)} />
          </label>
          <div className="mt-4 grid gap-3">
            <button className="btn-primary" type="button" disabled={loading} onClick={() => void createManualRequest()}>
              1. Create authorized review request
            </button>
            <button className="btn-secondary" type="button" disabled={loading} onClick={() => void importScanFindings()}>
              2. Import real scan findings
            </button>
            <button className="btn-secondary" type="button" disabled={loading || !firstFindingId} onClick={() => void triageFirstFinding()}>
              3. Confirm first finding with reviewer note
            </button>
            <button className="btn-secondary" type="button" disabled={loading || !requestId} onClick={() => void prepareReviewedDecision()}>
              4. Try reviewed report-ready decision
            </button>
          </div>
          <div className="mt-5 rounded-2xl border border-cyan-300/15 bg-cyan-300/[0.05] p-4 text-sm leading-6 text-cyan-50">
            Request ID: <b>{requestId || "Create request first"}</b><br />
            Finding ID: <b>{firstFindingId || "Import finding first"}</b>
          </div>
        </article>

        <article className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-2xl font-black text-white">Paste latest scan payload</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Paste real unified scan JSON here. Demo payload only shows the shape; production findings must come from real scan/static artifact/manual evidence.
          </p>
          <textarea className="textarea mt-4 min-h-[320px]" value={scanPayloadText} onChange={(event) => setScanPayloadText(event.target.value)} />
        </article>
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-2">
        <article className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-2xl font-black text-white">Review board</h2>
          {board ? (
            <div className="mt-4 grid gap-3">
              <pre className="max-h-[420px] overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{jsonPreview(board)}</pre>
            </div>
          ) : <p className="mt-3 text-sm text-slate-400">Loading board...</p>}
        </article>
        <article className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-2xl font-black text-white">Latest actions</h2>
          <div className="mt-4 grid gap-3">
            {created ? <pre className="max-h-52 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{jsonPreview(created)}</pre> : null}
            {importResult ? <pre className="max-h-52 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{jsonPreview(importResult)}</pre> : null}
            {triageResult ? <pre className="max-h-52 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{jsonPreview(triageResult)}</pre> : null}
            {decisionResult ? <pre className="max-h-52 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{jsonPreview(decisionResult)}</pre> : null}
            {!created && !importResult && !triageResult && !decisionResult ? <p className="text-sm text-slate-400">No manual-review action yet.</p> : null}
          </div>
        </article>
      </section>

      {methodology ? (
        <section className="mt-6 rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5">
          <h2 className="text-2xl font-black text-white">Methodology boundary</h2>
          <pre className="mt-4 max-h-[420px] overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{jsonPreview(methodology)}</pre>
        </section>
      ) : null}
    </main>
  );
}
