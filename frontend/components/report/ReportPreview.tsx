"use client";

import { useMemo, useState } from "react";
import type { CombinedLaunchReport } from "@/lib/types";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

type Props = {
  report: CombinedLaunchReport;
};

const severityOrder = ["critical", "high", "medium", "low", "info"] as const;

export function ReportPreview({ report }: Props) {
  const [copied, setCopied] = useState(false);
  const score = report.combined.overall_score ?? report.combined.available_score ?? null;
  const scoreLabel = report.combined.overall_score !== null && report.combined.overall_score !== undefined ? "Weighted score" : "Available score";
  const markdownBlobUrl = useMemo(() => {
    if (typeof window === "undefined") return "";
    return URL.createObjectURL(new Blob([report.markdown_report], { type: "text/markdown" }));
  }, [report.markdown_report]);
  const jsonBlobUrl = useMemo(() => {
    if (typeof window === "undefined") return "";
    return URL.createObjectURL(new Blob([JSON.stringify(report.json_export ?? report, null, 2)], { type: "application/json" }));
  }, [report]);

  async function copyMarkdown() {
    await navigator.clipboard.writeText(report.markdown_report);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <div className="card p-5 sm:p-6 print:border-0 print:bg-white print:text-black">
      <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start print:block">
        <div className="min-w-0">
          <p className="section-label print:text-black">Professional report preview</p>
          <h2 className="mt-2 text-2xl font-black text-white print:text-black">{report.project_name}</h2>
          <div className="mt-3 grid gap-2 text-xs text-slate-400 print:text-black">
            <p className="mono break-all">Report ID: {report.report_id}</p>
            <p className="mono break-all">Hash: {report.report_hash}</p>
          </div>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 lg:min-w-[27rem] print:hidden">
          <button type="button" className="btn-secondary" onClick={copyMarkdown}>{copied ? "Copied" : "Copy markdown"}</button>
          <a className="btn-secondary" href={markdownBlobUrl} download={`${report.report_id}.md`}>Download MD</a>
          <a className="btn-secondary" href={jsonBlobUrl} download={`${report.report_id}.json`}>Download JSON</a>
          <button type="button" className="btn-primary" onClick={() => window.print()}>Print / save PDF</button>
        </div>
      </div>

      <div className="mt-6 rounded-3xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm leading-6 text-amber-100 print:border-black/20 print:bg-white print:text-black">
        This report is a pre-audit readiness artifact. It is not a certified audit, penetration test, financial/legal opinion, or guarantee of security.
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4 print:grid-cols-4">
        <Metric label={scoreLabel} value={score ?? "N/A"} />
        <Metric label="Risk label" value={report.combined.risk_label} />
        <Metric label="Coverage" value={`${report.coverage.assessed_count}/${report.coverage.total_modules}`} helper={`${report.coverage.coverage_percent}% · ${report.score_confidence}`} />
        <Metric label="Recommended package" value={report.package_recommendation.package} />
      </div>

      <section className="mt-6 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="glass-tile p-5 print:border-black/20 print:bg-white">
          <h3 className="text-lg font-black text-white print:text-black">Executive summary</h3>
          <p className="mt-2 text-sm leading-6 text-slate-300 print:text-black">{report.executive_summary}</p>
          <p className="mt-2 text-sm leading-6 text-slate-400 print:text-black">{report.risk_narrative}</p>
        </div>
        <div className="glass-tile p-5 print:border-black/20 print:bg-white">
          <h3 className="text-lg font-black text-white print:text-black">Coverage note</h3>
          <p className="mt-2 text-sm leading-6 text-slate-300 print:text-black">{report.coverage.note}</p>
          {report.coverage.missing_modules.length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {report.coverage.missing_modules.map((item) => <span key={item} className="badge badge-amber print:text-black">{item}</span>)}
            </div>
          ) : null}
        </div>
      </section>

      {report.ai_summary ? (
        <section className="mt-6 rounded-3xl border border-cyan/20 bg-cyan/10 p-4 print:border-black/20 print:bg-white">
          <div className="flex flex-wrap items-center gap-2">
            <span className="badge">AI mode: {report.ai_summary.status}</span>
            <span className="badge">Provider: {report.ai_summary.provider}</span>
            <span className="badge">Language: {report.ai_summary.language}</span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-200 print:text-black">{report.ai_summary.summary}</p>
          <p className="mt-2 text-sm leading-6 text-slate-300 print:text-black">{report.ai_summary.manual_review_note}</p>
        </section>
      ) : null}

      <section className="mt-6">
        <h3 className="text-lg font-black text-white print:text-black">Weighted module matrix</h3>
        <div className="mt-3 overflow-x-auto rounded-3xl border border-white/10 print:border-black/20">
          <table className="min-w-[820px] w-full border-collapse text-sm">
            <thead className="bg-white/[0.04] text-xs font-black uppercase tracking-wider text-slate-400 print:bg-white print:text-black">
              <tr>
                <th className="p-3 text-left">Module</th>
                <th className="p-3 text-left">Weight</th>
                <th className="p-3 text-left">Score</th>
                <th className="p-3 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {report.module_matrix.map((module) => (
                <tr key={module.module} className="border-t border-white/10 print:border-black/20">
                  <td className="p-3"><p className="font-black text-white print:text-black">{module.label}</p><p className="text-xs text-slate-500 print:text-black">{module.evidence}</p></td>
                  <td className="p-3 text-slate-300 print:text-black">{module.weight_percent}%</td>
                  <td className="p-3 font-black text-cyan print:text-black">{module.score ?? "N/A"}</td>
                  <td className="p-3 text-slate-300 print:text-black">{module.status} · {module.risk_label}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-6">
        <h3 className="text-lg font-black text-white print:text-black">Severity breakdown</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {severityOrder.map((severity) => (
            <span key={severity} className="badge"><span className="capitalize">{severity}</span>: {report.severity_breakdown[severity] ?? 0}</span>
          ))}
        </div>
      </section>

      <section className="mt-6">
        <h3 className="text-lg font-black text-white print:text-black">Priority action plan</h3>
        <div className="mt-3 space-y-3">
          {report.priority_action_plan.length ? report.priority_action_plan.map((item) => (
            <div key={`${item.step}-${item.title}`} className="rounded-3xl border border-white/10 bg-white/[0.03] p-4 print:border-black/20 print:bg-white">
              <div className="flex flex-wrap items-center gap-3">
                <span className="kbd-chip print:text-black">#{item.step}</span>
                <SeverityBadge severity={item.severity} />
                <p className="font-black text-white print:text-black">{item.title}</p>
              </div>
              <p className="mt-1 text-xs text-slate-500 print:text-black">{item.module_label ?? item.module}</p>
              <p className="mt-2 text-sm text-slate-300 print:text-black">{item.recommended_action}</p>
              {item.business_impact ? <p className="mt-2 text-xs text-slate-400 print:text-black">Impact: {item.business_impact}</p> : null}
            </div>
          )) : <p className="text-sm text-slate-400 print:text-black">No priority actions found for the provided modules.</p>}
        </div>
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="text-lg font-black text-white print:text-black">Before launch checklist</h3>
          <ul className="mt-2 grid gap-2 text-sm leading-6 text-slate-300 print:text-black">
            {report.before_launch_checklist.map((item) => <li key={item} className="rounded-xl border border-white/10 p-3 print:border-black/20">□ {item}</li>)}
          </ul>
        </div>
        <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-4 print:border-black/20 print:bg-white">
          <h3 className="font-black text-white print:text-black">Client delivery + public sharing</h3>
          <p className="mt-2 text-sm text-slate-300 print:text-black">Public wording: {report.client_delivery.public_wording}</p>
          <p className="mt-2 text-sm text-slate-400 print:text-black">{report.public_summary_note}</p>
          <p className="mt-2 text-xs text-slate-500 print:text-black">Do not use: {report.client_delivery.do_not_use_wording.join(", ")}</p>
        </div>
      </section>

      <section className="mt-6">
        <h3 className="text-lg font-black text-white print:text-black">Limitations</h3>
        <ul className="mt-2 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-300 print:text-black">
          {report.limitations.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>

      <section className="mt-6 rounded-3xl border border-amber-400/20 bg-amber-400/10 p-4 print:border-black/20 print:bg-white">
        <h3 className="font-black text-white print:text-black">Disclaimer</h3>
        <p className="mt-2 text-sm leading-6 text-amber-100 print:text-black">{report.disclaimer}</p>
      </section>
    </div>
  );
}

function Metric({ label, value, helper }: { label: string; value: string | number; helper?: string }) {
  return (
    <div className="stat-slab p-4 print:border-black/20 print:bg-white">
      <p className="text-xs text-slate-500 print:text-black">{label}</p>
      <p className="mt-1 truncate text-2xl font-black text-white print:text-black">{value}</p>
      {helper ? <p className="mt-1 text-xs text-slate-400 print:text-black">{helper}</p> : null}
    </div>
  );
}
