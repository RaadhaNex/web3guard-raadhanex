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
  const scoreLabel = report.combined.overall_score !== null && report.combined.overall_score !== undefined ? "Full weighted score" : "Available partial score";
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
    <div className="card p-6 print:border-0 print:bg-white print:text-black">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start print:block">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.28em] text-cyan print:text-black">final combined report</p>
          <h2 className="mt-2 text-2xl font-black text-white print:text-black">{report.project_name}</h2>
          <p className="mono mt-2 break-all text-xs text-slate-400 print:text-black">{report.report_id}</p>
          <p className="mono mt-1 break-all text-[11px] text-slate-500 print:text-black">hash: {report.report_hash}</p>
        </div>
        <div className="flex flex-wrap gap-2 print:hidden">
          <button type="button" className="btn-secondary" onClick={copyMarkdown}>{copied ? "Copied" : "Copy markdown"}</button>
          <a className="btn-secondary" href={markdownBlobUrl} download={`${report.report_id}.md`}>Download MD</a>
          <a className="btn-secondary" href={jsonBlobUrl} download={`${report.report_id}.json`}>Download JSON</a>
          <button type="button" className="btn-primary" onClick={() => window.print()}>Print / Save PDF</button>
        </div>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-4 print:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 print:border-black/20 print:bg-white">
          <p className="text-xs text-slate-500 print:text-black">{scoreLabel}</p>
          <p className="mt-1 text-4xl font-black text-white print:text-black">{score ?? "N/A"}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 print:border-black/20 print:bg-white">
          <p className="text-xs text-slate-500 print:text-black">Risk label</p>
          <p className="mt-1 text-lg font-black text-white print:text-black">{report.combined.risk_label}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 print:border-black/20 print:bg-white">
          <p className="text-xs text-slate-500 print:text-black">Coverage</p>
          <p className="mt-1 text-2xl font-black text-white print:text-black">{report.coverage.assessed_count}/{report.coverage.total_modules}</p>
          <p className="mt-1 text-xs text-slate-400 print:text-black">{report.coverage.coverage_percent}% · {report.score_confidence}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 print:border-black/20 print:bg-white">
          <p className="text-xs text-slate-500 print:text-black">Recommended package</p>
          <p className="mt-1 text-sm font-black text-white print:text-black">{report.package_recommendation.package}</p>
        </div>
      </div>

      <section className="mt-6">
        <h3 className="text-lg font-black text-white print:text-black">Executive summary</h3>
        <p className="mt-2 text-sm leading-6 text-slate-300 print:text-black">{report.executive_summary}</p>
        <p className="mt-2 text-sm leading-6 text-slate-400 print:text-black">{report.risk_narrative}</p>
      </section>

      <section className="mt-6 rounded-2xl border border-cyan/20 bg-cyan/10 p-4 print:border-black/20 print:bg-white">
        <h3 className="font-black text-white print:text-black">Coverage note</h3>
        <p className="mt-2 text-sm leading-6 text-slate-200 print:text-black">{report.coverage.note}</p>
        {report.coverage.missing_modules.length > 0 && (
          <p className="mt-2 text-xs text-slate-300 print:text-black">Missing: {report.coverage.missing_modules.join(", ")}</p>
        )}
      </section>

      {report.ai_summary && (
        <section className="mt-6 rounded-2xl border border-cyan/20 bg-cyan/10 p-4 print:border-black/20 print:bg-white">
          <div className="flex flex-wrap items-center gap-2">
            <span className="badge">AI mode: {report.ai_summary.status}</span>
            <span className="badge">Provider: {report.ai_summary.provider}</span>
            <span className="badge">Language: {report.ai_summary.language}</span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-200 print:text-black">{report.ai_summary.summary}</p>
          <p className="mt-2 text-sm leading-6 text-slate-300 print:text-black">{report.ai_summary.manual_review_note}</p>
        </section>
      )}

      <section className="mt-6">
        <h3 className="text-lg font-black text-white print:text-black">Weighted module matrix</h3>
        <div className="mt-3 overflow-hidden rounded-2xl border border-white/10 print:border-black/20">
          <div className="grid grid-cols-[1.2fr_0.5fr_0.7fr_1fr] bg-white/[0.04] text-xs font-black uppercase tracking-wider text-slate-400 print:bg-white print:text-black">
            <div className="p-3">Module</div><div className="p-3">Weight</div><div className="p-3">Score</div><div className="p-3">Status</div>
          </div>
          {report.module_matrix.map((module) => (
            <div key={module.module} className="grid grid-cols-[1.2fr_0.5fr_0.7fr_1fr] border-t border-white/10 text-sm print:border-black/20">
              <div className="p-3"><p className="font-black text-white print:text-black">{module.label}</p><p className="text-xs text-slate-500 print:text-black">{module.evidence}</p></div>
              <div className="p-3 text-slate-300 print:text-black">{module.weight_percent}%</div>
              <div className="p-3 font-black text-cyan print:text-black">{module.score ?? "N/A"}</div>
              <div className="p-3 text-slate-300 print:text-black">{module.status} · {module.risk_label}</div>
            </div>
          ))}
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
            <div key={`${item.step}-${item.title}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 print:border-black/20 print:bg-white">
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-sm font-black text-slate-400 print:text-black">#{item.step}</span>
                <SeverityBadge severity={item.severity} />
                <p className="font-black text-white print:text-black">{item.title}</p>
              </div>
              <p className="mt-1 text-xs text-slate-500 print:text-black">{item.module_label ?? item.module}</p>
              <p className="mt-2 text-sm text-slate-300 print:text-black">{item.recommended_action}</p>
              {item.business_impact && <p className="mt-2 text-xs text-slate-400 print:text-black">Impact: {item.business_impact}</p>}
            </div>
          )) : <p className="text-sm text-slate-400 print:text-black">No priority actions found for the provided modules.</p>}
        </div>
      </section>

      <section className="mt-6">
        <h3 className="text-lg font-black text-white print:text-black">Before launch checklist</h3>
        <ul className="mt-2 grid gap-2 text-sm leading-6 text-slate-300 sm:grid-cols-2 print:text-black">
          {report.before_launch_checklist.map((item) => <li key={item} className="rounded-xl border border-white/10 p-3 print:border-black/20">□ {item}</li>)}
        </ul>
      </section>

      <section className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-4 print:border-black/20 print:bg-white">
        <h3 className="font-black text-white print:text-black">Client delivery + public sharing</h3>
        <p className="mt-2 text-sm text-slate-300 print:text-black">Public wording: {report.client_delivery.public_wording}</p>
        <p className="mt-2 text-sm text-slate-400 print:text-black">{report.public_summary_note}</p>
        <p className="mt-2 text-xs text-slate-500 print:text-black">Do not use: {report.client_delivery.do_not_use_wording.join(", ")}</p>
      </section>

      <section className="mt-6">
        <h3 className="text-lg font-black text-white print:text-black">Limitations</h3>
        <ul className="mt-2 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-300 print:text-black">
          {report.limitations.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>

      <section className="mt-6 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 print:border-black/20 print:bg-white">
        <h3 className="font-black text-white print:text-black">Disclaimer</h3>
        <p className="mt-2 text-sm leading-6 text-amber-100 print:text-black">{report.disclaimer}</p>
      </section>
    </div>
  );
}
