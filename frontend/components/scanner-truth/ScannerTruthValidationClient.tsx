"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { loadLatestUnifiedScan } from "@/lib/latestUnifiedScan";
import { CommandEmptyState, CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";
import { StatusPill } from "@/components/ui/StatusPill";
import type { UnifiedUrlScanResponse } from "@/lib/types";

type StatusResponse = {
  ok: boolean;
  phase: string;
  version: string;
  purpose: string;
  what_this_does: string[];
  what_this_does_not_do: string[];
  required_disclaimer: string;
};

type Issue = {
  severity: string;
  title: string;
  detail: string;
  action: string;
  path?: string;
};

type ModuleTruthRow = {
  surface: string;
  label: string;
  status: string;
  assessed: boolean;
  score?: number | null;
  evidence_state: string;
  findings_count?: number;
  critical_high_count?: number;
  issue_count: number;
  action: string;
};

type SamplePlanItem = {
  id: string;
  title: string;
  steps: string[];
  pass_condition: string;
};

type TruthResult = {
  ok: boolean;
  phase: string;
  engine_version: string;
  generated_at: string;
  project_name: string;
  report_id?: string | null;
  truth_score: number;
  verdict: string;
  blockers: Issue[];
  warnings: Issue[];
  passed_checks: string[];
  module_truth_table: ModuleTruthRow[];
  surface_truth: Record<string, unknown>;
  report_mapping: Record<string, unknown>;
  next_actions: string[];
  manual_sample_plan: SamplePlanItem[];
  safe_public_summary: string;
};

type SamplePlanResponse = {
  ok: boolean;
  sample_validation_plan: SamplePlanItem[];
  real_only_note: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown, fallback = "") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function asNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="mono max-h-96 overflow-auto rounded-2xl border border-white/10 bg-black/35 p-4 text-xs leading-5 text-slate-300">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function IssueCard({ issue }: { issue: Issue }) {
  const tone = issue.severity === "critical" || issue.severity === "high"
    ? "border-red-300/25 bg-red-500/10 text-red-100"
    : issue.severity === "medium"
      ? "border-amber-300/25 bg-amber-400/10 text-amber-100"
      : "border-cyan/20 bg-cyan/10 text-cyan-50";
  return (
    <div className={`rounded-2xl border p-4 ${tone}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <b className="text-sm text-white">{issue.title}</b>
        <span className="rounded-full border border-white/15 px-2.5 py-1 text-[11px] font-black uppercase tracking-[0.14em]">{issue.severity}</span>
      </div>
      <p className="mt-2 text-sm leading-6 opacity-90">{issue.detail}</p>
      <p className="mt-2 text-xs font-bold uppercase tracking-[0.14em] text-white/80">Action: {issue.action}</p>
      {issue.path ? <p className="mt-1 mono text-[11px] opacity-70">{issue.path}</p> : null}
    </div>
  );
}

function ScoreRing({ score }: { score: number }) {
  const label = score >= 85 ? "Beta proof-ready" : score >= 70 ? "Fix warnings" : "Needs QA";
  return (
    <div className="rounded-[2rem] border border-cyan/20 bg-cyan/10 p-6 text-center shadow-2xl shadow-cyan-950/20">
      <p className="section-label">Internal truth score</p>
      <div className="mt-4 text-6xl font-black tracking-[-0.08em] text-white">{score}</div>
      <p className="mt-2 text-sm font-black uppercase tracking-[0.18em] text-cyan">{label}</p>
      <p className="mt-3 text-xs leading-5 text-slate-400">Internal QA score only. Not a customer security score, audit score, or guarantee.</p>
    </div>
  );
}

function ReportMapping({ mapping }: { mapping: Record<string, unknown> }) {
  const formats = Array.isArray(mapping.delivery_formats) ? mapping.delivery_formats.map(String) : [];
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {[
        ["Coverage", `${asNumber(mapping.assessed_count) ?? "?"}/${asNumber(mapping.total_modules) ?? "?"}`],
        ["Module matrix", `${asNumber(mapping.module_matrix_count) ?? 0} rows`],
        ["Priority actions", `${asNumber(mapping.priority_action_count) ?? 0}`],
        ["Markdown", mapping.has_markdown_report ? "Present" : "Missing"],
        ["JSON export", mapping.has_json_export ? "Present" : "Missing"],
        ["Formats", formats.length ? formats.join(", ") : "Not listed"],
      ].map(([label, value]) => (
        <div key={label} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">{label}</p>
          <p className="mt-2 text-sm font-bold text-white">{String(value)}</p>
        </div>
      ))}
    </div>
  );
}

function SurfaceTruth({ value }: { value: Record<string, unknown> }) {
  const items = Object.entries(value);
  return (
    <div className="grid gap-3">
      {items.map(([key, raw]) => {
        const record = isRecord(raw) ? raw : {};
        const state = asString(record.state, asString(record.osv_state, "Not Assessed"));
        return (
          <div key={key} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <b className="text-white">{key.replaceAll("_", " ")}</b>
              <StatusPill status={state} />
            </div>
            <div className="mt-3 grid gap-2 sm:grid-cols-3">
              {Object.entries(record).slice(0, 6).map(([label, entry]) => (
                <div key={label} className="rounded-xl bg-black/20 p-3">
                  <p className="text-[11px] font-black uppercase tracking-[0.14em] text-slate-500">{label}</p>
                  <p className="mt-1 truncate text-xs text-slate-300">{typeof entry === "object" ? JSON.stringify(entry) : String(entry)}</p>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function ScannerTruthValidationClient() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [samplePlan, setSamplePlan] = useState<SamplePlanResponse | null>(null);
  const [latest, setLatest] = useState<UnifiedUrlScanResponse | null>(null);
  const [result, setResult] = useState<TruthResult | null>(null);
  const [rawOverride, setRawOverride] = useState("");
  const [showRaw, setShowRaw] = useState(false);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [statusData, planData] = await Promise.all([
          apiGet<StatusResponse>("/scanner-truth/status"),
          apiGet<SamplePlanResponse>("/scanner-truth/sample-plan"),
        ]);
        setStatus(statusData);
        setSamplePlan(planData);
        setLatest(loadLatestUnifiedScan());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load scanner truth validation.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const selectedPayload = useMemo(() => {
    if (rawOverride.trim()) {
      try {
        const parsed: unknown = JSON.parse(rawOverride);
        return isRecord(parsed) ? parsed : null;
      } catch {
        return null;
      }
    }
    return latest;
  }, [latest, rawOverride]);

  async function runValidation() {
    setError(null);
    setRunning(true);
    try {
      if (!selectedPayload) {
        throw new Error("No valid latest scan payload found. Run unified scan first or paste JSON payload here.");
      }
      const response = await apiPost<TruthResult>("/scanner-truth/validate", {
        project_name: asString(selectedPayload.project_name, "Latest Web3Guard scan"),
        unified_scan_result: selectedPayload,
        real_only_acknowledged: true,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Truth validation failed.");
    } finally {
      setRunning(false);
    }
  }

  if (loading) return <CommandLoadingState label="Loading scanner truth validation..." />;

  return (
    <section className="mt-6 grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <div className="space-y-6">
        {error ? <CommandNotice tone="danger" title="Truth validation error" text={error} /> : null}

        <article className="clean-panel p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Phase 44</p>
              <h2 className="mt-2 text-2xl font-black text-white">Scanner Truth Validation</h2>
            </div>
            <StatusPill status={status?.ok ? "Validation live" : "Not assessed"} />
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-400">{status?.purpose}</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {(status?.what_this_does || []).slice(0, 4).map((item) => (
              <div key={item} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm leading-6 text-slate-300">{item}</div>
            ))}
          </div>
          <CommandNotice tone="info" title="No repeated setup work" text="This phase does not install Slither/Semgrep again. It validates whether existing real output is mapped truthfully into Results and Report." />
          <div className="mt-5 flex flex-wrap gap-3">
            <button className="btn-primary" onClick={runValidation} disabled={running}>{running ? "Validating..." : "Validate latest scan truth"}</button>
            <button className="btn-secondary" onClick={() => setLatest(loadLatestUnifiedScan())}>Reload latest scan</button>
            <Link href="/scanner/unified-url" className="btn-secondary">Run unified scan</Link>
          </div>
        </article>

        <article className="clean-panel p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Current payload</p>
              <h2 className="mt-2 text-2xl font-black text-white">Latest scan source</h2>
            </div>
            <StatusPill status={latest ? "Latest scan found" : "No latest scan"} />
          </div>
          {latest ? (
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Report ID</p>
                <p className="mt-2 break-all text-sm font-bold text-white">{latest.report_id}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Website</p>
                <p className="mt-2 break-all text-sm font-bold text-white">{latest.website_url}</p>
              </div>
            </div>
          ) : (
            <CommandEmptyState title="No latest scan found" text="Run the unified scanner first, or paste a real unified scan JSON payload below for validation." actionHref="/scanner/unified-url" actionLabel="Open scanner" />
          )}
          <div className="mt-5">
            <label className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Optional: paste unified scan JSON</label>
            <textarea
              value={rawOverride}
              onChange={(event) => setRawOverride(event.target.value)}
              placeholder="Paste real unified scan JSON here if localStorage does not have the latest scan."
              className="mt-2 min-h-36 w-full rounded-2xl border border-white/10 bg-black/30 p-4 mono text-xs text-slate-200 outline-none focus:border-cyan/50"
            />
          </div>
        </article>

        <article className="clean-panel p-6">
          <p className="section-label">Manual proof plan</p>
          <h2 className="mt-2 text-2xl font-black text-white">Samples to run after patch</h2>
          <div className="mt-5 grid gap-3">
            {(samplePlan?.sample_validation_plan || result?.manual_sample_plan || []).map((item) => (
              <div key={item.id} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4">
                <b className="text-white">{item.title}</b>
                <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm leading-6 text-slate-400">
                  {item.steps.map((step) => <li key={step}>{step}</li>)}
                </ol>
                <p className="mt-3 rounded-xl border border-emerald-300/20 bg-emerald-400/10 p-3 text-xs leading-5 text-emerald-100">Pass: {item.pass_condition}</p>
              </div>
            ))}
          </div>
        </article>
      </div>

      <div className="space-y-6">
        {result ? (
          <>
            <ScoreRing score={result.truth_score} />

            <article className="clean-panel p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="section-label">Verdict</p>
                  <h2 className="mt-2 text-2xl font-black text-white">{result.verdict}</h2>
                </div>
                <StatusPill status={result.blockers.length ? "Blockers found" : "No blockers"} />
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-400">{result.safe_public_summary}</p>
              <div className="mt-5 grid gap-3">
                {result.next_actions.map((action) => (
                  <div key={action} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm font-semibold text-slate-300">{action}</div>
                ))}
              </div>
            </article>

            <article className="clean-panel p-6">
              <p className="section-label">Module truth table</p>
              <h2 className="mt-2 text-2xl font-black text-white">Assessed vs missing proof</h2>
              <div className="mt-5 overflow-x-auto rounded-2xl border border-white/10">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead className="bg-white/[0.04] text-xs uppercase tracking-[0.16em] text-slate-500">
                    <tr>
                      <th className="p-3">Surface</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Score</th>
                      <th className="p-3">Evidence state</th>
                      <th className="p-3">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.module_truth_table.map((row) => (
                      <tr key={row.surface} className="border-t border-white/10">
                        <td className="p-3 font-bold text-white">{row.label}</td>
                        <td className="p-3"><StatusPill status={row.status} /></td>
                        <td className="p-3 text-slate-300">{row.score ?? "—"}</td>
                        <td className="p-3 mono text-xs text-slate-400">{row.evidence_state}</td>
                        <td className="p-3 text-slate-300">{row.action}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </article>

            {result.blockers.length ? (
              <article className="clean-panel p-6">
                <p className="section-label">Must fix</p>
                <h2 className="mt-2 text-2xl font-black text-white">Truth blockers</h2>
                <div className="mt-5 grid gap-3">{result.blockers.map((issue, index) => <IssueCard key={`${issue.title}-${index}`} issue={issue} />)}</div>
              </article>
            ) : null}

            <article className="clean-panel p-6">
              <p className="section-label">Warnings</p>
              <h2 className="mt-2 text-2xl font-black text-white">Polish before public demo</h2>
              <div className="mt-5 grid gap-3">
                {result.warnings.length ? result.warnings.map((issue, index) => <IssueCard key={`${issue.title}-${index}`} issue={issue} />) : <CommandNotice tone="success" title="No warning gaps" text="Current payload passed the warning-level checks." />}
              </div>
            </article>

            <article className="clean-panel p-6">
              <p className="section-label">Surface truth</p>
              <h2 className="mt-2 text-2xl font-black text-white">Static / GitHub / API evidence</h2>
              <div className="mt-5"><SurfaceTruth value={result.surface_truth} /></div>
            </article>

            <article className="clean-panel p-6">
              <p className="section-label">Report mapping</p>
              <h2 className="mt-2 text-2xl font-black text-white">Results → Report → Export</h2>
              <div className="mt-5"><ReportMapping mapping={result.report_mapping} /></div>
            </article>

            <article className="clean-panel p-6">
              <button className="btn-secondary" onClick={() => setShowRaw(!showRaw)}>{showRaw ? "Hide raw validation JSON" : "Show raw validation JSON"}</button>
              {showRaw ? <div className="mt-5"><JsonBlock value={result} /></div> : null}
            </article>
          </>
        ) : (
          <CommandEmptyState title="Run truth validation" text="Use this after a real unified scan. It checks whether the output is honest, mapped, and demo-ready without repeating scanner setup work." actionHref="/scanner/unified-url" actionLabel="Open scanner" />
        )}
      </div>
    </section>
  );
}
