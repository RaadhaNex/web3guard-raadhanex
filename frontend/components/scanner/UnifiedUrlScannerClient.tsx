
"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { API_BASE, apiGet, apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
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
  "Passive website review",
  "Optional evidence mapping",
  "Readiness scoring",
  "Report package",
];

const moduleOrder = ["website", "dapp", "api", "contract", "wallet", "admin_opsec", "github"];

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

type ProjectMode = "new" | "existing";
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
      score: result.overall_score ?? result.available_score ?? null,
      status: result.overall_score == null ? "Partial assessed confidence" : "Full assessed confidence",
      risk_label: result.risk_label || "Not Assessed",
      source: "Uses assessed modules only when evidence is present; missing modules stay outside confidence.",
    },
    no_full_audit_score: result.overall_score == null,
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

function CardShell({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`card p-5 sm:p-6 ${className}`}>{children}</section>;
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
          <p className="mt-1">{card.required_input[0]}</p>
        </div>
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
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const [authLoading, setAuthLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [scanHistory, setScanHistory] = useState<ScanHistoryRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [selectedHistoryId, setSelectedHistoryId] = useState("");

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

  const resolvedProjectType = useMemo(() => projectType === "Other" ? customProjectType.trim() || "Other" : projectType.trim() || "Not selected", [customProjectType, projectType]);
  const resolvedChain = useMemo(() => chain === "Other" ? customChain.trim() || "Other" : chain.trim() || "Web only", [chain, customChain]);

  const missingRequiredFields = useMemo(() => {
    const missing: string[] = [];
    if (!websiteUrl.trim()) missing.push("Website / dApp URL");
    if (!projectType.trim()) missing.push("Project type");
    if (projectType === "Other" && !customProjectType.trim()) missing.push("Custom project type");
    if (!chain.trim()) missing.push("Chain / surface");
    if (chain === "Other" && !customChain.trim()) missing.push("Custom chain");
    if (!authorized) missing.push("Authorization confirmation");
    if (!realOnly) missing.push("Evidence-only acknowledgement");
    return missing;
  }, [authorized, chain, customChain, customProjectType, projectType, realOnly, websiteUrl]);

  const canRunScan = !loading && !authLoading;
  const cards = result?.module_cards ? sortModuleCards(result.module_cards) : [];
  const scoreSplit = result ? buildScoreSplit(result) : null;
  const splitCards = scoreSplit ? scoreSplitCards(scoreSplit) : [];
  const requiredInputs = result?.module_cards.flatMap((card) => (card.required_input || []).map((item) => ({ label: card.label, item, guide: moduleFixGuide(card) }))) || [];

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
    setAdvancedOpen(false);
    setResult(null);
    setError(null);
    setFieldPrompt(null);
    setExportStatus(null);
    setSaveMessage(null);
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
      setProgress((value) => (value >= 92 ? value : value + 7));
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
          authorization_confirmed: authorized,
          real_only_acknowledged: realOnly,
        },
        { headers }
      );
      setStageIndex(scanStages.length - 1);
      setProgress(100);
      setResult(data);
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
      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl space-y-6">
          <CardShell className="scanner-premium-console card-glow">
            <div className="scanner-premium-aurora" aria-hidden="true" />
            <div className="scanner-premium-grid scanner-premium-grid-single">
              <div className="scanner-input-panel scanner-input-panel-wide">
                <div className="scanner-input-head">
                  <div>
                    <p className="section-label">Scan setup</p>
                    <h2>Paste URL and choose surface</h2>
                  </div>
                  <span className={`scanner-ready-pill ${missingRequiredFields.length ? 'scanner-ready-pill-warn' : 'scanner-ready-pill-ok'}`}>
                    {missingRequiredFields.length ? 'Needs input' : 'Ready'}
                  </span>
                </div>

                <div className="scanner-premium-fields">
                  <FieldLabel label="Website / dApp URL" required>
                    <input className="input scanner-input-xl scanner-premium-url" value={websiteUrl} onChange={(event) => setWebsiteUrl(event.target.value)} placeholder="https://yourproject.com" />
                  </FieldLabel>

                  <div className="scanner-field-row">
                    <FieldLabel label="Project type" required>
                      <select className="select scanner-choice-select" value={projectType} onChange={(event) => setProjectType(event.target.value)}>
                        <option value="" disabled>Select project type</option>
                        {projectTypeOptions.map((option) => <option key={option} value={option}>{option}</option>)}
                      </select>
                    </FieldLabel>

                    <FieldLabel label="Chain / surface" required>
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

                <div className="scanner-evidence-panel">
                  <button type="button" onClick={() => setAdvancedOpen((value) => !value)} className="scanner-evidence-toggle">
                    <span className="scanner-chip-icon">＋</span>
                    <span>
                      <strong>Optional evidence</strong>
                      <small>Contract, API, GitHub, and Solidity source can add context.</small>
                    </span>
                    <b>{advancedOpen ? 'Close' : 'Add'}</b>
                  </button>

                  {!advancedOpen ? (
                    <div className="scanner-evidence-chips" aria-label="Optional evidence types">
                      {['Contract address', 'API base', 'GitHub repo', 'Solidity source'].map((item) => <span key={item}>{item}</span>)}
                    </div>
                  ) : null}

                  {advancedOpen ? (
                    <div className="scanner-evidence-grid">
                      <FieldLabel label="Contract address">
                        <input className="input" value={contractAddress} onChange={(event) => setContractAddress(event.target.value)} placeholder="0x..." />
                      </FieldLabel>
                      <FieldLabel label="API base URL">
                        <input className="input" value={apiBaseUrl} onChange={(event) => setApiBaseUrl(event.target.value)} placeholder="https://api.yourproject.com" />
                      </FieldLabel>
                      <FieldLabel label="GitHub repo URL">
                        <input className="input" value={githubRepoUrl} onChange={(event) => setGithubRepoUrl(event.target.value)} placeholder="https://github.com/org/repo" />
                      </FieldLabel>
                      <div className="scanner-evidence-wide">
                        <FieldLabel label="Solidity source">
                          <textarea className="textarea" value={solidityCode} onChange={(event) => setSolidityCode(event.target.value)} placeholder="Paste Solidity source here for local rule checks." />
                        </FieldLabel>
                      </div>
                    </div>
                  ) : null}
                </div>

                <div className="scanner-consent-grid">
                  <label className={`scanner-check-card ${authorized ? "scanner-check-card-on" : ""}`}>
                    <input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} />
                    <span>
                      <strong>Permission confirmed</strong>
                      <small>I own this project or have permission to review it.</small>
                    </span>
                  </label>
                  <label className={`scanner-check-card ${realOnly ? "scanner-check-card-on" : ""}`}>
                    <input type="checkbox" checked={realOnly} onChange={(event) => setRealOnly(event.target.checked)} />
                    <span>
                      <strong>Evidence-only result</strong>
                      <small>Unavailable modules stay Not Assessed.</small>
                    </span>
                  </label>
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
                <ScoreOrb score={result.overall_score ?? result.available_score ?? null} label="confidence" />
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
