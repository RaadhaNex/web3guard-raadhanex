"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { loadLatestUnifiedScan } from "@/lib/latestUnifiedScan";
import type { Finding, Severity, UnifiedModuleCard, UnifiedUrlScanResponse } from "@/lib/types";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

type SurfaceRecord = Record<string, unknown>;

const stateCopy = [
  ["Assessed", "Real backend/tool evidence was supplied and processed."],
  ["Not Assessed", "No evidence was available, so Web3Guard does not guess."],
  ["Tool Not Installed", "A tool exists, but the binary is missing from the tools venv."],
  ["Provider Not Configured", "A provider/env flag/API key is missing, so the result is blocked safely."],
  ["Manual Review Required", "A founder or reviewer must verify this area before launch decisions."],
];

const moduleOrder = ["website", "dapp", "api", "github", "contract", "static_analysis", "wallet", "admin_opsec"];

function isRecord(value: unknown): value is SurfaceRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asRecord(value: unknown): SurfaceRecord {
  return isRecord(value) ? value : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asString(value: unknown, fallback = "—") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

function formatJson(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function toSeverity(value: unknown): Severity {
  return value === "critical" || value === "high" || value === "medium" || value === "low" || value === "info" ? value : "info";
}

function statusClass(status?: string) {
  const text = (status || "").toLowerCase();
  if (text.includes("assessed") && !text.includes("not")) return "badge-green";
  if (text.includes("tool not installed") || text.includes("provider") || text.includes("manual") || text.includes("needs")) return "badge-amber";
  if (text.includes("live") || text.includes("assessed")) return "badge-green";
  return "badge-slate";
}

function scoreText(score?: number | null) {
  return typeof score === "number" ? `${score}/100` : "Not Assessed";
}

function sortCards(cards: UnifiedModuleCard[]) {
  return [...cards].sort((a, b) => {
    const ai = moduleOrder.indexOf(a.module);
    const bi = moduleOrder.indexOf(b.module);
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });
}

function findingFromRecord(value: unknown): Finding | null {
  if (!isRecord(value)) return null;
  return {
    id: asString(value.id, `finding-${asString(value.title, "unknown")}`),
    module: asString(value.module, "static_analysis"),
    severity: toSeverity(value.severity),
    title: asString(value.title, "Untitled finding"),
    description: asString(value.description, "No description provided."),
    affected_line: asNumber(value.affected_line),
    affected_function: typeof value.affected_function === "string" ? value.affected_function : null,
    affected_code: typeof value.affected_code === "string" ? value.affected_code : null,
    confidence: value.confidence === "high" || value.confidence === "medium" || value.confidence === "low" ? value.confidence : "medium",
    source: asString(value.source, "Real backend output"),
    category: typeof value.category === "string" ? value.category : undefined,
    rule_id: typeof value.rule_id === "string" ? value.rule_id : null,
    fingerprint: typeof value.fingerprint === "string" ? value.fingerprint : null,
    business_impact: asString(value.business_impact, "Manual triage recommended."),
    developer_explanation: asString(value.developer_explanation, "Review the raw evidence."),
    recommendation: asString(value.recommendation, "Review and fix before public launch."),
    references: Array.isArray(value.references) ? value.references.filter((item): item is string => typeof item === "string") : [],
    paid_review_recommended: Boolean(value.paid_review_recommended),
    ai_explanation: isRecord(value.ai_explanation) ? value.ai_explanation : null,
  };
}

function ModuleEvidenceCard({ card }: { card: UnifiedModuleCard }) {
  return (
    <article className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/20">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-xl font-black text-white">{card.label}</h2>
          <p className="mt-1 font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">{card.module}</p>
        </div>
        <span className={`badge ${statusClass(card.status)}`}>{card.status || "Not Assessed"}</span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-3">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Score</p>
          <p className="mt-2 text-sm font-black text-white">{scoreText(card.score)}</p>
        </div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-3">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Findings</p>
          <p className="mt-2 text-sm font-black text-white">{card.findings_count} total · {card.critical_high_count} C/H</p>
        </div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-3">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Risk</p>
          <p className="mt-2 text-sm font-black text-white">{card.risk_label || "Not Assessed"}</p>
        </div>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-cyan-200">Evidence</p>
          {card.evidence.length ? (
            <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-300">
              {card.evidence.slice(0, 5).map((item) => <li key={item}>• {item}</li>)}
            </ul>
          ) : <p className="mt-3 text-sm leading-6 text-slate-500">No real evidence was supplied for this module.</p>}
        </div>
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-amber-200">Gap / limitation</p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-300">
            {(card.required_input.length ? card.required_input : card.limitations).slice(0, 5).map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </div>
      </div>
    </article>
  );
}

function FindingCard({ finding }: { finding: Finding }) {
  return (
    <article className="rounded-2xl border border-white/10 bg-black/20 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-black text-white">{finding.title}</h3>
          <p className="mt-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{finding.module} · {finding.source}</p>
        </div>
        <SeverityBadge severity={finding.severity} />
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-300">{finding.description}</p>
      <p className="mt-3 rounded-xl border border-cyan-300/15 bg-cyan-300/[0.04] p-3 text-sm leading-6 text-cyan-50">Fix hint: {finding.recommendation}</p>
      <details className="mt-3 rounded-xl border border-white/[0.07] bg-white/[0.03] p-3 text-xs text-slate-400">
        <summary className="cursor-pointer font-bold text-slate-200">Raw evidence</summary>
        <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap break-words">{formatJson(finding)}</pre>
      </details>
    </article>
  );
}

function StaticAnalysisPanel({ surface }: { surface: SurfaceRecord }) {
  const staticAnalysis = asRecord(surface.static_analysis);
  const tools = asArray(staticAnalysis.tools).filter(isRecord);
  const findings = asArray(staticAnalysis.findings).map(findingFromRecord).filter((item): item is Finding => Boolean(item));
  const messages = asArray(staticAnalysis.status_messages).map(findingFromRecord).filter((item): item is Finding => Boolean(item));

  return (
    <section className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="section-label">Tool output</p>
          <h2 className="mt-2 text-2xl font-black text-white">Slither / Semgrep evidence</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">Real subprocess output appears here only when the backend tools are installed and enabled.</p>
        </div>
        <span className={`badge ${statusClass(asString(staticAnalysis.state, "Not Assessed"))}`}>{asString(staticAnalysis.state, "Not Assessed")}</span>
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-2">
        {tools.length ? tools.map((tool) => (
          <article key={asString(tool.tool)} className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-black capitalize text-white">{asString(tool.tool)}</h3>
              <span className={`badge ${statusClass(asString(tool.state, "Not Assessed"))}`}>{asString(tool.state, "Not Assessed")}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">Installed: {String(Boolean(tool.installed))} · Enabled: {String(Boolean(tool.enabled_by_env))} · Real findings: {String(tool.real_findings ?? 0)}</p>
            {(tool.stderr_tail || tool.stdout_tail) ? (
              <details className="mt-3 rounded-xl border border-white/[0.07] bg-white/[0.03] p-3 text-xs text-slate-400">
                <summary className="cursor-pointer font-bold text-slate-200">Tool log tail</summary>
                <pre className="mt-3 max-h-48 overflow-auto whitespace-pre-wrap break-words">{asString(tool.stderr_tail, "") || asString(tool.stdout_tail, "")}</pre>
              </details>
            ) : null}
          </article>
        )) : (
          <article className="rounded-2xl border border-amber-300/15 bg-amber-300/10 p-4 text-sm leading-6 text-amber-100">No Slither/Semgrep tool run exists for this scan. Paste Solidity source and configure tools to assess this layer.</article>
        )}
      </div>
      <div className="mt-5 grid gap-3">
        {findings.length ? findings.map((finding) => <FindingCard key={finding.id} finding={finding} />) : (
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4 text-sm leading-6 text-slate-400">No parsed Slither/Semgrep vulnerability findings are present. Tool-status messages stay separate and are not treated as fake vulnerabilities.</div>
        )}
        {messages.length ? (
          <details className="rounded-2xl border border-white/[0.07] bg-black/20 p-4 text-sm leading-6 text-slate-300">
            <summary className="cursor-pointer font-black text-white">Tool status messages</summary>
            <ul className="mt-3 space-y-2">
              {messages.map((message) => <li key={message.id}>• {message.title}: {message.description}</li>)}
            </ul>
          </details>
        ) : null}
      </div>
    </section>
  );
}

function GithubDependencyPanel({ surface }: { surface: SurfaceRecord }) {
  const github = asRecord(surface.github_dependency_risk);
  const manifests = asArray(github.dependency_manifests).filter(isRecord);
  const findings = asArray(github.findings).map(findingFromRecord).filter((item): item is Finding => Boolean(item));

  return (
    <section className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="section-label">Repository evidence</p>
          <h2 className="mt-2 text-2xl font-black text-white">GitHub dependency risk</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">Uses only public repo evidence already fetched by the backend. OSV/live dependency lookup is not faked.</p>
        </div>
        <span className={`badge ${statusClass(asString(github.state, "Not Assessed"))}`}>{asString(github.state, "Not Assessed")}</span>
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-4">
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">package.json</p><p className="mt-2 text-lg font-black text-white">{String(github.package_json_count ?? "—")}</p></div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">lockfiles</p><p className="mt-2 text-lg font-black text-white">{String(github.lockfile_count ?? "—")}</p></div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">manifests</p><p className="mt-2 text-lg font-black text-white">{String(github.dependency_manifest_count ?? manifests.length)}</p></div>
        <div className="rounded-2xl border border-amber-300/15 bg-amber-300/10 p-4"><p className="text-xs uppercase tracking-[0.16em] text-amber-200">OSV state</p><p className="mt-2 text-sm font-black text-amber-50">{asString(github.osv_state, "Provider Not Configured")}</p></div>
      </div>
      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {manifests.length ? manifests.map((manifest) => (
          <article key={asString(manifest.path)} className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
            <h3 className="font-black text-white">{asString(manifest.path, "package.json")}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-300">Dependencies: {String(manifest.dependency_count ?? 0)} · test script: {String(Boolean(manifest.has_test_script))} · audit script: {String(Boolean(manifest.has_audit_script))}</p>
            <details className="mt-3 text-xs text-slate-400"><summary className="cursor-pointer font-bold text-slate-200">Security relevant dependencies</summary><pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap break-words">{formatJson(manifest.security_relevant_dependencies ?? [])}</pre></details>
          </article>
        )) : (
          <article className="rounded-2xl border border-white/[0.07] bg-black/20 p-4 text-sm leading-6 text-slate-400">No dependency manifest was available from the current scan. Provide a public GitHub repo URL to assess this layer.</article>
        )}
      </div>
      {findings.length ? <div className="mt-5 grid gap-3">{findings.map((finding) => <FindingCard key={finding.id} finding={finding} />)}</div> : null}
    </section>
  );
}

function ApiExposurePanel({ surface }: { surface: SurfaceRecord }) {
  const api = asRecord(surface.api_admin_exposure);
  const endpoints = asArray(api.safe_endpoints_checked).filter(isRecord);
  const findings = asArray(api.findings).map(findingFromRecord).filter((item): item is Finding => Boolean(item));

  return (
    <section className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="section-label">Safe passive backend checks</p>
          <h2 className="mt-2 text-2xl font-black text-white">API/admin exposure checklist</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">Checks CORS/docs/OpenAPI/GraphQL hints only. No fuzzing, brute force, DoS, credential testing, or auth bypass.</p>
        </div>
        <span className={`badge ${statusClass(asString(api.state, "Not Assessed"))}`}>{asString(api.state, "Not Assessed")}</span>
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-4">
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Endpoints checked</p><p className="mt-2 text-lg font-black text-white">{endpoints.length}</p></div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">OpenAPI</p><p className="mt-2 text-lg font-black text-white">{String(Boolean(api.openapi_detected))}</p></div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">GraphQL</p><p className="mt-2 text-lg font-black text-white">{String(Boolean(api.graphql_detected))}</p></div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Findings</p><p className="mt-2 text-lg font-black text-white">{findings.length}</p></div>
      </div>
      <details className="mt-5 rounded-2xl border border-white/[0.07] bg-black/20 p-4 text-sm leading-6 text-slate-300">
        <summary className="cursor-pointer font-black text-white">Safe endpoint evidence</summary>
        <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-words text-xs text-slate-400">{formatJson(endpoints)}</pre>
      </details>
      {findings.length ? <div className="mt-5 grid gap-3">{findings.map((finding) => <FindingCard key={finding.id} finding={finding} />)}</div> : null}
    </section>
  );
}


function RealFindingsPipelinePanel({ pipeline }: { pipeline?: UnifiedUrlScanResponse["findings_pipeline"] }) {
  if (!pipeline) {
    return (
      <section className="rounded-[1.5rem] border border-amber-300/15 bg-amber-300/10 p-5 text-sm leading-7 text-amber-50">
        <p className="section-label">Phase 45 pipeline</p>
        <h2 className="mt-2 text-2xl font-black text-white">Real findings pipeline not attached</h2>
        <p className="mt-3">Re-run the unified scanner after applying Phase 45. Older local scan payloads will not contain pipeline validation.</p>
      </section>
    );
  }

  const realFindings = (pipeline.normalized_findings || []).map(findingFromRecord).filter((item): item is Finding => Boolean(item));
  const tools = (pipeline.tool_runs || []).filter(isRecord);
  const moduleStatus = (pipeline.module_status || []).filter(isRecord);
  const issues = pipeline.integrity?.issues || [];
  const blockers = pipeline.integrity?.blockers || [];

  return (
    <section className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="section-label">Phase 45 truth mapping</p>
          <h2 className="mt-2 text-2xl font-black text-white">Real findings pipeline</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">Checks tool output → parser → module cards → Results → Report/export mapping. Status messages stay separate from vulnerability findings.</p>
        </div>
        <span className={`badge ${pipeline.pipeline_ready ? "badge-green" : "badge-amber"}`}>{pipeline.status}</span>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Real findings</p><p className="mt-2 text-2xl font-black text-white">{pipeline.summary.real_findings}</p></div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Status msgs</p><p className="mt-2 text-2xl font-black text-white">{pipeline.summary.tool_status_messages}</p></div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">C/H findings</p><p className="mt-2 text-2xl font-black text-white">{pipeline.summary.critical_high_findings}</p></div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Export gate</p><p className="mt-2 text-sm font-black text-white">{pipeline.export_gate.export_ready ? "Ready" : "Blocked"}</p></div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Blockers</p><p className="mt-2 text-2xl font-black text-white">{pipeline.summary.blocker_count}</p></div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <article className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
          <h3 className="font-black text-white">Tool run integrity</h3>
          <div className="mt-3 grid gap-2">
            {tools.length ? tools.map((tool) => (
              <div key={asString(tool.tool)} className="flex flex-col gap-2 rounded-xl border border-white/[0.06] bg-white/[0.03] p-3 text-sm text-slate-300 sm:flex-row sm:items-center sm:justify-between">
                <span className="font-black capitalize text-white">{asString(tool.tool)}</span>
                <span className={`badge ${statusClass(asString(tool.state, "Not Assessed"))}`}>{asString(tool.state, "Not Assessed")} · {String(tool.real_findings ?? 0)} finding(s)</span>
              </div>
            )) : <p className="text-sm leading-6 text-slate-400">No tool run status exists in this scan payload.</p>}
          </div>
        </article>
        <article className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
          <h3 className="font-black text-white">Module mapping integrity</h3>
          <div className="mt-3 grid gap-2">
            {moduleStatus.slice(0, 8).map((module) => (
              <div key={asString(module.module)} className="flex flex-col gap-2 rounded-xl border border-white/[0.06] bg-white/[0.03] p-3 text-sm text-slate-300 sm:flex-row sm:items-center sm:justify-between">
                <span className="font-black text-white">{asString(module.label, asString(module.module))}</span>
                <span className={`badge ${statusClass(asString(module.state, "Not Assessed"))}`}>{asString(module.state, "Not Assessed")}</span>
              </div>
            ))}
          </div>
        </article>
      </div>

      {blockers.length || issues.length ? (
        <details className="mt-5 rounded-2xl border border-amber-300/15 bg-amber-300/10 p-4 text-sm leading-6 text-amber-50" open={blockers.length > 0}>
          <summary className="cursor-pointer font-black text-white">Pipeline issues / blockers</summary>
          <ul className="mt-3 space-y-2">
            {(blockers.length ? blockers : issues).slice(0, 8).map((issue) => <li key={issue}>• {issue}</li>)}
          </ul>
        </details>
      ) : (
        <p className="mt-5 rounded-2xl border border-emerald-300/15 bg-emerald-300/10 p-4 text-sm leading-7 text-emerald-50">Pipeline passed: no fake score/tool-output/export blocker detected in this payload.</p>
      )}

      <div className="mt-5 grid gap-3">
        {realFindings.slice(0, 6).map((finding) => <FindingCard key={`pipeline-${finding.id}`} finding={finding} />)}
        {!realFindings.length ? <p className="rounded-2xl border border-white/[0.07] bg-black/20 p-4 text-sm leading-7 text-slate-400">No normalized vulnerability findings. This can be valid when tools ran clean or evidence was not provided.</p> : null}
      </div>
    </section>
  );
}


function DynamicScoreTracePanel({ trace }: { trace: SurfaceRecord }) {
  const score = asNumber(trace.score);
  const totalPenalty = asNumber(trace.total_penalty);
  const breakdown = asArray(trace.breakdown).filter(isRecord);
  if (score === null && !breakdown.length) return null;

  return (
    <section className="mt-5 rounded-[1.5rem] border border-cyan-300/15 bg-cyan-300/[0.035] p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="section-label">Dynamic score proof</p>
          <h2 className="mt-2 text-2xl font-black text-white">Why this number changed or stayed same</h2>
          <p className="mt-2 max-w-4xl text-sm leading-7 text-slate-300">{asString(trace.formula, "Score is calculated from real findings and penalty math.")}</p>
          <p className="mt-2 text-xs leading-5 text-cyan-100/70">{asString(trace.important_note, "This is not a certified audit score.")}</p>
        </div>
        <div className="grid min-w-[220px] gap-2 text-right sm:grid-cols-2 lg:grid-cols-1">
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-3">
            <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Score</p>
            <p className="mt-1 text-2xl font-black text-white">{scoreText(score)}</p>
          </div>
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-3">
            <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Penalty</p>
            <p className="mt-1 text-2xl font-black text-white">{totalPenalty ?? 0}</p>
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-3">
        {breakdown.length ? breakdown.map((item, index) => (
          <article key={`${asString(item.id, "trace")}-${index}`} className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 className="font-black text-white">{asString(item.title, "Finding penalty")}</h3>
                <p className="mt-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{asString(item.category)} · {asString(item.rule_id, "no rule id")}</p>
              </div>
              <SeverityBadge severity={toSeverity(item.severity)} />
            </div>
            <div className="mt-3 grid gap-2 text-sm sm:grid-cols-4">
              <div className="rounded-xl bg-white/[0.04] p-3"><span className="text-slate-500">Base</span><br /><b className="text-white">{asNumber(item.base_penalty) ?? 0}</b></div>
              <div className="rounded-xl bg-white/[0.04] p-3"><span className="text-slate-500">Confidence</span><br /><b className="text-white">×{asNumber(item.confidence_multiplier) ?? 0}</b></div>
              <div className="rounded-xl bg-white/[0.04] p-3"><span className="text-slate-500">Applied</span><br /><b className="text-white">-{asNumber(item.applied_penalty) ?? 0}</b></div>
              <div className="rounded-xl bg-white/[0.04] p-3"><span className="text-slate-500">Score after</span><br /><b className="text-white">{scoreText(asNumber(item.score_after_finding))}</b></div>
            </div>
          </article>
        )) : (
          <p className="rounded-2xl border border-white/[0.07] bg-black/20 p-4 text-sm leading-7 text-slate-400">No finding penalties were applied. If the site is clean from passive evidence, website readiness can be 100/100 while full launch confidence remains gated until other modules are assessed.</p>
        )}
      </div>
    </section>
  );
}

export function ResultsClient() {
  const [result, setResult] = useState<UnifiedUrlScanResponse | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setResult(loadLatestUnifiedScan());
    setLoaded(true);
  }, []);

  const cards = useMemo(() => sortCards(result?.module_cards ?? []), [result]);
  const surface = asRecord(result?.surface_hints);
  const assessedCount = cards.filter((card) => card.assessed).length;
  const missingCount = cards.length - assessedCount;
  const priorityActions = result?.priority_actions ?? [];
  const coverageGate = result?.coverage_gate;
  const realEvidenceSummary = result?.real_evidence_summary;
  const dynamicScoreTrace = asRecord(realEvidenceSummary?.dynamic_score_trace ?? result?.dynamic_score_trace);

  if (!loaded) {
    return <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8"><div className="card p-6 text-slate-300">Loading latest real scan output...</div></main>;
  }

  if (!result) {
    return (
      <main className="results-final-page mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="results-clean-actions">
          <Link href="/scanner/unified-url" className="btn-primary">Run readiness scan →</Link>
          <Link href="/dashboard/scans" className="btn-secondary">Open saved scans</Link>
          <Link href="/report" className="btn-secondary">Open report center</Link>
        </div>
        <section className="mt-6 rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-6 shadow-2xl shadow-black/20">
          <p className="section-label">No active real result</p>
          <h1 className="mt-2 text-3xl font-black text-white">Run or open a scan to see evidence.</h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">This page intentionally does not show sample findings. Results appear only from a real backend scan, local latest scan storage, or saved scan workflow.</p>
        </section>
        <section className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-5" aria-label="Result states">
          {stateCopy.map(([title, text]) => (
            <article key={title} className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/20">
              <h2 className="text-xl font-black text-white">{title}</h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">{text}</p>
            </article>
          ))}
        </section>
      </main>
    );
  }

  return (
    <main className="results-final-page mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="results-clean-actions">
        <Link href="/scanner/unified-url" className="btn-primary">Run another scan →</Link>
        <Link href="/report" className="btn-secondary">Open report center</Link>
        <Link href="/dashboard/scans" className="btn-secondary">Saved scans</Link>
      </div>

      <section className="mt-6 rounded-[1.5rem] border border-cyan-300/15 bg-cyan-300/[0.04] p-6 shadow-2xl shadow-black/20">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="section-label">Latest real scan result</p>
            <h1 className="mt-2 text-3xl font-black text-white">{result.project_name || result.website_url}</h1>
            <p className="mt-2 break-words text-sm leading-7 text-slate-300">{result.website_url}</p>
            <p className="mt-2 text-sm leading-7 text-slate-400">Generated: {formatDate(result.generated_at)} · Report ID: {result.report_id}</p>
          </div>
          <span className={`badge ${statusClass(result.risk_label || "")}`}>{result.risk_label || "Partial readiness"}</span>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Available score</p><p className="mt-2 text-2xl font-black text-white">{scoreText(result.available_score)}</p></div>
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Overall gate</p><p className="mt-2 text-2xl font-black text-white">{coverageGate?.overall_confidence_allowed ? scoreText(result.overall_score) : "Gated"}</p></div>
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Assessed</p><p className="mt-2 text-2xl font-black text-white">{assessedCount}/{cards.length}</p></div>
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Missing/manual</p><p className="mt-2 text-2xl font-black text-white">{missingCount}</p></div>
        </div>
        <p className="mt-5 rounded-2xl border border-amber-300/15 bg-amber-300/10 p-4 text-sm leading-7 text-amber-50">{result.safe_public_summary}</p>
      </section>

      {coverageGate ? (
        <section className="mt-5 rounded-[1.5rem] border border-amber-300/15 bg-amber-300/10 p-5">
          <p className="section-label">Truth gate</p>
          <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h2 className="text-2xl font-black text-white">{coverageGate.overall_confidence_allowed ? "Overall confidence allowed" : "Overall confidence blocked"}</h2>
              <p className="mt-2 max-w-4xl text-sm leading-7 text-amber-50/90">{coverageGate.reason}</p>
              <p className="mt-2 text-xs leading-5 text-amber-100/70">{coverageGate.display_rule}</p>
            </div>
            <span className="badge badge-amber">Coverage {coverageGate.assessed_count}/{coverageGate.total_modules}</span>
          </div>
        </section>
      ) : null}

      {realEvidenceSummary ? (
        <section className="mt-5 rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
          <p className="section-label">Real evidence</p>
          <h2 className="mt-2 text-2xl font-black text-white">Observed issues vs hardening hints</h2>
          <p className="mt-2 text-sm leading-7 text-slate-400">{realEvidenceSummary.summary_rule}</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Observed</p><p className="mt-2 text-2xl font-black text-white">{realEvidenceSummary.real_observed_issue_count}</p></div>
            <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Hints</p><p className="mt-2 text-2xl font-black text-white">{realEvidenceSummary.potential_hardening_hint_count}</p></div>
            <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4"><p className="text-xs uppercase tracking-[0.16em] text-slate-500">Exploits proved</p><p className="mt-2 text-2xl font-black text-white">{realEvidenceSummary.confirmed_exploit_count}</p></div>
          </div>
          <details className="mt-5 rounded-2xl border border-white/[0.07] bg-black/20 p-4 text-xs text-slate-400">
            <summary className="cursor-pointer font-black text-white">Show raw passive website evidence</summary>
            <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words">{formatJson(realEvidenceSummary.website_raw_evidence)}</pre>
          </details>
        </section>
      ) : null}

      <DynamicScoreTracePanel trace={dynamicScoreTrace} />

      <section className="mt-5 grid gap-4 lg:grid-cols-2" aria-label="Module evidence">
        {cards.map((card) => <ModuleEvidenceCard key={card.module} card={card} />)}
      </section>

      <section className="mt-5 rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
        <p className="section-label">Priority actions</p>
        <h2 className="mt-2 text-2xl font-black text-white">Fix path from real findings</h2>
        {priorityActions.length ? (
          <div className="mt-5 grid gap-3">
            {priorityActions.map((action) => (
              <article key={`${action.step}-${action.title}`} className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="font-black text-white">{action.step}. {action.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-slate-300">{action.recommended_action}</p>
                    {action.business_impact ? <p className="mt-2 text-xs leading-5 text-slate-500">{action.business_impact}</p> : null}
                  </div>
                  <SeverityBadge severity={action.severity} />
                </div>
              </article>
            ))}
          </div>
        ) : <p className="mt-4 text-sm leading-7 text-slate-400">No priority actions were generated from the assessed evidence.</p>}
      </section>

      <div className="mt-5 grid gap-5">
        <RealFindingsPipelinePanel pipeline={result.findings_pipeline} />
        <StaticAnalysisPanel surface={surface} />
        <GithubDependencyPanel surface={surface} />
        <ApiExposurePanel surface={surface} />
      </div>

      {result.blocked_claims.length ? (
        <section className="mt-5 rounded-[1.5rem] border border-red-400/15 bg-red-500/10 p-5 text-sm leading-7 text-red-100">
          <h2 className="text-xl font-black text-white">Blocked claims</h2>
          <ul className="mt-3 space-y-2">
            {result.blocked_claims.map((claim) => <li key={claim}>• {claim}</li>)}
          </ul>
        </section>
      ) : null}
    </main>
  );
}
