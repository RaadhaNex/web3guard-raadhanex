"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";

type Finding = {
  id: string;
  module: string;
  kind: string;
  severity: string;
  status: string;
  title: string;
  description: string;
  source: string;
  confidence?: string;
  evidence_id?: string;
  recommendation?: string;
  limitation?: string;
};

type NotAssessedModule = {
  module: string;
  status: string;
  reason: string;
  enable_next: string;
};

type ScannerResult = {
  ok: boolean;
  version: string;
  result_id: string;
  project_name: string;
  generated_at: string;
  overall_status: string;
  summary: {
    assessed_modules: string[];
    assessed_module_count: number;
    real_findings_count: number;
    tool_findings_count: number;
    external_advisory_count: number;
    not_assessed_count: number;
    severity_breakdown: Record<string, number>;
    launch_blockers: number;
  };
  findings: Finding[];
  not_assessed_modules: NotAssessedModule[];
  priority_actions: string[];
  pilot_report_cta: {
    paid_cta: string;
    payment_status: string;
    payment_next_step: string;
  };
  disclaimer: string;
};

type StatusPayload = {
  ok: boolean;
  version: string;
  slither_status: string;
  razorpay_status: string;
  safe_statuses: string[];
  not_claimed: string[];
};

type PilotReport = {
  ok: boolean;
  report_id: string;
  project_name: string;
  report_hash: string;
  executive_summary: {
    real_findings_count: number;
    not_assessed_count: number;
    headline: string;
  };
  limitations: string[];
};

const sampleSlitherJson = JSON.stringify(
  {
    success: true,
    results: {
      detectors: [
        {
          check: "reentrancy-eth",
          impact: "High",
          description: "Potential reentrancy in withdraw() from imported Slither JSON.",
          elements: [{ source_mapping: { lines: [42] } }],
        },
      ],
    },
  },
  null,
  2
);

const samplePackageJson = JSON.stringify(
  {
    dependencies: {
      lodash: "^4.17.21",
      next: "16.2.6",
    },
  },
  null,
  2
);

function severityClass(severity: string) {
  const value = severity.toLowerCase();
  if (value === "critical") return "badge badge-red";
  if (value === "high") return "badge badge-amber";
  if (value === "medium") return "badge badge-purple";
  return "badge badge-cyan";
}

function statusClass(status: string) {
  if (status === "Assessed") return "badge badge-cyan";
  if (status === "Tool Not Installed" || status === "Needs API Key") return "badge badge-amber";
  if (status === "Manual review required") return "badge badge-purple";
  return "badge";
}

export function ScannerResultsClient() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [projectName, setProjectName] = useState("Pilot Web3 Project");
  const [slitherJson, setSlitherJson] = useState(sampleSlitherJson);
  const [packageJson, setPackageJson] = useState(samplePackageJson);
  const [includeImportedSlither, setIncludeImportedSlither] = useState(true);
  const [runStaticTools, setRunStaticTools] = useState(false);
  const [liveDependencyLookup, setLiveDependencyLookup] = useState(false);
  const [result, setResult] = useState<ScannerResult | null>(null);
  const [report, setReport] = useState<PilotReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<StatusPayload>("/scanner-results/status")
      .then(setStatus)
      .catch((err: Error) => setError(err.message));
  }, []);

  const summaryCards = useMemo(() => {
    if (!result) return [];
    return [
      ["Real findings", result.summary.real_findings_count],
      ["Launch blockers", result.summary.launch_blockers],
      ["External advisories", result.summary.external_advisory_count],
      ["Not assessed", result.summary.not_assessed_count],
    ];
  }, [result]);

  async function runEvaluation() {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const response = await apiPost<ScannerResult>("/scanner-results/evaluate", {
        project_name: projectName,
        slither_json: includeImportedSlither ? slitherJson : null,
        package_json: packageJson,
        run_static_tools: runStaticTools,
        live_dependency_lookup: liveDependencyLookup,
        authorization_confirmed: true,
        real_only_acknowledged: true,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Result engine failed");
    } finally {
      setLoading(false);
    }
  }

  async function generateReport() {
    if (!result) return;
    setReportLoading(true);
    setError(null);
    try {
      const response = await apiPost<PilotReport>("/scanner-results/pilot-report", {
        result,
        real_only_acknowledged: true,
      });
      setReport(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pilot report generation failed");
    } finally {
      setReportLoading(false);
    }
  }

  return (
    <div className="mt-10 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <section className="card p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="section-label">Phase 32 engine</p>
            <h2 className="mt-2 text-2xl font-black text-white">Run a normalized result preview</h2>
          </div>
          <span className={statusClass(status?.slither_status || "Not assessed yet")}>Slither: {status?.slither_status || "checking"}</span>
        </div>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          This preview never invents findings. Imported Slither JSON is marked as imported evidence; live OSV/CISA lookups run only when backend network flags are enabled.
        </p>

        <label className="mt-5 block text-xs font-black uppercase tracking-[0.16em] text-slate-500">Project name</label>
        <input
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
          className="mt-2 w-full rounded-xl border border-white/[0.08] bg-black/30 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan/40"
        />

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <label className="flex items-center gap-3 rounded-xl border border-white/[0.08] bg-white/[0.03] p-3 text-sm text-slate-300">
            <input type="checkbox" checked={includeImportedSlither} onChange={(event) => setIncludeImportedSlither(event.target.checked)} />
            Import Slither JSON sample
          </label>
          <label className="flex items-center gap-3 rounded-xl border border-white/[0.08] bg-white/[0.03] p-3 text-sm text-slate-300">
            <input type="checkbox" checked={runStaticTools} onChange={(event) => setRunStaticTools(event.target.checked)} />
            Try backend static tools
          </label>
          <label className="flex items-center gap-3 rounded-xl border border-white/[0.08] bg-white/[0.03] p-3 text-sm text-slate-300 sm:col-span-2">
            <input type="checkbox" checked={liveDependencyLookup} onChange={(event) => setLiveDependencyLookup(event.target.checked)} />
            Run live OSV/CISA lookup if backend provider flags are enabled
          </label>
        </div>

        <label className="mt-5 block text-xs font-black uppercase tracking-[0.16em] text-slate-500">Slither JSON import</label>
        <textarea
          value={slitherJson}
          onChange={(event) => setSlitherJson(event.target.value)}
          rows={7}
          className="mt-2 w-full rounded-xl border border-white/[0.08] bg-black/30 px-4 py-3 font-mono text-xs text-slate-200 outline-none transition focus:border-cyan/40"
        />

        <label className="mt-5 block text-xs font-black uppercase tracking-[0.16em] text-slate-500">package.json dependency input</label>
        <textarea
          value={packageJson}
          onChange={(event) => setPackageJson(event.target.value)}
          rows={6}
          className="mt-2 w-full rounded-xl border border-white/[0.08] bg-black/30 px-4 py-3 font-mono text-xs text-slate-200 outline-none transition focus:border-cyan/40"
        />

        <button type="button" onClick={runEvaluation} disabled={loading} className="btn-primary mt-5 w-full disabled:cursor-not-allowed disabled:opacity-60">
          {loading ? "Evaluating real evidence..." : "Evaluate scanner result"}
        </button>
        {error ? <p className="mt-4 rounded-xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</p> : null}
      </section>

      <section className="grid gap-5">
        <div className="card p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Result output</p>
              <h2 className="mt-2 text-2xl font-black text-white">Findings, gaps, and next action</h2>
            </div>
            {result ? <span className={statusClass(result.overall_status)}>{result.overall_status}</span> : null}
          </div>

          {!result ? (
            <div className="mt-5 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5 text-sm leading-6 text-slate-400">
              Run the evaluation to see a single normalized result shape. Missing tools remain outside findings, so the report cannot accidentally imply fake coverage.
            </div>
          ) : (
            <>
              <div className="mt-5 grid gap-3 sm:grid-cols-4">
                {summaryCards.map(([label, value]) => (
                  <div key={label} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
                    <p className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">{label}</p>
                    <p className="mt-2 text-2xl font-black text-white">{value}</p>
                  </div>
                ))}
              </div>

              <div className="mt-5 grid gap-3">
                {result.findings.length ? result.findings.map((finding) => (
                  <article key={finding.id} className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={severityClass(finding.severity)}>{finding.severity}</span>
                      <span className="badge">{finding.source}</span>
                      <span className="badge">{finding.confidence || "medium"} confidence</span>
                    </div>
                    <h3 className="mt-3 text-lg font-black text-white">{finding.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-slate-400">{finding.description}</p>
                    <p className="mt-3 text-sm leading-6 text-cyan/90">Fix direction: {finding.recommendation}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-500">Evidence: {finding.evidence_id} · {finding.limitation}</p>
                  </article>
                )) : (
                  <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 text-sm text-slate-400">
                    No real findings were produced in this preview. That does not mean the project is secure; complete the Not Assessed modules and manual review.
                  </div>
                )}
              </div>

              <div className="mt-5 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4">
                <p className="font-black text-amber-100">Not assessed / setup required</p>
                <div className="mt-3 grid gap-3">
                  {result.not_assessed_modules.map((item) => (
                    <div key={`${item.module}-${item.status}`} className="rounded-xl border border-white/[0.08] bg-black/20 p-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={statusClass(item.status)}>{item.status}</span>
                        <p className="font-bold text-white">{item.module}</p>
                      </div>
                      <p className="mt-2 text-sm text-amber-100/80">{item.reason}</p>
                      <p className="mt-1 text-xs text-slate-400">Next: {item.enable_next}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-5 rounded-2xl border border-cyan/15 bg-cyan/[0.06] p-4">
                <p className="font-black text-white">What to fix first</p>
                <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-300">
                  {result.priority_actions.map((action) => <li key={action}>• {action}</li>)}
                </ul>
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                <button type="button" onClick={generateReport} disabled={reportLoading} className="btn-primary disabled:cursor-not-allowed disabled:opacity-60">
                  {reportLoading ? "Generating report..." : "Generate pilot report"}
                </button>
                <Link href="/pricing" className="btn-secondary">{result.pilot_report_cta.paid_cta}</Link>
              </div>
              <p className="mt-3 text-xs text-slate-500">Payment state: {result.pilot_report_cta.payment_status} — {result.pilot_report_cta.payment_next_step}</p>
            </>
          )}
        </div>

        {report ? (
          <div className="card p-5 sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="section-label">Pilot report</p>
                <h2 className="mt-2 text-2xl font-black text-white">{report.report_id}</h2>
              </div>
              <span className="badge badge-cyan">Hash {report.report_hash}</span>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-300">{report.executive_summary.headline}</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-4">
                <p className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">Findings</p>
                <p className="mt-2 text-2xl font-black text-white">{report.executive_summary.real_findings_count}</p>
              </div>
              <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-4">
                <p className="text-xs font-black uppercase tracking-[0.14em] text-slate-500">Not assessed</p>
                <p className="mt-2 text-2xl font-black text-white">{report.executive_summary.not_assessed_count}</p>
              </div>
            </div>
            <ul className="mt-4 space-y-2 text-sm leading-6 text-slate-400">
              {report.limitations.map((item) => <li key={item}>• {item}</li>)}
            </ul>
          </div>
        ) : null}
      </section>
    </div>
  );
}
