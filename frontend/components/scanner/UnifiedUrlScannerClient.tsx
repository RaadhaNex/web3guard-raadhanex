
"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { API_BASE, apiGet, apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
import { clearLatestUnifiedScan, saveLatestUnifiedScan } from "@/lib/latestUnifiedScan";
import type {
  ProjectRecord,
  ScanHistoryRecord,
  Severity,
  UnifiedModuleCard,
  UnifiedScoreSplit,
  UnifiedScoreSplitItem,
  UnifiedUrlScanResponse,
} from "@/lib/types";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

const scanStages = [
  "Session check",
  "URL validation",
  "Auto public website scan",
  "Deep evidence orchestration",
  "Readiness scoring",
  "Report package",
];

const moduleOrder = ["website", "dapp", "api", "github", "contract", "static_analysis", "wallet", "admin_opsec"];

const projectTypeOptions = [
  "Website / dApp Frontend",
  "Smart Contract",
  "DeFi Protocol",
  "NFT / Marketplace",
  "DAO / Governance",
  "Wallet / Account Abstraction",
  "Token Launch",
  "GameFi",
  "Bridge / Cross-chain",
  "AI x Web3",
  "API / SaaS Backend",
  "Full Web3 Startup",
  "Other",
];

const chainOptions = [
  "Web only",
  "Ethereum",
  "Polygon",
  "BSC",
  "Arbitrum",
  "Optimism",
  "Base",
  "Avalanche",
  "Solana",
  "Multi-chain",
  "Other",
];

const scanModeOptions: Array<{ id: ScanMode; title: string; subtitle: string; bullets: string[] }> = [
  {
    id: "quick",
    title: "Quick Scan",
    subtitle: "URL-only scan for normal founders/users.",
    bullets: ["Website headers/CSP/cookies", "Public exposure paths", "JS/API discovery", "No technical evidence required"],
  },
  {
    id: "deep",
    title: "Deep Scan",
    subtitle: "Add repo/API/contract evidence for stronger results.",
    bullets: ["GitHub + OSV", "API base/OpenAPI", "Solidity/contract", "Backend tools if enabled"],
  },
  {
    id: "expert",
    title: "Expert Evidence",
    subtitle: "Paste tool artifacts and reviewer evidence.",
    bullets: ["Slither/Semgrep JSON", "HAR/auth/API artifacts", "Wallet/DeFi evidence", "Manual review context"],
  },
];

type ProjectMode = "new" | "existing";
type ScanMode = "quick" | "deep" | "expert";
type ExportFormat = "pdf" | "html" | "markdown" | "json";

type FixGuide = {
  where_to_fix: string;
  why_it_matters: string;
  how_to_fix: string;
  verify: string;
};

function normaliseUrl(value: string) {
  const clean = value.trim();
  if (!clean) return "";
  if (clean.startsWith("http://") || clean.startsWith("https://")) return clean;
  return `https://${clean}`;
}

function safeJsonStringify(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function plainRecord(value: unknown): Record<string, unknown> {
  return isPlainRecord(value) ? value : {};
}

function unknownArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function unknownNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function unknownString(value: unknown, fallback = "—") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function makeJsonSafe<T>(value: T): T {
  const seen = new WeakSet<object>();
  return JSON.parse(
    JSON.stringify(value, (_key, current) => {
      if (typeof current === "object" && current !== null) {
        if (seen.has(current)) return "[Circular]";
        seen.add(current);
      }
      return current;
    })
  ) as T;
}

function readableClientError(error: unknown) {
  if (!error) return "Unknown error. Please check the backend logs.";
  if (error instanceof Error) return error.message === "[object Object]" ? "Backend returned a structured error. Check the required fields and server logs." : error.message;
  if (typeof error === "string") return error === "[object Object]" ? "Backend returned a structured error." : error;
  if (typeof error === "object") {
    const record = error as Record<string, unknown>;
    if (typeof record.message === "string") return record.message;
    if (typeof record.error === "string") return record.error;
    if (typeof record.detail === "string") return record.detail;
    if (record.detail) return readableClientError(record.detail);
    return safeJsonStringify(error);
  }
  return String(error);
}

function formatDateTime(value?: string | null) {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function scoreTone(score?: number | null) {
  if (typeof score !== "number") return "text-slate-400";
  if (score >= 85) return "text-emerald-300";
  if (score >= 65) return "text-amber-300";
  return "text-red-300";
}

function riskBadgeClass(label?: string | null) {
  const value = String(label || "").toLowerCase();
  if (value.includes("critical") || value.includes("high")) return "badge-red";
  if (value.includes("medium") || value.includes("evidence") || value.includes("manual")) return "badge-amber";
  if (value.includes("low") || value.includes("pass") || value.includes("safe")) return "badge-green";
  return "badge-cyan";
}

function statusBadgeClass(status?: string | null) {
  const value = String(status || "").toLowerCase();
  if (value.includes("live") || value.includes("assessed") || value.includes("complete")) return "badge-green";
  if (value.includes("manual") || value.includes("input") || value.includes("needed")) return "badge-amber";
  if (value.includes("not assessed") || value.includes("not installed") || value.includes("key")) return "badge";
  return "badge-cyan";
}

function sortModuleCards(cards: UnifiedModuleCard[]) {
  return [...cards].sort((a, b) => {
    const aIndex = moduleOrder.indexOf(a.module);
    const bIndex = moduleOrder.indexOf(b.module);
    return (aIndex === -1 ? 999 : aIndex) - (bIndex === -1 ? 999 : bIndex);
  });
}

function getHistoryPayload(scan: ScanHistoryRecord) {
  return (scan.payload || {}) as Partial<UnifiedUrlScanResponse> & Record<string, unknown>;
}

function getHistoryWebsite(scan: ScanHistoryRecord) {
  const payload = getHistoryPayload(scan);
  return typeof payload.website_url === "string" && payload.website_url ? payload.website_url : "URL not stored";
}

function looksLikeUnifiedResult(payload: Record<string, unknown>): payload is UnifiedUrlScanResponse {
  return Boolean(
    typeof payload.website_url === "string" &&
      typeof payload.report_id === "string" &&
      Array.isArray(payload.module_cards)
  );
}

function moduleFixGuide(card: UnifiedModuleCard) {
  const module = card.module.toLowerCase();
  if (module === "wallet") return "Add wallet-flow evidence: transaction preview, chain mismatch handling, clear approval copy, and no seed/private-key requests.";
  if (module === "admin_opsec") return "Add admin evidence: MFA, multisig, timelock, role separation, signer policy, and break-glass procedure.";
  if (module === "contract") return "Paste Solidity source or provide verified contract evidence. Without source, code review remains Not Assessed.";
  if (module === "dapp") return "Provide frontend source or GitHub repo plus wallet-flow proof for deeper dApp scoring.";
  if (module === "api") return "Provide API base URL or docs and verify auth, rate limits, CORS, webhook signature checks, and object authorization.";
  if (module === "github") return "Provide a public GitHub repo and review secrets, branch protection, CI permissions, and dependency hygiene.";
  return "Review the listed evidence gaps, add the missing proof, and run the scanner again.";
}

function fixGuideForFinding(title: string, module?: string): FixGuide {
  const text = `${title} ${module || ""}`.toLowerCase();
  if (text.includes("content-security-policy") || text.includes("csp")) {
    return {
      where_to_fix: "frontend/next.config.mjs or hosting security headers",
      why_it_matters: "A strong CSP reduces the blast radius of script injection and compromised third-party assets.",
      how_to_fix: "Add a Content-Security-Policy header that allows only trusted script, frame, image, connect, and style sources.",
      verify: "Run curl -I against production and confirm Content-Security-Policy is present.",
    };
  }
  if (text.includes("rate limit")) {
    return {
      where_to_fix: "backend middleware and public scan/API routes",
      why_it_matters: "Rate limits protect your public infrastructure, scanner quotas, and authenticated dashboards from abuse.",
      how_to_fix: "Apply per-IP and per-user limits to scanner, auth-adjacent, report, and API endpoints.",
      verify: "Send repeated requests and confirm excessive calls return HTTP 429.",
    };
  }
  if (text.includes("webhook")) {
    return {
      where_to_fix: "backend payment or integration webhook route",
      why_it_matters: "Webhook events must be signature-verified before changing trust, billing, or launch status.",
      how_to_fix: "Verify provider signature using the raw request body and configured webhook secret before storing state.",
      verify: "Replay a request with an invalid signature and confirm it is rejected.",
    };
  }
  if (text.includes("bola") || text.includes("idor")) {
    return {
      where_to_fix: "project, scan, report, and dashboard detail endpoints",
      why_it_matters: "Object-level authorization bugs can expose one customer’s reports or project details to another account.",
      how_to_fix: "Verify every object belongs to the authenticated user or organization before returning data.",
      verify: "Use two accounts and confirm cross-account object IDs return 403 or 404.",
    };
  }
  if (text.includes("docs exposure") || text.includes("api docs")) {
    return {
      where_to_fix: "backend/main.py and deployment configuration",
      why_it_matters: "Public docs can reveal production routes, payload shapes, and admin-only surfaces.",
      how_to_fix: "Disable public docs in production or protect them with admin authentication.",
      verify: "Open /docs, /redoc, and /openapi.json on production and confirm the intended protection.",
    };
  }
  return {
    where_to_fix: "Manual review required",
    why_it_matters: "This item depends on project-specific architecture and launch context.",
    how_to_fix: "Document the affected flow, add the missing control or evidence, then re-run the scanner.",
    verify: "Re-test the exact flow and confirm the finding is resolved or explicitly accepted as risk.",
  };
}

function buildScoreSplit(result: UnifiedUrlScanResponse): UnifiedScoreSplit {
  if (result.score_split) return result.score_split;
  const byModule = new Map(result.module_cards.map((card) => [card.module, card]));
  const moduleEntry = (module: string, label: string, source: string): UnifiedScoreSplitItem => {
    const card = byModule.get(module);
    const assessed = Boolean(card?.assessed);
    return {
      label,
      score: assessed ? card?.score ?? null : null,
      status: card?.status || "Not Assessed",
      risk_label: card?.risk_label || "Not Assessed",
      source: assessed ? source : "Not Assessed — required evidence was not provided.",
    };
  };
  const total = result.module_cards.length || 1;
  const assessed = result.module_cards.filter((card) => card.assessed).length;
  const missing = result.module_cards.reduce((sum, card) => sum + (card.required_input?.length || 0), 0);
  const evidenceScore = Math.max(0, Math.min(100, Math.round((assessed / total) * 100 - Math.min(missing * 2, 24))));
  return {
    website_surface_score: moduleEntry("website", "Website Surface Score", "Passive public URL evidence such as HTTPS, headers, HTML hints, and policy signals."),
    contract_rule_score: moduleEntry("contract", "Contract Rule Score", "Solidity source or verified address evidence analyzed by local rules."),
    launch_evidence_score: {
      label: "Launch Evidence Score",
      score: evidenceScore,
      status: missing ? "Evidence needed" : "Evidence complete",
      risk_label: missing ? "Evidence gap" : "Evidence present",
      source: `${assessed}/${total} modules assessed; ${missing} required evidence item(s) still listed.`,
    },
    overall_launch_confidence: {
      label: "Overall Launch Confidence",
      score: (result.coverage_gate ? result.coverage_gate.overall_confidence_allowed : result.overall_score != null) ? result.overall_score ?? null : null,
      status: (result.coverage_gate ? result.coverage_gate.overall_confidence_allowed : result.overall_score != null) ? "Full assessed confidence" : "Insufficient evidence — overall confidence gated",
      risk_label: (result.coverage_gate ? result.coverage_gate.overall_confidence_allowed : result.overall_score != null) ? result.risk_label || "Not Assessed" : "Insufficient Evidence",
      source: "Overall confidence is shown only when every required module has real assessed evidence. Partial scans show website readiness and evidence coverage only.",
    },
    no_full_audit_score: !(result.coverage_gate ? result.coverage_gate.overall_confidence_allowed : result.overall_score != null),
    note: "Launch-readiness scores are not a certified audit score, penetration-test score, or security guarantee.",
  };
}

function scoreSplitCards(scoreSplit: UnifiedScoreSplit) {
  return ["website_surface_score", "contract_rule_score", "launch_evidence_score", "overall_launch_confidence"]
    .map((key) => ({ key, ...((scoreSplit[key] as UnifiedScoreSplitItem | undefined) || {}) }))
    .filter((item) => item.label);
}

function buildInlineMarkdownReport(report: Record<string, unknown>) {
  const findings = Array.isArray(report.top_findings) ? (report.top_findings as Array<Record<string, unknown>>) : [];
  const evidenceRequired = Array.isArray(report.evidence_required) ? (report.evidence_required as Array<Record<string, unknown>>) : [];
  const matrix = Array.isArray(report.module_matrix) ? (report.module_matrix as Array<Record<string, unknown>>) : [];
  const split = scoreSplitCards((report.score_split || {}) as UnifiedScoreSplit);

  const lines = [
    `# ${String(report.project_name || "Web3Guard Launch Readiness Report")}`,
    "",
    `Report ID: ${String(report.report_id || "not-generated")}`,
    `Verification hash: ${String(report.report_hash || "not-available")}`,
    "",
    "## Important note",
    "This report is generated from supplied or passive evidence only. Missing modules remain Not Assessed. This is not a certified audit.",
    "",
    "## Executive summary",
    String(report.executive_summary || "Evidence-first launch readiness summary."),
    "",
    "## Split readiness scores",
  ];

  split.forEach((item) => {
    lines.push(`- **${String(item.label)}**: ${typeof item.score === "number" ? item.score : "Not Assessed"} — ${String(item.status || "Not Assessed")}`);
    lines.push(`  - Evidence basis: ${String(item.source || "Not provided")}`);
  });

  lines.push("", "## Findings and fix hints");
  if (findings.length) {
    findings.forEach((finding, index) => {
      const fix = (finding.fix_guidance || {}) as Record<string, unknown>;
      lines.push(
        `${index + 1}. **${String(finding.severity || "info").toUpperCase()} — ${String(finding.title || "Finding")}**`,
        `   - Module: ${String(finding.module || "unknown")}`,
        `   - Recommendation: ${String(finding.recommendation || "Review before launch.")}`,
        `   - Where to fix: ${String(fix.where_to_fix || "Manual review required")}`,
        `   - How to fix: ${String(fix.how_to_fix || "Apply project-specific fix.")}`,
        `   - Verify: ${String(fix.verify || "Re-run scan after the fix.")}`
      );
    });
  } else {
    lines.push("No findings were detected in the assessed modules of this scan payload.");
  }

  lines.push("", "## Evidence required / Not Assessed modules");
  if (evidenceRequired.length) {
    evidenceRequired.forEach((item) => {
      lines.push(`- **${String(item.module_label || item.module || "Module")}**: ${String(item.required_input || "Missing evidence")}`);
    });
  } else {
    lines.push("No missing evidence was listed.");
  }

  lines.push("", "## Module matrix");
  matrix.forEach((row) => {
    lines.push(`- ${String(row.label || row.module || "Module")}: ${row.score ?? "Not Assessed"} · ${String(row.status || "Not Assessed")}`);
  });

  lines.push("", "## Disclaimer", String(report.disclaimer || "Not a certified audit."));
  return lines.join("\n");
}

function buildInlineReportFromResult(result: UnifiedUrlScanResponse) {
  const combined = (result.combined_report || {}) as Record<string, unknown>;
  const realFindings = (result.priority_actions || []).map((item) => ({
    severity: item.severity,
    module: item.module,
    title: item.title,
    confidence: "medium",
    recommendation: item.recommended_action,
    business_impact: item.business_impact || "Fix before production launch if this affects users, funds, or admin control.",
    fix_guidance: fixGuideForFinding(item.title, item.module),
  }));

  const evidenceRequired = result.module_cards.flatMap((card) =>
    (card.required_input || []).map((input) => ({
      module: card.module,
      module_label: card.label,
      status: card.status,
      required_input: input,
      next_step: moduleFixGuide(card),
    }))
  );

  const scoreSplit = buildScoreSplit(result);
  const moduleMatrix = result.module_cards.map((card) => ({
    label: card.label,
    module: card.module,
    weight_percent: card.assessed ? "assessed-only" : "not-scored",
    score: card.score ?? null,
    risk_label: card.risk_label || card.status || "Not Assessed",
    assessed: Boolean(card.assessed || card.score !== null),
    status: card.status || "Not Assessed",
    evidence: (card.evidence || []).slice(0, 4).join(" | ") || "No evidence provided",
  }));

  const report: Record<string, unknown> = {
    ...combined,
    report_id: result.report_id || combined.report_id,
    report_hash: (combined as Record<string, unknown>).report_hash,
    generated_at: result.generated_at || combined.generated_at,
    project_name: result.project_name || combined.project_name || result.website_url,
    combined: {
      ...(((combined as Record<string, unknown>).combined || {}) as Record<string, unknown>),
      overall_score: result.overall_score ?? null,
      available_score: result.available_score ?? null,
      risk_label: result.risk_label || "Not Assessed",
    },
    coverage: result.coverage || combined.coverage,
    score_split: scoreSplit,
    module_matrix: moduleMatrix,
    priority_action_plan: result.priority_actions || [],
    top_findings: realFindings,
    evidence_required: evidenceRequired,
    evidence_summary: result.module_cards.map((card) => ({
      module: card.module,
      module_label: card.label,
      status: card.status,
      score: card.score ?? null,
      evidence: card.evidence || [],
      limitations: card.limitations || [],
    })),
    dynamic_score_trace: result.dynamic_score_trace || result.real_evidence_summary?.dynamic_score_trace || null,
    detection_expansion: (result as unknown as { detection_expansion?: unknown }).detection_expansion || null,
    executive_summary: result.safe_public_summary || combined.executive_summary || "Preliminary launch-surface report generated from scanner evidence.",
    risk_narrative: result.realness_rule || combined.risk_narrative || "Only assessed modules receive scores. Missing modules remain Not Assessed.",
    limitations: [
      result.disclaimer,
      "URL-only scans are partial by design.",
      "Missing modules remain Not Assessed.",
      "This is not a certified audit, penetration test, or guarantee of security.",
    ].filter(Boolean),
    before_launch_checklist: combined.before_launch_checklist || [],
    package_recommendation: combined.package_recommendation || {
      package: "Complete missing evidence before public launch decisions",
      reason: "Report confidence depends on assessed modules and supplied evidence.",
    },
    disclaimer: result.disclaimer || combined.disclaimer,
  };

  report.markdown_report = buildInlineMarkdownReport(report);
  report.json_export = {
    report_id: report.report_id,
    report_hash: report.report_hash,
    generated_at: report.generated_at,
    project_name: report.project_name,
    website_url: result.website_url,
    combined: report.combined,
    coverage: report.coverage,
    score_split: report.score_split,
    module_matrix: report.module_matrix,
    priority_action_plan: report.priority_action_plan,
    top_findings: report.top_findings,
    evidence_required: report.evidence_required,
    evidence_summary: report.evidence_summary,
    dynamic_score_trace: report.dynamic_score_trace,
    detection_expansion: report.detection_expansion,
    limitations: report.limitations,
    disclaimer: report.disclaimer,
  };
  return makeJsonSafe(report);
}

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
    body: JSON.stringify(makeJsonSafe(payload)),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Export failed with ${response.status}`);
  }
  return response.blob();
}

function DynamicScoreTraceCard({ trace }: { trace: Record<string, unknown> }) {
  const score = unknownNumber(trace.score);
  const penalty = unknownNumber(trace.total_penalty);
  const rows = unknownArray(trace.breakdown).filter(isPlainRecord);
  if (score === null && !rows.length) return null;

  return (
    <CardShell>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="section-label">Dynamic score proof</p>
          <h2 className="mt-2 text-2xl font-black text-white">Why score is {score ?? "—"}</h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">{unknownString(trace.formula, "Score changes only when real response/tool evidence changes.")}</p>
          <p className="mt-2 text-xs leading-5 text-slate-500">{unknownString(trace.important_note, "This is a readiness score, not a certified audit score.")}</p>
        </div>
        <div className="grid min-w-[260px] gap-3 sm:grid-cols-2">
          <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Website score</p>
            <p className={`mt-2 text-2xl font-black ${scoreTone(score)}`}>{score ?? "—"}/100</p>
          </div>
          <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Penalty</p>
            <p className="mt-2 text-2xl font-black text-white">-{penalty ?? 0}</p>
          </div>
        </div>
      </div>
      <div className="mt-5 grid gap-3">
        {rows.length ? rows.map((item, index) => (
          <div key={`${unknownString(item.id, "score-row")}-${index}`} className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="font-black text-white">{unknownString(item.title, "Finding penalty")}</p>
                <p className="mt-1 text-xs uppercase tracking-[0.14em] text-slate-500">{unknownString(item.category)} · {unknownString(item.rule_id, "no rule id")}</p>
              </div>
              <SeverityBadge severity={(unknownString(item.severity, "info") as Severity)} />
            </div>
            <div className="mt-3 grid gap-2 text-xs sm:grid-cols-4">
              <span className="rounded-xl bg-black/20 p-3 text-slate-300">Base <b className="text-white">{unknownNumber(item.base_penalty) ?? 0}</b></span>
              <span className="rounded-xl bg-black/20 p-3 text-slate-300">Confidence <b className="text-white">×{unknownNumber(item.confidence_multiplier) ?? 0}</b></span>
              <span className="rounded-xl bg-black/20 p-3 text-slate-300">Applied <b className="text-white">-{unknownNumber(item.applied_penalty) ?? 0}</b></span>
              <span className="rounded-xl bg-black/20 p-3 text-slate-300">After <b className="text-white">{unknownNumber(item.score_after_finding) ?? "—"}</b></span>
            </div>
          </div>
        )) : (
          <p className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4 text-sm leading-6 text-slate-400">No penalty rows were generated. That means the assessed website surface had no passive findings.</p>
        )}
      </div>
    </CardShell>
  );
}


function getStaticAnalysisSummary(result: UnifiedUrlScanResponse): Record<string, unknown> {
  const hints = plainRecord(result.surface_hints);
  return plainRecord(hints.static_analysis);
}

function toolStateClass(state: string, status: string) {
  const value = `${state} ${status}`.toLowerCase();
  if (value.includes("assessed") || value.includes("completed") || value.includes("ran")) return "border-emerald-400/25 bg-emerald-400/10 text-emerald-100";
  if (value.includes("error") || value.includes("failed") || value.includes("timeout")) return "border-red-400/25 bg-red-500/10 text-red-100";
  if (value.includes("manual") || value.includes("configured") || value.includes("not assessed")) return "border-amber-300/25 bg-amber-300/10 text-amber-100";
  return "border-white/10 bg-white/[0.04] text-slate-300";
}

function cleanToolName(value: unknown) {
  const text = unknownString(value, "tool").replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function StaticToolStatusPanel({ result }: { result: UnifiedUrlScanResponse }) {
  const summary = getStaticAnalysisSummary(result);
  const tools = unknownArray(summary.tools).filter(isPlainRecord);
  const verification = plainRecord(summary.tool_verification);
  const findings = unknownArray(summary.findings).filter(isPlainRecord);
  const messages = unknownArray(summary.status_messages).filter(isPlainRecord);
  if (!tools.length && !findings.length && !messages.length) return null;

  const ranCount = unknownNumber(verification.ran_count) ?? tools.filter((tool) => ["completed", "completed_with_errors", "artifact_parsed"].includes(unknownString(tool.status, ""))).length;
  const realFindings = unknownNumber(verification.real_findings_count) ?? tools.reduce((sum, tool) => sum + (unknownNumber(tool.real_findings) ?? 0), 0);
  const failedCount = unknownNumber(verification.failed_count) ?? tools.filter((tool) => Boolean(tool.timed_out) || unknownString(tool.status, "").includes("error")).length;

  return (
    <CardShell className="border-cyan-300/15 bg-cyan-300/[0.035]">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="section-label">Tool verification</p>
          <h2 className="mt-2 text-2xl font-black text-white">Slither · Semgrep · Aderyn status</h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
            Real tool results are counted only when the backend actually ran the binary or parsed user-supplied JSON artifacts. Not-run rows stay informational.
          </p>
          {verification.evidence_rule ? <p className="mt-2 text-xs leading-5 text-slate-500">{unknownString(verification.evidence_rule)}</p> : null}
        </div>
        <div className="grid min-w-[280px] gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Ran</p>
            <p className="mt-2 text-2xl font-black text-white">{ranCount}</p>
          </div>
          <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Findings</p>
            <p className="mt-2 text-2xl font-black text-white">{realFindings}</p>
          </div>
          <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Failed</p>
            <p className="mt-2 text-2xl font-black text-white">{failedCount}</p>
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {tools.map((tool, index) => {
          const state = unknownString(tool.state, "Not Assessed");
          const status = unknownString(tool.status, "not_run");
          const statusText = `${state} · ${status}`;
          const stderr = unknownString(tool.stderr_tail, "");
          const stdout = unknownString(tool.stdout_tail, "");
          return (
            <div key={`${unknownString(tool.tool, "tool")}-${index}`} className={`rounded-2xl border p-4 ${toolStateClass(state, status)}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-black text-white">{cleanToolName(tool.tool)}</p>
                  <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.12em] opacity-80">{statusText}</p>
                </div>
                <span className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[10px] font-black text-white">{unknownNumber(tool.real_findings) ?? 0}</span>
              </div>
              <div className="mt-3 grid gap-2 text-[11px]">
                <span>Installed: <b>{Boolean(tool.installed) ? "Yes" : "No"}</b></span>
                <span>Enabled: <b>{Boolean(tool.enabled_by_env) ? "Yes" : "No"}</b></span>
                <span>Will run: <b>{Boolean(tool.will_run) ? "Yes" : "No"}</b></span>
              </div>
              {stderr && stderr !== "—" ? <p className="mt-3 max-h-20 overflow-auto rounded-xl bg-black/25 p-2 text-[11px] leading-5 text-red-100/85">{stderr}</p> : null}
              {!stderr && stdout && stdout !== "—" ? <p className="mt-3 max-h-20 overflow-auto rounded-xl bg-black/25 p-2 text-[11px] leading-5 text-slate-300">{stdout}</p> : null}
            </div>
          );
        })}
      </div>

      {findings.length ? (
        <details className="mt-5 rounded-2xl border border-white/[0.08] bg-black/20 p-4">
          <summary className="cursor-pointer text-sm font-black text-white">Show parsed tool findings with file/line</summary>
          <div className="mt-4 grid gap-3">
            {findings.slice(0, 12).map((finding, index) => (
              <div key={`${unknownString(finding.rule_id, "tool-finding")}-${index}`} className="rounded-xl border border-white/[0.07] bg-white/[0.03] p-3">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="font-black text-white">{unknownString(finding.title, "Tool finding")}</p>
                    <p className="mt-1 mono text-[11px] text-slate-500">
                      {unknownString(finding.affected_file, "file not reported")}:{unknownString(finding.affected_line, "line not reported")}
                    </p>
                  </div>
                  <SeverityBadge severity={(unknownString(finding.severity, "info") as Severity)} />
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{unknownString(finding.description, "Tool did not provide description.")}</p>
              </div>
            ))}
          </div>
        </details>
      ) : null}
    </CardShell>
  );
}

function CardShell({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`card p-4 sm:p-5 ${className}`}>{children}</section>;
}

function FieldLabel({ label, required, children, helper }: { label: string; required?: boolean; children: React.ReactNode; helper?: string }) {
  return (
    <label className="block text-sm font-bold text-slate-200">
      {label} {required ? <span className="text-red-300">*</span> : null}
      <div className="mt-2">{children}</div>
      {helper ? <span className="mt-1 block text-xs font-medium text-slate-500">{helper}</span> : null}
    </label>
  );
}

function ScoreOrb({ score, label }: { score?: number | null; label: string }) {
  const numeric = typeof score === "number" ? Math.max(0, Math.min(100, score)) : null;
  const circumference = 251;
  const dash = numeric == null ? circumference : circumference - (numeric / 100) * circumference;
  return (
    <div className="relative grid place-items-center">
      <svg viewBox="0 0 96 96" className="h-32 w-32 -rotate-90">
        <circle cx="48" cy="48" r="40" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="8" />
        <circle
          cx="48"
          cy="48"
          r="40"
          fill="none"
          stroke="url(#scoreGradient)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dash}
          className="transition-all duration-700"
        />
        <defs>
          <linearGradient id="scoreGradient" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" />
            <stop offset="55%" stopColor="#facc15" />
            <stop offset="100%" stopColor="#22c55e" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute text-center">
        <p className={`text-4xl font-black ${scoreTone(numeric)}`}>{numeric == null ? "—" : numeric}</p>
        <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">{label}</p>
      </div>
    </div>
  );
}

function SplitScoreCard({ item }: { item: ReturnType<typeof scoreSplitCards>[number] }) {
  return (
    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-black text-white">{item.label}</p>
        <span className={`badge ${riskBadgeClass(item.risk_label || item.status)}`}>{typeof item.score === "number" ? item.score : "N/A"}</span>
      </div>
      <p className="mt-2 text-xs font-bold text-slate-400">{item.status || "Not Assessed"}</p>
      <p className="mt-3 text-xs leading-5 text-slate-500">{item.source || "Evidence basis not supplied."}</p>
    </div>
  );
}

function FindingCard({ action }: { action: UnifiedUrlScanResponse["priority_actions"][number] }) {
  const severity = (action.severity || "info") as Severity;
  const guide = fixGuideForFinding(action.title, action.module);
  return (
    <details className="group rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4 open:border-cyan/20 open:bg-cyan/[0.035]">
      <summary className="flex cursor-pointer list-none flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <SeverityBadge severity={severity} />
          <h3 className="mt-2 text-base font-black text-white">{action.title}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-400">{action.recommended_action}</p>
        </div>
        <span className="badge badge-cyan shrink-0">{action.module_label || action.module}</span>
      </summary>
      <div className="mt-4 grid gap-3 border-t border-white/[0.07] pt-4 md:grid-cols-2">
        {[
          ["Where to fix", guide.where_to_fix],
          ["Why it matters", guide.why_it_matters],
          ["Fix direction", guide.how_to_fix],
          ["Verify", guide.verify],
        ].map(([title, text]) => (
          <div key={title} className="rounded-xl border border-white/[0.06] bg-black/20 p-3">
            <p className="mono text-[10px] font-bold uppercase tracking-[0.16em] text-cyan">{title}</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">{text}</p>
          </div>
        ))}
      </div>
    </details>
  );
}

function ModuleCard({ card }: { card: UnifiedModuleCard }) {
  const assessed = Boolean(card.assessed || card.score !== null);
  return (
    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-base font-black text-white">{card.label}</p>
          <p className="mt-1 text-xs font-semibold text-slate-500">{card.module}</p>
        </div>
        <span className={`badge ${statusBadgeClass(card.status)}`}>{assessed ? card.score ?? "—" : "Not Assessed"}</span>
      </div>
      <p className={`mt-3 text-sm font-bold ${scoreTone(card.score)}`}>{card.risk_label || card.status || "Not Assessed"}</p>
      {card.evidence?.length ? (
        <ul className="mt-3 space-y-2 text-xs leading-5 text-slate-400">
          {card.evidence.slice(0, 3).map((item) => <li key={item}>• {item}</li>)}
        </ul>
      ) : (
        <p className="mt-3 text-xs leading-5 text-slate-500">No evidence was available for this module in the current scan.</p>
      )}
      {card.required_input?.length ? (
        <div className="mt-4 rounded-xl border border-amber-300/15 bg-amber-300/10 p-3 text-xs leading-5 text-amber-100">
          <p className="font-black">Evidence needed</p>
          <ul className="mt-1 space-y-1">
            {card.required_input.slice(0, 3).map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </div>
      ) : null}
      {card.limitations?.length ? (
        <p className="mt-3 text-[11px] leading-5 text-slate-500">Limit: {card.limitations[0]}</p>
      ) : null}
    </div>
  );
}

export function UnifiedUrlScannerClient() {
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [projectName, setProjectName] = useState("");
  const [projectMode, setProjectMode] = useState<ProjectMode>("new");
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [projectType, setProjectType] = useState("");
  const [customProjectType, setCustomProjectType] = useState("");
  const [chain, setChain] = useState("");
  const [customChain, setCustomChain] = useState("");
  const [contractAddress, setContractAddress] = useState("");
  const [apiBaseUrl, setApiBaseUrl] = useState("");
  const [githubRepoUrl, setGithubRepoUrl] = useState("");
  const [solidityCode, setSolidityCode] = useState("");
  const [slitherJson, setSlitherJson] = useState("");
  const [semgrepJson, setSemgrepJson] = useState("");
  const [aderynJson, setAderynJson] = useState("");
  const [openapiJson, setOpenapiJson] = useState("");
  const [apiObservationsJson, setApiObservationsJson] = useState("");
  const [walletEvidenceJson, setWalletEvidenceJson] = useState("");
  const [signatureSamplesJson, setSignatureSamplesJson] = useState("");
  const [transactionSamplesJson, setTransactionSamplesJson] = useState("");
  const [businessContextJson, setBusinessContextJson] = useState("");
  const [defiSimulationJson, setDefiSimulationJson] = useState("");
  const [protocolContextJson, setProtocolContextJson] = useState("");
  const [reviewContextJson, setReviewContextJson] = useState("");
  const [harJson, setHarJson] = useState("");
  const [crawlerArtifactJson, setCrawlerArtifactJson] = useState("");
  const [authTestContextJson, setAuthTestContextJson] = useState("");
  const [securityToolArtifactsJson, setSecurityToolArtifactsJson] = useState("");
  const [foundryTestOutput, setFoundryTestOutput] = useState("");
  const [echidnaOutputJson, setEchidnaOutputJson] = useState("");
  const [invariantArtifactJson, setInvariantArtifactJson] = useState("");
  const [accuracyFeedbackJson, setAccuracyFeedbackJson] = useState("");
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [scanMode, setScanMode] = useState<ScanMode>("quick");
  const [activeEvidenceEditor, setActiveEvidenceEditor] = useState<string | null>(null);

  const [authLoading, setAuthLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [scanHistory, setScanHistory] = useState<ScanHistoryRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [selectedHistoryId, setSelectedHistoryId] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyRailHidden, setHistoryRailHidden] = useState(false);
  const [historySearch, setHistorySearch] = useState("");
  const [historyFilter, setHistoryFilter] = useState<"all" | "risky" | "clean">("all");
  const [termsOpen, setTermsOpen] = useState(false);

  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stageIndex, setStageIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [fieldPrompt, setFieldPrompt] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [result, setResult] = useState<UnifiedUrlScanResponse | null>(null);
  const [exportStatus, setExportStatus] = useState<string | null>(null);

  const selectedProject = projects.find((project) => project.id === selectedProjectId) || null;
  const selectedHistory = scanHistory.find((scan) => scan.id === selectedHistoryId) || null;
  const currentStage = scanStages[Math.min(stageIndex, scanStages.length - 1)];
  const activeScanMode = scanModeOptions.find((option) => option.id === scanMode) ?? scanModeOptions[0];
  const termsAccepted = authorized && realOnly;
  const filteredHistory = useMemo(() => {
    const query = historySearch.trim().toLowerCase();
    return scanHistory.filter((scan) => {
      const payload = getHistoryPayload(scan);
      const haystack = [
        scan.project_name,
        scan.risk_label,
        getHistoryWebsite(scan),
        typeof payload.report_id === "string" ? payload.report_id : "",
        typeof payload.project_type === "string" ? payload.project_type : "",
        typeof payload.chain === "string" ? payload.chain : "",
      ].filter(Boolean).join(" ").toLowerCase();
      const matchesSearch = !query || haystack.includes(query);
      const score = typeof scan.score === "number" ? scan.score : null;
      const findingCount = scan.findings_count ?? 0;
      const riskText = String(scan.risk_label || "").toLowerCase();
      const matchesFilter =
        historyFilter === "all" ||
        (historyFilter === "risky" && (findingCount > 0 || (score !== null && score < 85) || riskText.includes("high") || riskText.includes("critical"))) ||
        (historyFilter === "clean" && findingCount === 0 && (score === null || score >= 85));
      return matchesSearch && matchesFilter;
    });
  }, [historyFilter, historySearch, scanHistory]);

  const deepEditorFields = [
    {
      id: "solidity-source",
      label: "Solidity source",
      value: solidityCode,
      setValue: setSolidityCode,
      placeholder: "Paste Solidity source here for local rule checks and optional backend Slither/Semgrep execution.",
      rows: 12,
    },
  ];

  const expertEditorFields = [
    {
      id: "slither-json",
      label: "Slither JSON",
      value: slitherJson,
      setValue: setSlitherJson,
      placeholder: '{ "results": { "detectors": [...] } }',
      rows: 8,
    },
    {
      id: "semgrep-json",
      label: "Semgrep JSON",
      value: semgrepJson,
      setValue: setSemgrepJson,
      placeholder: '{ "results": [...] }',
      rows: 8,
    },
    {
      id: "aderyn-json",
      label: "Aderyn JSON",
      value: aderynJson,
      setValue: setAderynJson,
      placeholder: '{ "issues": [...] }',
      rows: 8,
    },
    {
      id: "openapi-json",
      label: "OpenAPI JSON",
      value: openapiJson,
      setValue: setOpenapiJson,
      placeholder: '{ "openapi": "3.0.0", "paths": { ... } }',
      rows: 8,
    },
    {
      id: "authorized-api-observations",
      label: "Authorized API observations JSON array",
      value: apiObservationsJson,
      setValue: setApiObservationsJson,
      placeholder: '[{"endpoint":"/api/orders/123","role":"userA","status_code":200,"cross_account_access_proved":true,"response_hash":"sha256..."}]',
      rows: 8,
    },
    {
      id: "wallet-evidence-json",
      label: "Wallet evidence JSON",
      value: walletEvidenceJson,
      setValue: setWalletEvidenceJson,
      placeholder: '{ "expected_chain_id":"1", "copy":"No seed phrase requested" }',
      rows: 8,
    },
    {
      id: "transaction-samples-json",
      label: "Transaction samples JSON array",
      value: transactionSamplesJson,
      setValue: setTransactionSamplesJson,
      placeholder: '[{"chain_id":"1","approval":"unlimited"}]',
      rows: 8,
    },
    {
      id: "signature-samples-json",
      label: "Signature samples JSON array",
      value: signatureSamplesJson,
      setValue: setSignatureSamplesJson,
      placeholder: '[{"message":"Claim airdrop","human_readable_purpose":""}]',
      rows: 8,
    },
    {
      id: "business-context-json",
      label: "Business context JSON",
      value: businessContextJson,
      setValue: setBusinessContextJson,
      placeholder: '{ "roles":["owner","user"], "critical_actions":["report unlock"], "asset_flows":["payment to report"] }',
      rows: 8,
    },
    {
      id: "defi-simulation-json",
      label: "DeFi simulation artifact JSON",
      value: defiSimulationJson,
      setValue: setDefiSimulationJson,
      placeholder: '{ "invariants":[{"name":"assets conserved","passed":false,"evidence":"local test output"}] }',
      rows: 8,
    },
    {
      id: "protocol-context-json",
      label: "Protocol context JSON",
      value: protocolContextJson,
      setValue: setProtocolContextJson,
      placeholder: '{ "uses_oracle": true, "has_flash_loan_surface": true }',
      rows: 8,
    },
    {
      id: "reviewed-confirmation-json",
      label: "Reviewed confirmation JSON",
      value: reviewContextJson,
      setValue: setReviewContextJson,
      placeholder: '{ "reviewer":"name", "triaged_findings_count":8, "unresolved_critical_high_count":0, "payment_verified":true }',
      rows: 8,
    },
    {
      id: "har-json",
      label: "HAR / browser network capture JSON",
      value: harJson,
      setValue: setHarJson,
      placeholder: '{ "log": { "entries": [{ "request": {"url":"https://example.com/api/me","method":"GET"}, "response": {"status": 200} }] } }',
      rows: 8,
    },
    {
      id: "crawler-artifact-json",
      label: "Crawler artifact JSON",
      value: crawlerArtifactJson,
      setValue: setCrawlerArtifactJson,
      placeholder: '{ "entries": [{"url":"https://example.com/admin","status":200,"method":"GET"}] }',
      rows: 8,
    },
    {
      id: "authorized-api-test-context-json",
      label: "Authorized API test context JSON",
      value: authTestContextJson,
      setValue: setAuthTestContextJson,
      placeholder: '[{"endpoint":"/api/orders/123","expected_status":403,"actual_status":200,"cross_account_access_proved":true,"response_hash":"sha256..."}]',
      rows: 8,
    },
    {
      id: "sca-secrets-tool-artifact-json",
      label: "SCA / secrets tool artifact JSON",
      value: securityToolArtifactsJson,
      setValue: setSecurityToolArtifactsJson,
      placeholder: '{ "gitleaks": [{"RuleID":"generic-api-key","File":"src/config.ts"}], "npm_audit": {"vulnerabilities": []} }',
      rows: 8,
    },
    {
      id: "foundry-forge-test-output",
      label: "Foundry / forge test output",
      value: foundryTestOutput,
      setValue: setFoundryTestOutput,
      placeholder: 'Paste forge test output. Failure markers become evidence-backed local test findings.',
      rows: 8,
    },
    {
      id: "echidna-output-json",
      label: "Echidna output JSON",
      value: echidnaOutputJson,
      setValue: setEchidnaOutputJson,
      placeholder: '[{"name":"echidna_balance_never_drops","status":"falsified","counterexample":"..."}]',
      rows: 8,
    },
    {
      id: "invariant-simulation-artifact-json",
      label: "Invariant / simulation artifact JSON",
      value: invariantArtifactJson,
      setValue: setInvariantArtifactJson,
      placeholder: '{ "invariants": [{"name":"assets conserved","status":"failed","evidence":"local fork test"}] }',
      rows: 8,
    },
    {
      id: "accuracy-feedback-json",
      label: "Accuracy feedback / triage benchmark JSON",
      value: accuracyFeedbackJson,
      setValue: setAccuracyFeedbackJson,
      placeholder: '[{"finding_id":"abc","status":"confirmed"},{"finding_id":"def","status":"false_positive"}]',
      rows: 8,
    },
  ];

  const visibleEditorFields = scanMode === "expert" ? [...deepEditorFields, ...expertEditorFields] : deepEditorFields;
  const activeEvidenceField = visibleEditorFields.find((field) => field.id === activeEvidenceEditor) ?? null;

  const resolvedProjectType = useMemo(() => projectType === "Other" ? customProjectType.trim() || "Other" : projectType.trim() || "Website / dApp Frontend", [customProjectType, projectType]);
  const resolvedChain = useMemo(() => chain === "Other" ? customChain.trim() || "Other" : chain.trim() || "Web only", [chain, customChain]);

  const missingRequiredFields = useMemo(() => {
    const missing: string[] = [];
    if (!websiteUrl.trim()) missing.push("Website / dApp URL");
    if (scanMode !== "quick") {
      if (!projectType.trim()) missing.push("Project type");
      if (projectType === "Other" && !customProjectType.trim()) missing.push("Custom project type");
      if (!chain.trim()) missing.push("Chain / surface");
      if (chain === "Other" && !customChain.trim()) missing.push("Custom chain");
    }
    if (!authorized || !realOnly) missing.push("Terms and scan authorization");
    return missing;
  }, [authorized, chain, customChain, customProjectType, projectType, realOnly, scanMode, websiteUrl]);

  const canRunScan = !loading && !authLoading;
  const cards = result?.module_cards ? sortModuleCards(result.module_cards) : [];
  const scoreSplit = result ? buildScoreSplit(result) : null;
  const splitCards = scoreSplit ? scoreSplitCards(scoreSplit) : [];
  const requiredInputs = result?.module_cards.flatMap((card) => (card.required_input || []).map((item) => ({ label: card.label, item, guide: moduleFixGuide(card) }))) || [];
  const coverageGate = result?.coverage_gate;
  const realEvidenceSummary = result?.real_evidence_summary;
  const dynamicScoreTrace = plainRecord(realEvidenceSummary?.dynamic_score_trace ?? result?.dynamic_score_trace);
  const overallAllowed = coverageGate ? coverageGate.overall_confidence_allowed : Boolean(result?.overall_score);
  const heroScore = overallAllowed ? result?.overall_score ?? null : scoreSplit?.website_surface_score?.score ?? null;
  const heroLabel = overallAllowed ? "confidence" : "site score";

  function setKnownProjectType(value?: string | null) {
    if (!value) return;
    if (projectTypeOptions.includes(value)) {
      setProjectType(value);
      setCustomProjectType("");
    } else {
      setProjectType("Other");
      setCustomProjectType(value);
    }
  }

  function setKnownChain(value?: string | null) {
    if (!value) return;
    if (chainOptions.includes(value)) {
      setChain(value);
      setCustomChain("");
    } else {
      setChain("Other");
      setCustomChain(value);
    }
  }

  function setScanTermsAccepted(next: boolean) {
    setAuthorized(next);
    setRealOnly(next);
    if (next) setFieldPrompt(null);
  }

  async function loadWorkspaceQuickData() {
    if (!isLoggedIn) return;
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const userId = await getCurrentUserId();
      const token = await getSessionToken();
      const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
      const queryUser = encodeURIComponent(userId);
      const scanData = await apiGet<{ scans: ScanHistoryRecord[] }>(`/scan-history?user_id=${queryUser}&limit=30`, { headers });
      setScanHistory(
        (scanData.scans || []).filter((scan) => scan.module === "unified_url" || looksLikeUnifiedResult(getHistoryPayload(scan) as Record<string, unknown>))
      );
    } catch (err) {
      setHistoryError(readableClientError(err));
    } finally {
      setHistoryLoading(false);
    }
  }

  function applyProject(projectId: string) {
    setSelectedProjectId(projectId);
    setProjectMode(projectId ? "existing" : "new");
    const project = projects.find((item) => item.id === projectId);
    if (!project) return;
    setProjectName(project.name || "");
    setWebsiteUrl(project.website_url || "");
    setKnownChain(project.chain);
    setKnownProjectType(project.project_type);
    setContractAddress(project.contract_address || "");
    setGithubRepoUrl(project.github_repo_url || "");
    setSaveMessage("Existing project loaded. Run a fresh scan or load a saved result.");
  }

  function startNewProject() {
    setProjectMode("new");
    setSelectedProjectId("");
    setSelectedHistoryId("");
    setProjectName("");
    setWebsiteUrl("");
    setProjectType("");
    setCustomProjectType("");
    setChain("");
    setCustomChain("");
    setAuthorized(false);
    setRealOnly(false);
    setContractAddress("");
    setApiBaseUrl("");
    setGithubRepoUrl("");
    setSolidityCode("");
    setSlitherJson("");
    setSemgrepJson("");
    setAderynJson("");
    setOpenapiJson("");
    setApiObservationsJson("");
    setWalletEvidenceJson("");
    setSignatureSamplesJson("");
    setTransactionSamplesJson("");
    setBusinessContextJson("");
    setDefiSimulationJson("");
    setProtocolContextJson("");
    setReviewContextJson("");
    setHarJson("");
    setCrawlerArtifactJson("");
    setAuthTestContextJson("");
    setSecurityToolArtifactsJson("");
    setFoundryTestOutput("");
    setEchidnaOutputJson("");
    setInvariantArtifactJson("");
    setAccuracyFeedbackJson("");
    setAdvancedOpen(false);
    setScanMode("quick");
    setActiveEvidenceEditor(null);
    setHistorySearch("");
    setHistoryFilter("all");
    setTermsOpen(false);
    setProgress(0);
    setStageIndex(0);
    setResult(null);
    clearLatestUnifiedScan();
    setError(null);
    setFieldPrompt(null);
    setExportStatus(null);
    setSaveMessage(null);
  }

  function resetForm() {
    startNewProject();
  }

  function applyHistory(scanId: string) {
    setSelectedHistoryId(scanId);
    setError(null);
    setExportStatus(null);
    const scan = scanHistory.find((item) => item.id === scanId);
    if (!scan) return;
    const payload = getHistoryPayload(scan) as Record<string, unknown>;
    const historyWebsite = typeof payload.website_url === "string" ? payload.website_url : "";
    const historyProjectName = scan.project_name || (typeof payload.project_name === "string" ? payload.project_name : "");
    if (historyWebsite) setWebsiteUrl(historyWebsite);
    if (historyProjectName) setProjectName(historyProjectName);
    setKnownProjectType(typeof payload.project_type === "string" ? payload.project_type : null);
    setKnownChain(typeof payload.chain === "string" ? payload.chain : null);
    if (scan.project_id) {
      setSelectedProjectId(scan.project_id);
      setProjectMode("existing");
    }
    if (looksLikeUnifiedResult(payload)) {
      setResult(payload);
      saveLatestUnifiedScan(payload);
      setSaveMessage(`Loaded saved scan from ${formatDateTime(scan.created_at)}.`);
    } else {
      setSaveMessage(`Loaded saved inputs from ${formatDateTime(scan.created_at)}. Run a fresh scan for a new result.`);
    }
  }

  useEffect(() => {
    let mounted = true;
    async function checkAuth() {
      setAuthLoading(true);
      try {
        await getCurrentUserId();
        if (mounted) setIsLoggedIn(true);
      } catch {
        if (mounted) setIsLoggedIn(false);
      } finally {
        if (mounted) setAuthLoading(false);
      }
    }
    void checkAuth();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (!isLoggedIn) return;
    void loadWorkspaceQuickData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoggedIn]);

  useEffect(() => {
    if (!loading) return;
    setProgress(8);
    setStageIndex(0);
    const timer = window.setInterval(() => {
      setProgress((value) => (value >= 96 ? value : value + 7));
      setStageIndex((value) => (value >= scanStages.length - 2 ? value : value + 1));
    }, 800);
    return () => window.clearInterval(timer);
  }, [loading]);

  async function runScan() {
    setError(null);
    setFieldPrompt(null);
    setSaveMessage(null);
    setResult(null);
    setExportStatus(null);

    if (!isLoggedIn) {
      setError("Login is required before running a saved evidence-based scan.");
      return;
    }
    if (missingRequiredFields.length) {
      const message = `Please complete: ${missingRequiredFields.join(", ")}.`;
      setFieldPrompt(message);
      setError(message);
      return;
    }
    const cleanWebsiteUrl = normaliseUrl(websiteUrl);
    if (!cleanWebsiteUrl) {
      const message = "Enter a valid website or dApp URL.";
      setFieldPrompt(message);
      setError(message);
      return;
    }

    setWebsiteUrl(cleanWebsiteUrl);
    setLoading(true);
    try {
      const userId = await getCurrentUserId();
      const token = await getSessionToken();
      const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
      const data = await apiPost<UnifiedUrlScanResponse>(
        "/scan/unified-url",
        {
          user_id: userId,
          website_url: cleanWebsiteUrl,
          project_name: projectName.trim() || cleanWebsiteUrl,
          project_type: resolvedProjectType,
          chain: resolvedChain,
          contract_address: contractAddress.trim() || null,
          api_base_url: apiBaseUrl.trim() || null,
          github_repo_url: githubRepoUrl.trim() || null,
          solidity_code: solidityCode.trim() || null,
          slither_json: slitherJson.trim() || null,
          semgrep_json: semgrepJson.trim() || null,
          aderyn_json: aderynJson.trim() || null,
          openapi_json: openapiJson.trim() || null,
          api_observations_json: apiObservationsJson.trim() || null,
          wallet_evidence_json: walletEvidenceJson.trim() || null,
          signature_samples_json: signatureSamplesJson.trim() || null,
          transaction_samples_json: transactionSamplesJson.trim() || null,
          business_context_json: businessContextJson.trim() || null,
          defi_simulation_json: defiSimulationJson.trim() || null,
          protocol_context_json: protocolContextJson.trim() || null,
          review_context_json: reviewContextJson.trim() || null,
          har_json: harJson.trim() || null,
          crawler_artifact_json: crawlerArtifactJson.trim() || null,
          auth_test_context_json: authTestContextJson.trim() || null,
          security_tool_artifacts_json: securityToolArtifactsJson.trim() || null,
          foundry_test_output: foundryTestOutput.trim() || null,
          echidna_output_json: echidnaOutputJson.trim() || null,
          invariant_artifact_json: invariantArtifactJson.trim() || null,
          accuracy_feedback_json: accuracyFeedbackJson.trim() || null,
          scan_mode: scanMode,
          deep_scan_requested: scanMode === "deep" || scanMode === "expert",
          expert_evidence_requested: scanMode === "expert",
          authorization_confirmed: authorized,
          real_only_acknowledged: realOnly,
        },
        { headers }
      );
      setStageIndex(scanStages.length - 1);
      setProgress(100);
      setResult(data);
      saveLatestUnifiedScan(data);
    } catch (err) {
      setError(readableClientError(err));
      setProgress(0);
      setStageIndex(0);
    } finally {
      window.setTimeout(() => setLoading(false), 350);
    }
  }

  async function saveUnifiedScanToDashboard() {
    if (!result) return;
    setSaveLoading(true);
    setSaveMessage(null);
    setError(null);
    try {
      const userId = await getCurrentUserId();
      const token = await getSessionToken();
      const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
      let projectId = projectMode === "existing" ? selectedProjectId : "";
      if (!projectId) {
        const projectResponse = await apiPost<{ project: { id: string } }>(
          "/projects",
          {
            user_id: userId,
            name: projectName.trim() || result.project_name || "Unified Launch Scan",
            website_url: websiteUrl,
            chain: resolvedChain,
            contract_address: contractAddress || null,
            github_repo_url: githubRepoUrl || null,
            project_type: resolvedProjectType,
            description: "Created from the unified launch scanner. Only assessed evidence contributes to scoring.",
          },
          { headers }
        );
        projectId = projectResponse.project.id;
        setSelectedProjectId(projectId);
        setProjectMode("existing");
      }

      const criticalHigh = result.priority_actions?.filter((item) => item.severity === "critical" || item.severity === "high").length || 0;
      await apiPost(
        "/scan-history",
        {
          user_id: userId,
          project_id: projectId,
          module: "unified_url",
          project_name: projectName.trim() || result.project_name,
          score: result.available_score ?? null,
          risk_label: result.risk_label,
          report_id: result.report_id,
          findings_count: result.module_cards.reduce((sum, card) => sum + (card.findings_count || 0), 0),
          critical_high_count: criticalHigh,
          status: "saved_from_unified_url_scanner",
          payload: result,
        },
        { headers }
      );
      setSaveMessage(projectMode === "existing" ? "Scan saved under the selected project." : "Scan saved and a new project record was created.");
      await loadWorkspaceQuickData();
    } catch (err) {
      setError(readableClientError(err));
    } finally {
      setSaveLoading(false);
    }
  }

  async function exportCurrentReport(format: ExportFormat) {
    if (!result) return;
    setExportStatus(`Preparing ${format.toUpperCase()} export from this scan result...`);
    setError(null);
    try {
      const report = buildInlineReportFromResult(result);
      const baseName = String(report.report_id || "web3guard-launch-report");
      const accept = format === "pdf" ? "application/pdf" : format === "html" ? "text/html" : format === "markdown" ? "text/markdown" : "application/json";
      const blob = await postBlob(`/report/export/${format}`, { report }, accept);
      downloadBlob(blob, `${baseName}.${format === "markdown" ? "md" : format}`);
      setExportStatus(`${format.toUpperCase()} export downloaded. Not Assessed modules remain clearly separated.`);
    } catch (err) {
      setExportStatus(null);
      setError(readableClientError(err));
    }
  }

  return (
    <main className="relative overflow-hidden scanner-console-page scanner-focus-page scanner-premium-page">
      <section className="mx-auto max-w-[1280px] px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-[1180px] space-y-5">
          {!historyRailHidden ? (
            <aside className="fixed left-3 top-24 z-40 hidden w-14 flex-col items-center gap-2 rounded-2xl border border-white/[0.08] bg-[#050b18]/95 p-2 shadow-2xl shadow-black/40 backdrop-blur-xl md:flex">
              <button
                type="button"
                onClick={() => setHistoryOpen((value) => !value)}
                title="Open scan history"
                aria-label="Open scan history"
                className={`flex h-10 w-10 items-center justify-center rounded-xl border text-lg transition ${historyOpen ? "border-cyan-300/40 bg-cyan-300/[0.14] text-cyan-100" : "border-white/[0.08] bg-white/[0.04] text-slate-300 hover:border-cyan-300/30 hover:bg-cyan-300/[0.08] hover:text-cyan-100"}`}
              >
                ☰
              </button>
              <button
                type="button"
                onClick={() => resetForm()}
                title="New scan"
                aria-label="New scan"
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.04] text-lg text-slate-300 transition hover:border-cyan-300/30 hover:bg-cyan-300/[0.08] hover:text-cyan-100"
              >
                ＋
              </button>
              <button
                type="button"
                onClick={() => void loadWorkspaceQuickData()}
                title="Refresh history"
                aria-label="Refresh history"
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.04] text-lg text-slate-300 transition hover:border-cyan-300/30 hover:bg-cyan-300/[0.08] hover:text-cyan-100"
              >
                ↻
              </button>
              <Link
                href="/dashboard/scans"
                title="Saved scans dashboard"
                aria-label="Saved scans dashboard"
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.04] text-lg text-slate-300 transition hover:border-cyan-300/30 hover:bg-cyan-300/[0.08] hover:text-cyan-100"
              >
                ◫
              </Link>
              <div className="my-1 h-px w-8 bg-white/[0.08]" />
              <button
                type="button"
                onClick={() => { setHistoryRailHidden(true); setHistoryOpen(false); }}
                title="Hide sidebar"
                aria-label="Hide sidebar"
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.04] text-lg text-slate-400 transition hover:border-white/20 hover:text-white"
              >
                ‹
              </button>
            </aside>
          ) : (
            <button
              type="button"
              onClick={() => setHistoryRailHidden(false)}
              title="Show sidebar"
              aria-label="Show sidebar"
              className="fixed left-0 top-24 z-40 hidden rounded-r-2xl border border-l-0 border-cyan-300/20 bg-[#050b18]/95 px-2.5 py-4 text-lg font-black text-cyan-100 shadow-2xl shadow-black/40 backdrop-blur-xl transition hover:bg-cyan-300/[0.10] md:block"
            >
              ☰
            </button>
          )}

          <button
            type="button"
            onClick={() => setHistoryOpen(true)}
            className="fixed bottom-5 left-5 z-40 rounded-full border border-cyan-300/25 bg-[#050b18]/95 px-4 py-2 text-xs font-black text-cyan-100 shadow-2xl shadow-black/50 backdrop-blur-xl transition hover:border-cyan-300/45 hover:bg-cyan-300/[0.12] md:hidden"
          >
            History {scanHistory.length ? `(${scanHistory.length})` : ""}
          </button>

          {historyOpen ? (
            <div className="fixed inset-0 z-50 bg-black/45 backdrop-blur-sm" onClick={() => setHistoryOpen(false)}>
              <aside
                className="h-full w-full max-w-[360px] overflow-y-auto border-r border-cyan-300/15 bg-[#050b18] p-4 shadow-2xl shadow-black/60"
                onClick={(event) => event.stopPropagation()}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyan-300/25 bg-cyan-300/[0.10] text-sm font-black text-cyan-100">W3</span>
                    <div>
                      <p className="text-sm font-black text-white">Scan history</p>
                      <p className="text-[11px] text-slate-500">Load, search, refresh, or start fresh.</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setHistoryOpen(false)}
                    className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 text-lg text-slate-300 transition hover:border-white/20 hover:text-white"
                    aria-label="Close history"
                  >
                    ×
                  </button>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => { resetForm(); setHistoryOpen(false); }}
                    className="rounded-xl border border-cyan-300/25 bg-cyan-300/[0.10] px-3 py-2.5 text-left text-xs font-black text-cyan-100 transition hover:border-cyan-300/45 hover:bg-cyan-300/[0.16]"
                  >
                    ＋ New scan
                  </button>
                  <button
                    type="button"
                    onClick={() => void loadWorkspaceQuickData()}
                    disabled={historyLoading}
                    className="rounded-xl border border-white/[0.08] bg-white/[0.04] px-3 py-2.5 text-left text-xs font-black text-slate-200 transition hover:border-cyan-300/30 hover:text-cyan-100 disabled:opacity-50"
                  >
                    {historyLoading ? "↻ Refreshing" : "↻ Refresh"}
                  </button>
                  <Link href="/results" className="rounded-xl border border-white/[0.08] bg-white/[0.04] px-3 py-2.5 text-xs font-black text-slate-200 transition hover:border-cyan-300/30 hover:text-cyan-100">
                    Results
                  </Link>
                  <Link href="/report" className="rounded-xl border border-white/[0.08] bg-white/[0.04] px-3 py-2.5 text-xs font-black text-slate-200 transition hover:border-cyan-300/30 hover:text-cyan-100">
                    Report
                  </Link>
                  <Link href="/dashboard/scans" className="rounded-xl border border-white/[0.08] bg-white/[0.04] px-3 py-2.5 text-xs font-black text-slate-200 transition hover:border-cyan-300/30 hover:text-cyan-100">
                    Dashboard scans
                  </Link>
                  <button
                    type="button"
                    onClick={() => { clearLatestUnifiedScan(); setResult(null); setSaveMessage("Current local result cleared. Saved dashboard history is unchanged."); }}
                    className="rounded-xl border border-white/[0.08] bg-white/[0.04] px-3 py-2.5 text-left text-xs font-black text-slate-200 transition hover:border-red-300/30 hover:text-red-100"
                  >
                    Clear current
                  </button>
                </div>

                <div className="mt-4 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-3">
                  <label className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-500">Search scans</label>
                  <input
                    className="input mt-2"
                    value={historySearch}
                    onChange={(event) => setHistorySearch(event.target.value)}
                    placeholder="Search project, URL, risk, report id..."
                  />
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    {(["all", "risky", "clean"] as const).map((filter) => (
                      <button
                        key={filter}
                        type="button"
                        onClick={() => setHistoryFilter(filter)}
                        className={`rounded-lg border px-2 py-1.5 text-[10px] font-black uppercase tracking-[0.08em] transition ${historyFilter === filter ? "border-cyan-300/35 bg-cyan-300/[0.12] text-cyan-100" : "border-white/[0.08] bg-white/[0.03] text-slate-500 hover:border-white/20 hover:text-slate-200"}`}
                      >
                        {filter}
                      </button>
                    ))}
                  </div>
                </div>

                {historyError ? <p className="mt-4 rounded-xl border border-red-400/25 bg-red-500/10 p-3 text-sm text-red-100">{historyError}</p> : null}

                <div className="mt-5 flex items-center justify-between gap-3">
                  <p className="text-[11px] font-black uppercase tracking-[0.14em] text-slate-500">Recent scans</p>
                  <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-1 text-[10px] font-black text-slate-400">{filteredHistory.length}/{scanHistory.length}</span>
                </div>

                <div className="mt-3 space-y-2">
                  {filteredHistory.length ? filteredHistory.map((scan) => (
                    <div
                      key={scan.id}
                      className={`rounded-2xl border p-3 transition ${selectedHistoryId === scan.id ? "border-cyan-300/40 bg-cyan-300/[0.10]" : "border-white/[0.07] bg-white/[0.03] hover:border-cyan-300/20 hover:bg-white/[0.05]"}`}
                    >
                      <button
                        type="button"
                        onClick={() => { applyHistory(scan.id); setHistoryOpen(false); }}
                        className="w-full text-left"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="truncate text-sm font-black text-white">{scan.project_name || getHistoryWebsite(scan)}</p>
                            <p className="mt-1 truncate text-xs text-slate-500">{getHistoryWebsite(scan)}</p>
                          </div>
                          <span className={`shrink-0 rounded-full border px-2 py-1 text-[10px] font-black ${typeof scan.score === "number" && scan.score >= 85 ? "border-emerald-300/25 bg-emerald-300/[0.10] text-emerald-200" : typeof scan.score === "number" && scan.score < 65 ? "border-red-300/25 bg-red-300/[0.10] text-red-200" : "border-amber-300/25 bg-amber-300/[0.10] text-amber-100"}`}>{scan.score ?? "—"}</span>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-1.5 text-[10px] font-semibold text-slate-400">
                          <span className="rounded-full bg-white/[0.05] px-2 py-1">{formatDateTime(scan.created_at)}</span>
                          <span className="rounded-full bg-white/[0.05] px-2 py-1">{scan.findings_count ?? 0} findings</span>
                          <span className="rounded-full bg-white/[0.05] px-2 py-1">{scan.risk_label || "Saved"}</span>
                        </div>
                      </button>
                      <div className="mt-3 grid grid-cols-3 gap-2">
                        <button type="button" onClick={() => { applyHistory(scan.id); setHistoryOpen(false); }} className="rounded-lg border border-white/[0.08] bg-white/[0.04] px-2 py-1.5 text-[10px] font-black text-slate-300 transition hover:border-cyan-300/30 hover:text-cyan-100">Load</button>
                        <Link href="/results" onClick={() => applyHistory(scan.id)} className="rounded-lg border border-white/[0.08] bg-white/[0.04] px-2 py-1.5 text-center text-[10px] font-black text-slate-300 transition hover:border-cyan-300/30 hover:text-cyan-100">Results</Link>
                        <Link href="/report" onClick={() => applyHistory(scan.id)} className="rounded-lg border border-white/[0.08] bg-white/[0.04] px-2 py-1.5 text-center text-[10px] font-black text-slate-300 transition hover:border-cyan-300/30 hover:text-cyan-100">Report</Link>
                      </div>
                    </div>
                  )) : (
                    <p className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4 text-sm leading-6 text-slate-400">
                      {scanHistory.length ? "No scans match this search/filter." : "No saved scans found yet. Run a scan and save it to dashboard to see it here."}
                    </p>
                  )}
                </div>

                <div className="mt-5 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-3 text-xs leading-5 text-slate-500">
                  <p className="font-black text-slate-300">History rules</p>
                  <p className="mt-1">Loading a scan restores its saved result locally. Dashboard data is read-only from this panel; destructive delete is intentionally not included.</p>
                </div>
              </aside>
            </div>
          ) : null}

          <CardShell className="scanner-premium-console scanner-premium-console-clean card-glow">
            <div className="scanner-premium-aurora" aria-hidden="true" />
            <div className="scanner-premium-grid scanner-premium-grid-single">
              <div className="scanner-input-panel scanner-input-panel-wide">

                <div className="scanner-premium-fields">
                  <FieldLabel label="Website / dApp URL" required>
                    <input className="input scanner-input-xl scanner-premium-url" value={websiteUrl} onChange={(event) => setWebsiteUrl(event.target.value)} placeholder="https://yourproject.com" />
                  </FieldLabel>

                  <div className="scanner-field-row">
                    <FieldLabel label="Project type" required={scanMode !== "quick"}>
                      <select className="select scanner-choice-select" value={projectType} onChange={(event) => setProjectType(event.target.value)}>
                        <option value="" disabled>Select project type</option>
                        {projectTypeOptions.map((option) => <option key={option} value={option}>{option}</option>)}
                      </select>
                    </FieldLabel>

                    <FieldLabel label="Chain / surface" required={scanMode !== "quick"}>
                      <select className="select scanner-choice-select" value={chain} onChange={(event) => setChain(event.target.value)}>
                        <option value="" disabled>Select chain</option>
                        {chainOptions.map((option) => <option key={option} value={option}>{option}</option>)}
                      </select>
                    </FieldLabel>
                  </div>

                  {(projectType === 'Other' || chain === 'Other') ? (
                    <div className="scanner-field-row">
                      {projectType === 'Other' ? (
                        <FieldLabel label="Custom project type" required>
                          <input className="input" value={customProjectType} onChange={(event) => setCustomProjectType(event.target.value)} placeholder="Example: RWA, DePIN, AI x Web3" />
                        </FieldLabel>
                      ) : <div />}

                      {chain === 'Other' ? (
                        <FieldLabel label="Custom chain" required>
                          <input className="input" value={customChain} onChange={(event) => setCustomChain(event.target.value)} placeholder="Example: Sui, Aptos, Monad" />
                        </FieldLabel>
                      ) : <div />}
                    </div>
                  ) : null}
                </div>


                <div className="rounded-2xl border border-cyan-300/10 bg-cyan-300/[0.03] p-3">
                  <div className="grid gap-3 lg:grid-cols-[minmax(0,220px)_1fr] lg:items-end">
                    <FieldLabel label="Scan mode">
                      <select
                        className="input"
                        value={scanMode}
                        onChange={(event) => {
                          const nextMode = event.target.value as ScanMode;
                          setScanMode(nextMode);
                          setAdvancedOpen(nextMode !== "quick");
                          setActiveEvidenceEditor(null);
                        }}
                      >
                        {scanModeOptions.map((option) => (
                          <option key={option.id} value={option.id}>
                            {option.title}
                          </option>
                        ))}
                      </select>
                    </FieldLabel>
                    <div className="rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2">
                      <p className="text-xs text-slate-300">{activeScanMode.subtitle}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {activeScanMode.bullets.map((bullet) => (
                          <span key={bullet} className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] text-slate-400">
                            {bullet}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="scanner-evidence-panel">
                  <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/[0.02] p-3">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm font-semibold text-white">{scanMode === "quick" ? "Auto public evidence" : scanMode === "deep" ? "Deep evidence" : "Expert evidence"}</p>
                        <p className="mt-1 text-[11px] leading-5 text-slate-400">
                          {scanMode === "quick"
                            ? "URL-only scan auto-runs safe public checks."
                            : scanMode === "deep"
                              ? "Add repo, API, contract, or source evidence when needed."
                              : "Keep fields compact. Open only the editor you want to paste into."}
                        </p>
                      </div>
                      {scanMode === "quick" ? (
                        <span className="badge badge-cyan">Auto</span>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setAdvancedOpen((value) => !value)}
                          className="rounded-full border border-cyan-300/20 bg-cyan-300/[0.08] px-3 py-1.5 text-[11px] font-semibold text-cyan-100 transition hover:border-cyan-300/40 hover:bg-cyan-300/[0.14]"
                        >
                          {advancedOpen ? "Hide fields" : "Open fields"}
                        </button>
                      )}
                    </div>

                    {scanMode === "quick" ? (
                      <div className="scanner-evidence-chips" aria-label="Auto evidence types">
                        {["Headers/CSP", "Cookies", "Public exposure paths", "JS/API discovery", "Score proof", "Coverage gate"].map((item) => <span key={item}>{item}</span>)}
                      </div>
                    ) : null}

                    {scanMode !== "quick" && advancedOpen ? (
                      <>
                        <div className="grid gap-3 lg:grid-cols-3">
                          <FieldLabel label="Contract address">
                            <input className="input" value={contractAddress} onChange={(event) => setContractAddress(event.target.value)} placeholder="0x..." />
                          </FieldLabel>
                          <FieldLabel label="API base URL">
                            <input className="input" value={apiBaseUrl} onChange={(event) => setApiBaseUrl(event.target.value)} placeholder="https://api.yourproject.com" />
                          </FieldLabel>
                          <FieldLabel label="GitHub repo URL">
                            <input className="input" value={githubRepoUrl} onChange={(event) => setGithubRepoUrl(event.target.value)} placeholder="https://github.com/org/repo" />
                          </FieldLabel>
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-3">
                          <div className="flex flex-wrap gap-2">
                            {visibleEditorFields.map((field) => {
                              const selected = activeEvidenceEditor === field.id;
                              const filled = field.value.trim().length > 0;
                              return (
                                <button
                                  key={field.id}
                                  type="button"
                                  onClick={() => setActiveEvidenceEditor((current) => current === field.id ? null : field.id)}
                                  className={`rounded-lg border px-3 py-1.5 text-left text-[11px] font-semibold transition ${selected ? "border-cyan-300/40 bg-cyan-300/[0.10] text-cyan-100" : "border-white/10 bg-white/[0.03] text-slate-300 hover:border-cyan-300/20 hover:bg-white/[0.05]"}`}
                                >
                                  <span className="block">{field.label}</span>
                                  <span className={`mt-1 block text-[10px] ${filled ? "text-emerald-300" : "text-slate-500"}`}>{filled ? "Filled" : "Tap to open"}</span>
                                </button>
                              );
                            })}
                          </div>

                          {activeEvidenceField ? (
                            <div className="mt-3 rounded-2xl border border-cyan-300/15 bg-slate-950/50 p-3">
                              <div className="flex items-center justify-between gap-3">
                                <p className="text-sm font-semibold text-white">{activeEvidenceField.label}</p>
                                <button
                                  type="button"
                                  onClick={() => setActiveEvidenceEditor(null)}
                                  className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-400 transition hover:border-white/20 hover:text-slate-200"
                                >
                                  Hide
                                </button>
                              </div>
                              <textarea
                                className="textarea mt-3"
                                rows={activeEvidenceField.rows}
                                value={activeEvidenceField.value}
                                onChange={(event) => activeEvidenceField.setValue(event.target.value)}
                                placeholder={activeEvidenceField.placeholder}
                              />
                            </div>
                          ) : null}
                        </div>
                      </>
                    ) : null}
                  </div>
                </div>

                <div className="mt-5">
                  <label className={`scanner-terms-card ${termsAccepted ? "scanner-terms-card-on" : ""}`}>
                    <input type="checkbox" checked={termsAccepted} onChange={(event) => setScanTermsAccepted(event.target.checked)} />
                    <span className="scanner-terms-switch" aria-hidden="true"><span /></span>
                    <span className="min-w-0 flex-1">
                      <strong>Permission + Evidence Terms accepted</strong>
                      <small>I own this project or have permission to review it. Unavailable modules stay Not Assessed.</small>
                    </span>
                    <button type="button" onClick={(event) => { event.preventDefault(); setTermsOpen((value) => !value); }} className="rounded-full border border-white/10 px-3 py-1 text-[11px] font-black text-slate-300 transition hover:border-cyan-300/30 hover:text-cyan-100">
                      {termsOpen ? "Hide terms" : "View terms"}
                    </button>
                  </label>
                  {termsOpen ? (
                    <div className="mt-3 rounded-2xl border border-cyan-300/15 bg-cyan-300/[0.045] p-4 text-xs leading-6 text-slate-300">
                      <p className="font-black text-white">Scan terms and conditions</p>
                      <ul className="mt-3 list-disc space-y-2 pl-5">
                        <li>You confirm that you own the project or have explicit permission to review it.</li>
                        <li>Web3Guard runs evidence-first readiness checks only; it is not a certified audit or security guarantee.</li>
                        <li>No private key, seed phrase, mnemonic, wallet signing, exploit automation, DoS, brute force, credential stuffing, or destructive testing is allowed.</li>
                        <li>Missing provider keys, disabled tools, absent artifacts, or unavailable evidence remain Not Assessed instead of invented findings.</li>
                        <li>Tool output from Slither, Semgrep, and Aderyn is shown only when the backend really runs the tool or parses valid user-supplied artifacts.</li>
                        <li>Findings are pre-audit signals and must be manually verified before launch, public claims, or client delivery.</li>
                        <li>You agree not to scan third-party systems without authorization.</li>
                      </ul>
                    </div>
                  ) : null}
                </div>

                {fieldPrompt ? <p className="mt-4 rounded-xl border border-amber-300/20 bg-amber-300/10 p-3 text-sm text-amber-100">{fieldPrompt}</p> : null}

                <div className="scanner-action-row">
                  <button type="button" onClick={() => void runScan()} disabled={!canRunScan} className="btn-primary scanner-run-button">
                    {loading ? 'Scanning evidence...' : 'Run readiness scan →'}
                  </button>
                  {!isLoggedIn && !authLoading ? <Link href="/auth/login" className="btn-secondary scanner-login-button">Login first</Link> : null}
                </div>
              </div>
            </div>
          </CardShell>

        {loading ? (
          <CardShell>
            <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="section-label">Scan running</p>
                <h2 className="mt-2 text-2xl font-black text-white">{currentStage}</h2>
                <p className="mt-2 text-sm text-slate-400">Building a traceable report from current evidence.</p>
              </div>
              <ScoreOrb score={progress} label="progress" />
            </div>
            <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/[0.06]">
              <div className="h-full rounded-full bg-gradient-to-r from-cyan via-blue-500 to-purple-500 transition-all duration-500" style={{ width: `${progress}%` }} />
            </div>
            <div className="mt-5 grid gap-2 sm:grid-cols-3">
              {scanStages.map((stage, index) => (
                <div key={stage} className={`rounded-xl border p-3 text-xs font-bold ${index <= stageIndex ? "border-cyan/25 bg-cyan/10 text-cyan-50" : "border-white/[0.07] bg-white/[0.03] text-slate-500"}`}>
                  {stage}
                </div>
              ))}
            </div>
          </CardShell>
        ) : null}

        {error ? (
          <CardShell className="border-red-400/25 bg-red-500/10">
            <p className="text-sm font-black uppercase tracking-[0.2em] text-red-200">Action needed</p>
            <p className="mt-3 text-sm leading-6 text-red-100">{error}</p>
          </CardShell>
        ) : null}

        {saveMessage ? (
          <CardShell className="border-emerald-400/20 bg-emerald-400/10">
            <p className="text-sm font-black text-emerald-100">{saveMessage}</p>
          </CardShell>
        ) : null}

        {result ? (
          <div className="space-y-6">
            <CardShell className="card-glow">
              <div className="grid gap-6 lg:grid-cols-[auto_1fr] lg:items-center">
                <ScoreOrb score={heroScore} label={heroLabel} />
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`badge ${riskBadgeClass(result.risk_label)}`}>{result.risk_label || "Not Assessed"}</span>
                    <span className="badge badge-cyan">Report {result.report_id}</span>
                    <span className="badge">{formatDateTime(result.generated_at)}</span>
                  </div>
                  <h2 className="mt-4 text-3xl font-black text-white">{result.project_name || result.website_url}</h2>
                  <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">{result.safe_public_summary || "Launch readiness result generated from supplied evidence."}</p>
                  <div className="mt-5 grid gap-3 sm:grid-cols-3">
                    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                      <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Assessed</p>
                      <p className="mt-1 text-2xl font-black text-white">{result.assessed_modules?.length || result.live_module_count || 0}</p>
                    </div>
                    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                      <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Not Assessed</p>
                      <p className="mt-1 text-2xl font-black text-white">{result.not_assessed_modules?.length || 0}</p>
                    </div>
                    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                      <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Actions</p>
                      <p className="mt-1 text-2xl font-black text-white">{result.priority_actions?.length || 0}</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardShell>

            <StaticToolStatusPanel result={result} />

            {coverageGate ? (
              <CardShell className={overallAllowed ? "border-emerald-400/20 bg-emerald-400/10" : "border-amber-300/20 bg-amber-300/10"}>
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p className="section-label">Truth gate</p>
                    <h2 className="mt-2 text-2xl font-black text-white">{overallAllowed ? "Overall confidence allowed" : "Overall confidence blocked"}</h2>
                    <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-300">{coverageGate.reason}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{coverageGate.display_rule}</p>
                  </div>
                  <div className="grid min-w-[260px] gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
                      <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Coverage</p>
                      <p className="mt-2 text-2xl font-black text-white">{coverageGate.assessed_count}/{coverageGate.total_modules}</p>
                    </div>
                    <div className="rounded-2xl border border-white/[0.08] bg-black/20 p-4">
                      <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Overall score</p>
                      <p className="mt-2 text-2xl font-black text-white">{overallAllowed ? result.overall_score ?? "—" : "Gated"}</p>
                    </div>
                  </div>
                </div>
              </CardShell>
            ) : null}

            <CardShell>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="section-label">Split scores</p>
                  <h2 className="mt-2 text-2xl font-black text-white">Launch confidence, not audit score</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-400">Each score explains its evidence basis. Missing evidence stays outside the score instead of being guessed.</p>
                </div>
                {scoreSplit?.note ? <span className="badge badge-amber">Pre-audit only</span> : null}
              </div>
              <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {splitCards.map((item) => <SplitScoreCard key={item.key} item={item} />)}
              </div>
            </CardShell>

            <CardShell>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="section-label">Exports</p>
                  <h2 className="mt-2 text-2xl font-black text-white">Report artifacts</h2>
                  <p className="mt-2 text-sm text-slate-400">Exports are built from this scan result and keep limitations visible.</p>
                </div>
                <button className="btn-secondary sm:w-auto" type="button" onClick={() => void saveUnifiedScanToDashboard()} disabled={saveLoading}>
                  {saveLoading ? "Saving..." : "Save to dashboard"}
                </button>
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-4">
                {(["pdf", "html", "markdown", "json"] as ExportFormat[]).map((format) => (
                  <button key={format} type="button" className="btn-primary !px-4 !py-3 text-xs" onClick={() => void exportCurrentReport(format)}>
                    Download {format === "markdown" ? "MD" : format.toUpperCase()}
                  </button>
                ))}
              </div>
              {exportStatus ? <p className="mt-4 rounded-xl border border-cyan/20 bg-cyan/10 p-3 text-sm text-cyan-50">{exportStatus}</p> : null}
            </CardShell>

            {realEvidenceSummary ? (
              <CardShell>
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p className="section-label">Real evidence</p>
                    <h2 className="mt-2 text-2xl font-black text-white">Observed issues vs hardening hints</h2>
                    <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">{realEvidenceSummary.summary_rule}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{realEvidenceSummary.confirmed_exploit_note}</p>
                  </div>
                  <div className="grid min-w-[300px] gap-3 sm:grid-cols-3">
                    <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
                      <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Observed</p>
                      <p className="mt-2 text-2xl font-black text-white">{realEvidenceSummary.real_observed_issue_count}</p>
                    </div>
                    <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
                      <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Hints</p>
                      <p className="mt-2 text-2xl font-black text-white">{realEvidenceSummary.potential_hardening_hint_count}</p>
                    </div>
                    <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
                      <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Exploits proved</p>
                      <p className="mt-2 text-2xl font-black text-white">{realEvidenceSummary.confirmed_exploit_count}</p>
                    </div>
                  </div>
                </div>
                <details className="mt-5 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4 text-xs text-slate-400">
                  <summary className="cursor-pointer font-black text-white">Show raw passive website evidence</summary>
                  <pre className="mt-4 max-h-80 overflow-auto whitespace-pre-wrap break-words">{safeJsonStringify(realEvidenceSummary.website_raw_evidence)}</pre>
                </details>
              </CardShell>
            ) : null}

            <DynamicScoreTraceCard trace={dynamicScoreTrace} />

            <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
              <CardShell>
                <p className="section-label">Priority actions</p>
                <h2 className="mt-2 text-2xl font-black text-white">Findings with fix hints</h2>
                <div className="mt-5 space-y-3">
                  {result.priority_actions?.length ? result.priority_actions.map((action, index) => <FindingCard key={`${action.title}-${index}`} action={action} />) : <p className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-100">No priority findings were returned for the assessed evidence.</p>}
                </div>
              </CardShell>

              <CardShell>
                <p className="section-label">Evidence gaps</p>
                <h2 className="mt-2 text-2xl font-black text-white">Not Assessed queue</h2>
                <div className="mt-5 space-y-3">
                  {requiredInputs.length ? requiredInputs.map(({ label, item, guide }) => (
                    <div key={`${label}-${item}`} className="rounded-2xl border border-amber-300/15 bg-amber-300/10 p-4">
                      <p className="text-sm font-black text-amber-50">{label}</p>
                      <p className="mt-2 text-sm leading-6 text-amber-100/90">{item}</p>
                      <p className="mt-3 text-xs leading-5 text-amber-100/70">{guide}</p>
                    </div>
                  )) : <p className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-100">No missing evidence listed in this result.</p>}
                </div>
              </CardShell>
            </div>

            <CardShell>
              <p className="section-label">Module matrix</p>
              <h2 className="mt-2 text-2xl font-black text-white">Assessed vs Not Assessed</h2>
              <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {cards.map((card) => <ModuleCard key={card.module} card={card} />)}
              </div>
            </CardShell>

            {result.warnings?.length || result.blocked_claims?.length ? (
              <CardShell>
                <p className="section-label">Boundaries</p>
                <div className="mt-5 grid gap-4 md:grid-cols-2">
                  {result.warnings?.length ? (
                    <div className="rounded-2xl border border-amber-300/15 bg-amber-300/10 p-4">
                      <p className="font-black text-amber-50">Warnings</p>
                      <ul className="mt-3 space-y-2 text-sm leading-6 text-amber-100/85">{result.warnings.map((item) => <li key={item}>• {item}</li>)}</ul>
                    </div>
                  ) : null}
                  {result.blocked_claims?.length ? (
                    <div className="rounded-2xl border border-red-400/20 bg-red-500/10 p-4">
                      <p className="font-black text-red-100">Do not claim</p>
                      <ul className="mt-3 space-y-2 text-sm leading-6 text-red-100/85">{result.blocked_claims.map((item) => <li key={item}>• {item}</li>)}</ul>
                    </div>
                  ) : null}
                </div>
              </CardShell>
            ) : null}
          </div>
        ) : null}
        </div>
      </section>
    </main>
  );
}
