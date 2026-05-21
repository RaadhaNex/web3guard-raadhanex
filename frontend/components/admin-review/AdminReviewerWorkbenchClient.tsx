"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type JsonMap = Record<string, unknown>;

type AdminBoard = {
  ok?: boolean;
  status?: string;
  filters?: JsonMap;
  assignments?: JsonMap[];
  fix_verifications?: JsonMap[];
  approval_events?: JsonMap[];
  ready_for_approval?: JsonMap[];
  blocked_or_in_progress?: JsonMap[];
  counters?: JsonMap;
  real_only_note?: string;
  next_steps?: string[];
};

type ListResponse = {
  ok?: boolean;
  items?: JsonMap[];
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
  if (value.includes("ready") || value.includes("verified") || value.includes("approved") || value.includes("fixed")) return "badge-green";
  if (value.includes("blocked") || value.includes("rejected") || value.includes("critical") || value.includes("high")) return "badge-red";
  if (value.includes("pending") || value.includes("triage") || value.includes("evidence") || value.includes("review")) return "badge-amber";
  return "badge-cyan";
}

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="mt-4 max-h-[420px] overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs leading-5 text-slate-300">
      {jsonText(value)}
    </pre>
  );
}

function MetricCard({ label, value, tone = "cyan" }: { label: string; value: unknown; tone?: "cyan" | "green" | "amber" | "red" }) {
  const toneClass = {
    cyan: "border-cyan/15 bg-cyan/5 text-cyan",
    green: "border-emerald-400/20 bg-emerald-500/10 text-emerald-200",
    amber: "border-amber-400/20 bg-amber-500/10 text-amber-100",
    red: "border-red-400/20 bg-red-500/10 text-red-100",
  }[tone];

  return (
    <div className={`rounded-2xl border p-4 ${toneClass}`}>
      <p className="text-xs font-black uppercase tracking-[0.18em] opacity-80">{label}</p>
      <p className="mt-2 text-2xl font-black text-white">{asText(value, "0")}</p>
    </div>
  );
}

function CompactTable({ title, items, empty }: { title: string; items: JsonMap[]; empty: string }) {
  return (
    <section className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-black text-white">{title}</h3>
        <span className="badge badge-cyan">{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="mt-4 text-sm leading-6 text-slate-400">{empty}</p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="text-xs uppercase tracking-[0.16em] text-slate-500">
              <tr>
                <th className="px-3 py-3">ID</th>
                <th className="px-3 py-3">Request</th>
                <th className="px-3 py-3">Reviewer</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {items.slice(0, 12).map((item, index) => (
                <tr key={`${asText(item.id, title)}-${index}`}>
                  <td className="max-w-[190px] truncate px-3 py-3 font-mono text-xs text-slate-300">{asText(item.id || item.event_id || item.finding_id)}</td>
                  <td className="max-w-[190px] truncate px-3 py-3 text-slate-300">{asText(item.request_id)}</td>
                  <td className="px-3 py-3 text-slate-300">{asText(item.reviewer || item.assigned_by)}</td>
                  <td className="px-3 py-3"><span className={`badge ${statusTone(item.status || item.decision)}`}>{asText(item.status || item.decision)}</span></td>
                  <td className="px-3 py-3 text-xs text-slate-500">{asText(item.created_at || item.assigned_at || item.reviewed_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function AdminReviewerWorkbenchClient() {
  const [status, setStatus] = useState<JsonMap | null>(null);
  const [board, setBoard] = useState<AdminBoard | null>(null);
  const [assignments, setAssignments] = useState<JsonMap[]>([]);
  const [fixes, setFixes] = useState<JsonMap[]>([]);
  const [activeResult, setActiveResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [requestId, setRequestId] = useState("req_sample_001");
  const [findingId, setFindingId] = useState("finding_sample_001");
  const [reviewer, setReviewer] = useState("RAADHANEX reviewer");
  const [reportHash, setReportHash] = useState("report_hash_from_reviewed_combined_report");
  const [reportId, setReportId] = useState("W3G-REPORT-SAMPLE");
  const [reviewerReason, setReviewerReason] = useState("Human reviewer checked the supplied evidence under authorized pre-audit scope. No certified audit claim is being made.");

  const counters = useMemo(() => board?.counters || {}, [board]);
  const ready = useMemo(() => asArray(board?.ready_for_approval), [board]);
  const blocked = useMemo(() => asArray(board?.blocked_or_in_progress), [board]);

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

  async function loadAll() {
    await withBusy(async () => {
      const [nextStatus, nextBoard, nextAssignments, nextFixes] = await Promise.all([
        apiGet<JsonMap>("/review-ops/status"),
        apiGet<AdminBoard>("/review-ops/admin-board"),
        apiGet<ListResponse>("/review-ops/assignments"),
        apiGet<ListResponse>("/review-ops/fix-verifications"),
      ]);
      setStatus(nextStatus);
      setBoard(nextBoard);
      setAssignments(asArray(nextAssignments.items));
      setFixes(asArray(nextFixes.items));
      setActiveResult(nextBoard);
    });
  }

  useEffect(() => {
    void loadAll();
  }, []);

  async function createAssignment() {
    await withBusy(async () => {
      const result = await apiPost<JsonMap>("/review-ops/assignments", {
        request_id: requestId.trim(),
        reviewer: reviewer.trim(),
        role: "lead_reviewer",
        assigned_by: "RAADHANEX admin UI",
        scope_summary: "Authorized human review for supplied Web3Guard evidence only. No exploit automation and no certified audit claim.",
      });
      setActiveResult(result);
      await loadAll();
    });
  }

  async function verifyFix(statusValue: string) {
    await withBusy(async () => {
      const result = await apiPost<JsonMap>("/review-ops/fix-verifications", {
        finding_id: findingId.trim(),
        request_id: requestId.trim(),
        reviewer: reviewer.trim(),
        status: statusValue,
        fix_summary: statusValue === "verified" ? "Fix evidence reviewed and accepted for pre-audit readiness workflow." : "Fix requires more evidence or regression testing.",
        evidence: {
          source: "admin_reviewer_ui",
          safe_boundary: "No destructive testing, no wallet signing, no private key collection.",
        },
        test_commands: ["python -m pytest -q"],
        reviewer_note: "Reviewer decision recorded from Phase M workbench.",
      });
      setActiveResult(result);
      await loadAll();
    });
  }

  async function loadReadiness() {
    await withBusy(async () => {
      const result = await apiGet<JsonMap>(`/review-ops/report-readiness?request_id=${encodeURIComponent(requestId.trim())}`);
      setActiveResult(result);
    });
  }

  async function approveReviewed() {
    await withBusy(async () => {
      const result = await apiPost<JsonMap>("/review-ops/reports/approve-reviewed", {
        request_id: requestId.trim(),
        decision: "approved_reviewed_pre_audit_report",
        reviewer: reviewer.trim(),
        reviewer_reason: reviewerReason.trim(),
        report_hash: reportHash.trim(),
        report_id: reportId.trim(),
        report_payload: {
          report_id: reportId.trim(),
          report_hash: reportHash.trim(),
          project_name: "Reviewed Web3 project",
          coverage: { assessed_count: 1, total_modules: 1, coverage_percent: 100, confidence: "reviewed" },
        },
      });
      setActiveResult(result);
      await loadAll();
    });
  }

  async function publishProofFromReviewed() {
    await withBusy(async () => {
      const result = await apiPost<JsonMap>("/review-ops/public-proof/from-reviewed", {
        request_id: requestId.trim(),
        decision: "approved_reviewed_pre_audit_report",
        reviewer: reviewer.trim(),
        reviewer_reason: reviewerReason.trim(),
        report_hash: reportHash.trim(),
        report_id: reportId.trim(),
        publish: true,
        visibility: "public",
        report_payload: {
          report_id: reportId.trim(),
          report_hash: reportHash.trim(),
          project_name: "Reviewed Web3 project",
          coverage: { assessed_count: 1, total_modules: 1, coverage_percent: 100, confidence: "reviewed" },
          top_findings: [],
        },
      });
      setActiveResult(result);
      await loadAll();
    });
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
        <div className="glass-tile p-6 sm:p-8">
          <p className="section-label">Phase M · Admin reviewer UI</p>
          <h1 className="mt-3 text-4xl font-black tracking-[-0.06em] sm:text-6xl">Human-review workbench for audit-style operations.</h1>
          <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400">
            Manage reviewer assignments, fix verification, report-readiness gates, and public-proof handoff without changing the real-only scanner rules.
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <span className="badge badge-green">Human-reviewed pre-audit only</span>
            <span className="badge badge-amber">No certified audit claim</span>
            <span className="badge badge-cyan">Fix verification log</span>
            <span className="badge badge-purple">Proof handoff ready</span>
          </div>
          <div className="mt-6 rounded-2xl border border-amber-400/20 bg-amber-500/10 p-4 text-sm leading-6 text-amber-100">
            This UI is for internal reviewer operations. It does not make Web3Guard a certified audit provider by itself. Real reviewer identity, legal scope, and client approval are still required.
          </div>
        </div>

        <div className="auth-shell p-5 sm:p-6">
          <p className="text-xs font-black uppercase tracking-[0.22em] text-cyan">Reviewer controls</p>
          <div className="mt-4 grid gap-3">
            <label className="grid gap-2 text-sm font-bold text-slate-300">Request ID<input className="input" value={requestId} onChange={(event) => setRequestId(event.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">Finding ID<input className="input" value={findingId} onChange={(event) => setFindingId(event.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">Reviewer<input className="input" value={reviewer} onChange={(event) => setReviewer(event.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">Report hash<input className="input" value={reportHash} onChange={(event) => setReportHash(event.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">Report ID<input className="input" value={reportId} onChange={(event) => setReportId(event.target.value)} /></label>
            <label className="grid gap-2 text-sm font-bold text-slate-300">Reviewer reason<textarea className="textarea min-h-28" value={reviewerReason} onChange={(event) => setReviewerReason(event.target.value)} /></label>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <button className="btn-primary" onClick={() => void loadAll()} disabled={loading}>{loading ? "Loading..." : "Refresh board"}</button>
            <button className="btn-secondary" onClick={() => void createAssignment()} disabled={loading}>Assign reviewer</button>
            <button className="btn-secondary" onClick={() => void verifyFix("verified")} disabled={loading}>Mark fix verified</button>
            <button className="btn-secondary" onClick={() => void verifyFix("regression_needed")} disabled={loading}>Needs regression</button>
            <button className="btn-secondary" onClick={() => void loadReadiness()} disabled={loading}>Check readiness</button>
            <button className="btn-secondary" onClick={() => void approveReviewed()} disabled={loading}>Approve reviewed</button>
          </div>
          <button className="btn-primary mt-3 w-full" onClick={() => void publishProofFromReviewed()} disabled={loading}>Publish public proof from reviewed report</button>
          {error ? <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p> : null}
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <Link href="/report/proof" className="badge badge-cyan">Open public proof UI</Link>
            <Link href="/admin" className="badge badge-purple">Admin hub</Link>
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Assignments" value={counters.assignments ?? assignments.length} />
        <MetricCard label="Fix verifications" value={counters.fix_verifications ?? fixes.length} tone="green" />
        <MetricCard label="Ready approvals" value={ready.length} tone="amber" />
        <MetricCard label="Blocked/in progress" value={blocked.length} tone="red" />
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-2">
        <CompactTable title="Latest assignments" items={assignments.length ? assignments : asArray(board?.assignments)} empty="No reviewer assignments stored yet." />
        <CompactTable title="Fix verification log" items={fixes.length ? fixes : asArray(board?.fix_verifications)} empty="No fix verification records stored yet." />
        <CompactTable title="Ready for approval" items={ready} empty="No request is ready for approval yet." />
        <CompactTable title="Blocked or in progress" items={blocked} empty="No blocked request found." />
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="glass-tile p-5">
          <p className="section-label">Workflow status</p>
          <h2 className="mt-2 text-2xl font-black text-white">Backend review operations wiring.</h2>
          <div className="mt-5 grid gap-3 text-sm text-slate-300">
            <p><b>Status:</b> {asText(status?.status || status?.phase || status?.ok)}</p>
            <p><b>Storage:</b> {asText(status?.storage || status?.storage_mode || "local-first JSONL")}</p>
            <p><b>Rule:</b> {asText(status?.real_only_note || board?.real_only_note, "Real-only output and no certified-audit claim.")}</p>
          </div>
          <details className="mt-5 rounded-2xl border border-white/10 bg-black/20 p-4">
            <summary className="cursor-pointer font-black text-white">Raw status</summary>
            <JsonBlock value={status} />
          </details>
        </div>
        <div className="glass-tile p-5">
          <p className="section-label">Last action result</p>
          <h2 className="mt-2 text-2xl font-black text-white">Real API response.</h2>
          {activeResult ? <JsonBlock value={activeResult} /> : <p className="mt-4 text-sm text-slate-400">Run an action to see the backend response.</p>}
        </div>
      </section>
    </main>
  );
}
