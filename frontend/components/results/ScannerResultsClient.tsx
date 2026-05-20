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
  const [slitherJson, setSlitherJson] = useState("");
  const [packageJson, setPackageJson] = useState("");
  const [includeImportedSlither, setIncludeImportedSlither] = useState(false);
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
      ["Advisories", result.summary.external_advisory_count],
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
        package_json: packageJson.trim() ? packageJson : null,
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
    <div className="result-engine-shell scroll-motion-ready">
      <section className="result-input-console">
        <div className="result-console-head">
          <div>
            <p className="video-section-kicker">LIVE PREVIEW</p>
            <h2>Use supplied evidence to create result cards.</h2>
          </div>
          <span className={statusClass(status?.slither_status || "Not assessed yet")}>Slither: {status?.slither_status || "checking"}</span>
        </div>

        <div className="result-form-grid">
          <label>
            <span>Project label</span>
            <input value={projectName} onChange={(event) => setProjectName(event.target.value)} />
          </label>

          <div className="result-toggle-stack">
            <label>
              <input type="checkbox" checked={includeImportedSlither} onChange={(event) => setIncludeImportedSlither(event.target.checked)} />
              <span>Include supplied Slither JSON</span>
            </label>
            <label>
              <input type="checkbox" checked={runStaticTools} onChange={(event) => setRunStaticTools(event.target.checked)} />
              <span>Try real backend tools if installed</span>
            </label>
            <label>
              <input type="checkbox" checked={liveDependencyLookup} onChange={(event) => setLiveDependencyLookup(event.target.checked)} />
              <span>Use live OSV/CISA only if provider flags allow</span>
            </label>
          </div>
        </div>

        <details className="result-evidence-drawer">
          <summary>Optional evidence payloads</summary>
          <div className="result-evidence-grid">
            <label>
              <span>Slither JSON</span>
              <textarea value={slitherJson} onChange={(event) => setSlitherJson(event.target.value)} rows={8} placeholder={sampleSlitherJson} />
            </label>
            <label>
              <span>package.json</span>
              <textarea value={packageJson} onChange={(event) => setPackageJson(event.target.value)} rows={8} placeholder={samplePackageJson} />
            </label>
          </div>
        </details>

        <button type="button" onClick={runEvaluation} disabled={loading} className="result-run-button disabled:cursor-not-allowed disabled:opacity-60">
          {loading ? "Evaluating evidence..." : "Evaluate result preview →"}
        </button>
        {error ? <p className="result-error-box">{error}</p> : null}
      </section>

      <section className="result-output-console">
        <div className="result-console-head">
          <div>
            <p className="video-section-kicker">OUTPUT</p>
            <h2>Findings, gaps, and report action.</h2>
          </div>
          {result ? <span className={statusClass(result.overall_status)}>{result.overall_status}</span> : <span className="badge">Waiting</span>}
        </div>

        {!result ? (
          <div className="result-empty-state">
            <strong>No preview generated yet.</strong>
            <p>Add evidence or run a safe preview to see backend result states. Empty modules must remain Not Assessed.</p>
          </div>
        ) : (
          <>
            <div className="result-metric-grid">
              {summaryCards.map(([label, value]) => (
                <article key={label} className="result-metric-card">
                  <span>{label}</span>
                  <strong>{value}</strong>
                </article>
              ))}
            </div>

            <div className="result-finding-stack">
              {result.findings.length ? result.findings.map((finding) => (
                <article key={finding.id} className="result-finding-card">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={severityClass(finding.severity)}>{finding.severity}</span>
                    <span className="badge">{finding.source}</span>
                    <span className="badge">{finding.confidence || "medium"} confidence</span>
                  </div>
                  <h3>{finding.title}</h3>
                  <p>{finding.description}</p>
                  {finding.recommendation ? <b>Fix: {finding.recommendation}</b> : null}
                  <small>Evidence: {finding.evidence_id || "provided payload"} · {finding.limitation || "pre-audit context"}</small>
                </article>
              )) : (
                <div className="result-empty-state">
                  <strong>No real findings in this preview.</strong>
                  <p>This does not mean secure. Complete missing evidence and manual review before launch decisions.</p>
                </div>
              )}
            </div>

            <div className="result-gap-panel">
              <h3>Not assessed / setup required</h3>
              {result.not_assessed_modules.map((item) => (
                <article key={`${item.module}-${item.status}`}>
                  <div>
                    <span className={statusClass(item.status)}>{item.status}</span>
                    <strong>{item.module}</strong>
                  </div>
                  <p>{item.reason}</p>
                  <small>Next: {item.enable_next}</small>
                </article>
              ))}
            </div>

            <div className="result-actions-panel">
              <h3>Priority path</h3>
              <ul>
                {result.priority_actions.map((action) => <li key={action}>{action}</li>)}
              </ul>
              <div className="mt-5 flex flex-wrap gap-3">
                <button type="button" onClick={generateReport} disabled={reportLoading} className="video-hero-primary disabled:cursor-not-allowed disabled:opacity-60">
                  {reportLoading ? "Generating report..." : "Generate pilot report"}
                </button>
                <Link href="/pricing" className="video-hero-secondary">{result.pilot_report_cta.paid_cta}</Link>
              </div>
              <p className="mt-3 text-xs text-slate-500">Payment state: {result.pilot_report_cta.payment_status} — {result.pilot_report_cta.payment_next_step}</p>
            </div>
          </>
        )}

        {report ? (
          <div className="result-report-card">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="video-section-kicker">PILOT REPORT</p>
                <h3>{report.report_id}</h3>
              </div>
              <span className="badge badge-cyan">Hash {report.report_hash}</span>
            </div>
            <p>{report.executive_summary.headline}</p>
            <div className="result-metric-grid">
              <article className="result-metric-card"><span>Findings</span><strong>{report.executive_summary.real_findings_count}</strong></article>
              <article className="result-metric-card"><span>Not assessed</span><strong>{report.executive_summary.not_assessed_count}</strong></article>
            </div>
            <ul>
              {report.limitations.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
        ) : null}
      </section>
    </div>
  );
}
