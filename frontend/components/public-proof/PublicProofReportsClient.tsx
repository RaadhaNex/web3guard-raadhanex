"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { loadLatestUnifiedScan } from "@/lib/latestUnifiedScan";

type JsonMap = Record<string, unknown>;

type ProofListResponse = {
  ok?: boolean;
  records?: JsonMap[];
  count?: number;
  real_only_note?: string;
};

function isRecord(value: unknown): value is JsonMap {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asArray(value: unknown): JsonMap[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function asText(value: unknown, fallback = "—") {
  if (value === null || value === undefined || value === "") return fallback;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return fallback;
  }
}

function jsonText(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function statusTone(status: unknown) {
  const value = asText(status, "").toLowerCase();
  if (value.includes("published") || value.includes("approved") || value.includes("verified")) return "badge-green";
  if (value.includes("revoked") || value.includes("blocked") || value.includes("not_ready")) return "badge-red";
  if (value.includes("draft") || value.includes("private") || value.includes("manual")) return "badge-amber";
  return "badge-cyan";
}

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="mt-4 max-h-[460px] overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs leading-5 text-slate-300">
      {jsonText(value)}
    </pre>
  );
}

const sampleReport = {
  report_id: "W3G-SAMPLE-REPORT",
  report_hash: "sample_report_hash_replace_with_real_hash",
  project_name: "Sample reviewed Web3 project",
  coverage: {
    assessed_count: 2,
    total_modules: 4,
    coverage_percent: 50,
    confidence: "medium",
  },
  professional_scanner_summary: {
    source_tool_counts: { local_rules: 2, slither: 1 },
  },
  top_findings: [
    {
      id: "finding-1",
      title: "Privileged upgrade path needs documented governance",
      severity: "medium",
      category: "upgradeability",
      source_tools: ["local_rules"],
      evidence: "Upgradeable pattern found from supplied source evidence.",
      impact: "Users may not understand who can upgrade implementation logic.",
      fix: "Document upgrade policy, add multisig/timelock where appropriate, and disclose upgrade power.",
      confidence: "medium",
      verification_status: "scanner_detected_needs_review",
    },
  ],
};

export function PublicProofReportsClient() {
  const [status, setStatus] = useState<JsonMap | null>(null);
  const [records, setRecords] = useState<JsonMap[]>([]);
  const [draft, setDraft] = useState<JsonMap | null>(null);
  const [packet, setPacket] = useState<JsonMap | null>(null);
  const [published, setPublished] = useState<JsonMap | null>(null);
  const [verification, setVerification] = useState<JsonMap | null>(null);
  const [activeResult, setActiveResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [projectName, setProjectName] = useState("Sample reviewed Web3 project");
  const [reportId, setReportId] = useState("W3G-SAMPLE-REPORT");
  const [reportHash, setReportHash] = useState("sample_report_hash_replace_with_real_hash");
  const [proofId, setProofId] = useState("");
  const [reviewer, setReviewer] = useState("RAADHANEX reviewer");
  const [reviewerReason, setReviewerReason] = useState("The report was reviewed under authorized pre-audit readiness scope. No certified audit claim is approved.");
  const [reportJson, setReportJson] = useState(jsonText(sampleReport));
  const [includePrivate, setIncludePrivate] = useState(true);

  const selectedProofId = useMemo(() => proofId.trim() || asText(published?.id || packet?.proof_id || draft?.proof_id, ""), [proofId, published, packet, draft]);

  async function withBusy(action: () => Promise<void>) {
    setError(null);
    setLoading(true);
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadStatusAndList() {
    await withBusy(async () => {
      const [nextStatus, list] = await Promise.all([
        apiGet<JsonMap>("/proof-reports/status"),
        apiGet<ProofListResponse>(`/proof-reports?include_private=${includePrivate ? "true" : "false"}`),
      ]);
      setStatus(nextStatus);
      setRecords(asArray(list.records));
      setActiveResult(list);
    });
  }

  useEffect(() => {
    void loadStatusAndList();
  }, []);

  function parseReport() {
    try {
      const parsed = JSON.parse(reportJson) as JsonMap;
      return parsed;
    } catch {
      throw new Error("Report JSON must be valid JSON.");
    }
  }

  function loadLatestScanFromBrowser() {
    const latest = loadLatestUnifiedScan();
    if (!latest) {
      setError("No latest unified scan was found in this browser. Run a scanner first or paste a report JSON manually.");
      return;
    }
    const report = latest.combined_report;
    setProjectName(latest.project_name || report.project_name || "Web3 project");
    setReportId(report.report_id || latest.report_id || "");
    setReportHash(report.report_hash || "");
    setReportJson(jsonText(report));
    setError(null);
  }

  async function createDraft() {
    await withBusy(async () => {
      const report = parseReport();
      const result = await apiPost<JsonMap>("/proof-reports/draft", {
        project_name: projectName.trim(),
        report_id: reportId.trim(),
        report_hash: reportHash.trim(),
        report,
        requested_public_claim: "Web3Guard AI pre-audit readiness proof",
        custom_summary: "Evidence-first public proof packet for an authorized pre-audit readiness review.",
        public_notes: "Not a certified audit, not a security guarantee, and not a claim that all bugs were found.",
        authorized_scope_confirmed: true,
        real_only_acknowledged: true,
      });
      const nextDraft = isRecord(result.draft) ? result.draft : null;
      setDraft(nextDraft);
      setPacket(null);
      setPublished(null);
      setProofId(asText(nextDraft?.proof_id, ""));
      setActiveResult(result);
    });
  }

  async function approveDraft() {
    await withBusy(async () => {
      const report = parseReport();
      const result = await apiPost<JsonMap>("/proof-reports/approve", {
        project_name: projectName.trim(),
        report_id: reportId.trim(),
        report_hash: reportHash.trim(),
        report,
        draft: draft || undefined,
        decision: "approved_public_pre_audit",
        reviewer: reviewer.trim(),
        reviewer_reason: reviewerReason.trim(),
        payment_verified: true,
        manual_review_completed: true,
        authorized_scope_confirmed: true,
        real_only_acknowledged: true,
      });
      const nextPacket = isRecord(result.packet) ? result.packet : null;
      setPacket(nextPacket);
      setProofId(asText(nextPacket?.proof_id, selectedProofId));
      setActiveResult(result);
    });
  }

  async function publishPacket() {
    await withBusy(async () => {
      const report = parseReport();
      const result = await apiPost<JsonMap>("/proof-reports/publish", {
        project_name: projectName.trim(),
        report_id: reportId.trim(),
        report_hash: reportHash.trim(),
        report,
        draft: draft || undefined,
        packet: packet || undefined,
        decision: "approved_public_pre_audit",
        reviewer: reviewer.trim(),
        reviewer_reason: reviewerReason.trim(),
        payment_verified: true,
        manual_review_completed: true,
        authorized_scope_confirmed: true,
        real_only_acknowledged: true,
        visibility: "public",
      });
      const record = isRecord(result.record) ? result.record : null;
      setPublished(record);
      setProofId(asText(record?.id, selectedProofId));
      setActiveResult(result);
      await loadStatusAndList();
    });
  }

  async function verifyProof() {
    const id = selectedProofId;
    if (!id) {
      setError("Enter a proof ID or publish/load a proof first.");
      return;
    }
    await withBusy(async () => {
      const result = await apiGet<JsonMap>(`/proof-reports/${encodeURIComponent(id)}/verify?report_hash=${encodeURIComponent(reportHash.trim())}`);
      setVerification(result);
      setActiveResult(result);
    });
  }

  async function revokeProof() {
    const id = selectedProofId;
    if (!id) {
      setError("Enter a proof ID to revoke.");
      return;
    }
    await withBusy(async () => {
      const result = await apiPost<JsonMap>(`/proof-reports/${encodeURIComponent(id)}/revoke`, {
        reviewer: reviewer.trim(),
        reason: "Revoked from Phase M UI because the public proof needs correction or updated evidence.",
      });
      setActiveResult(result);
      await loadStatusAndList();
    });
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
        <div className="glass-tile p-6 sm:p-8">
          <p className="section-label">Phase M · Public proof UI</p>
          <h1 className="mt-3 text-4xl font-black tracking-[-0.06em] sm:text-6xl">Publish proof without fake audit wording.</h1>
          <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400">
            Draft, approve, publish, verify, and revoke public proof packets backed by real report hashes and reviewer decisions. Missing evidence stays visible.
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <span className="badge badge-green">Report hash required</span>
            <span className="badge badge-amber">No 100% secure claim</span>
            <span className="badge badge-cyan">Integrity verification</span>
            <span className="badge badge-purple">Revocation support</span>
          </div>
          <div className="mt-6 rounded-2xl border border-amber-400/20 bg-amber-500/10 p-4 text-sm leading-6 text-amber-100">
            Safe claim: “Human-reviewed Web3Guard AI pre-audit readiness proof.” Do not market this as a certified audit or guarantee.
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <Link href="/admin/reviewer" className="btn-secondary">Open reviewer workbench</Link>
            <Link href="/report/verify" className="btn-secondary">Report hash verifier</Link>
          </div>
        </div>

        <div className="auth-shell p-5 sm:p-6">
          <p className="text-xs font-black uppercase tracking-[0.22em] text-cyan">Proof controls</p>
          <div className="mt-4 grid gap-3">
            <label className="grid gap-2 text-sm font-bold text-slate-300">Project name<input className="input" value={projectName} onChange={(event) => setProjectName(event.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">Report ID<input className="input" value={reportId} onChange={(event) => setReportId(event.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">Report hash<input className="input" value={reportHash} onChange={(event) => setReportHash(event.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">Proof ID<input className="input" value={proofId} onChange={(event) => setProofId(event.target.value)} placeholder="Auto-filled after draft/publish" /></label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">Reviewer<input className="input" value={reviewer} onChange={(event) => setReviewer(event.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">Reviewer reason<textarea className="textarea min-h-24" value={reviewerReason} onChange={(event) => setReviewerReason(event.target.value)} /></label>
            <label className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300">
              <input type="checkbox" checked={includePrivate} onChange={(event) => setIncludePrivate(event.target.checked)} />
              Include private records when listing proofs
            </label>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <button className="btn-secondary" onClick={loadLatestScanFromBrowser}>Use latest scan</button>
            <button className="btn-primary" onClick={() => void createDraft()} disabled={loading}>Draft proof</button>
            <button className="btn-secondary" onClick={() => void approveDraft()} disabled={loading}>Approve packet</button>
            <button className="btn-secondary" onClick={() => void publishPacket()} disabled={loading}>Publish proof</button>
            <button className="btn-secondary" onClick={() => void verifyProof()} disabled={loading}>Verify proof</button>
            <button className="btn-secondary" onClick={() => void loadStatusAndList()} disabled={loading}>Refresh list</button>
          </div>
          <button className="btn-secondary mt-3 w-full" onClick={() => void revokeProof()} disabled={loading}>Revoke proof if evidence changed</button>
          {error ? <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p> : null}
          {verification ? <p className={`mt-4 rounded-2xl border p-4 text-sm ${verification.verified ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-100" : "border-amber-400/30 bg-amber-500/10 text-amber-100"}`}>Verification: {asText(verification.verified)}</p> : null}
        </div>
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="glass-tile p-5">
          <p className="section-label">Report payload</p>
          <h2 className="mt-2 text-2xl font-black text-white">Paste real combined report JSON.</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">Use the latest unified scan button or paste a real combined report. The backend blocks unsafe claims and requires report_hash before public proof approval.</p>
          <textarea className="textarea mt-4 min-h-[420px] font-mono text-xs" value={reportJson} onChange={(event) => setReportJson(event.target.value)} />
        </div>
        <div className="glass-tile p-5">
          <p className="section-label">Last API response</p>
          <h2 className="mt-2 text-2xl font-black text-white">Proof engine output.</h2>
          {activeResult ? <JsonBlock value={activeResult} /> : <p className="mt-4 text-sm text-slate-400">Run a proof action to see the backend response.</p>}
          <details className="mt-5 rounded-2xl border border-white/10 bg-black/20 p-4">
            <summary className="cursor-pointer font-black text-white">Proof status</summary>
            <JsonBlock value={status} />
          </details>
        </div>
      </section>

      <section className="mt-8">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="section-label">Published proof records</p>
            <h2 className="mt-2 text-3xl font-black text-white">Public proof registry preview.</h2>
          </div>
          <span className="badge badge-cyan">{records.length} record(s)</span>
        </div>
        {records.length === 0 ? (
          <div className="glass-tile p-6 text-sm leading-7 text-slate-400">No proof records found yet. Draft, approve, and publish a proof packet from a real report hash.</div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {records.map((record, index) => {
              const id = asText(record.id, `proof-${index}`);
              const packet = isRecord(record.packet) ? record.packet : {};
              const coverage = isRecord(packet.coverage) ? packet.coverage : {};
              return (
                <article key={`${id}-${index}`} className="glass-tile p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="grid h-12 w-12 place-items-center rounded-2xl border border-cyan/20 bg-cyan/10 font-mono text-cyan">PF</div>
                    <span className={`badge ${statusTone(record.status)}`}>{asText(record.status)}</span>
                  </div>
                  <h3 className="mt-4 text-xl font-black text-white">{asText(record.project_name, "Web3 project")}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{asText(record.public_wording, "Pre-audit readiness proof")}</p>
                  <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                    <div className="rounded-2xl border border-white/10 bg-black/20 p-3"><p className="text-slate-500">Assessed</p><p className="mt-1 text-lg font-black text-white">{asText(coverage.assessed_count, "0")}/{asText(coverage.total_modules, "0")}</p></div>
                    <div className="rounded-2xl border border-white/10 bg-black/20 p-3"><p className="text-slate-500">Manual review</p><p className="mt-1 text-lg font-black text-white">{asText(record.manual_review_claim_allowed, "false")}</p></div>
                  </div>
                  <div className="mt-4 grid gap-2 text-xs text-slate-500">
                    <p className="truncate"><b>Proof:</b> {id}</p>
                    <p className="truncate"><b>Report hash:</b> {asText(record.report_hash)}</p>
                    <p className="truncate"><b>Integrity:</b> {asText(record.integrity_hash)}</p>
                  </div>
                  <button className="btn-secondary mt-4 w-full" onClick={() => { setProofId(id); setReportHash(asText(record.report_hash, "")); setActiveResult(record); }}>Load into verifier</button>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
