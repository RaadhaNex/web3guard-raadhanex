"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { API_BASE, apiGet, apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
import type { ProjectRecord, ScanHistoryRecord, UnifiedModuleCard, UnifiedUrlScanResponse } from "@/lib/types";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

const moduleOrder = [
  "website",
  "dapp",
  "api",
  "contract",
  "wallet",
  "admin_opsec",
  "github",
];

const scanStages = [
  "Checking login session",
  "Validating target URL",
  "Running passive website checks",
  "Checking API / GitHub / contract inputs",
  "Building evidence-based result",
  "Preparing fix guidance",
];

function statusClass(status: string) {
  const lowered = status.toLowerCase();

  if (lowered.startsWith("live")) {
    return "border-emerald-400/40 bg-emerald-500/10 text-emerald-700";
  }

  if (lowered.includes("manual") || lowered.includes("input")) {
    return "border-amber-400/40 bg-amber-500/10 text-amber-800";
  }

  if (lowered.includes("not assessed")) {
    return "border-slate-300 bg-slate-100 text-slate-700";
  }

  return "border-cyan-400/40 bg-cyan-500/10 text-cyan-700";
}

function scoreTone(score?: number | null) {
  if (typeof score !== "number") return "text-slate-500";
  if (score >= 85) return "text-emerald-600";
  if (score >= 65) return "text-amber-600";
  return "text-rose-600";
}

function normaliseUrl(value: string) {
  const clean = value.trim();

  if (!clean) return "";

  if (clean.startsWith("http://") || clean.startsWith("https://")) {
    return clean;
  }

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
  if (!error) return "Unknown error. Please check backend logs.";

  if (error instanceof Error) {
    if (error.message === "[object Object]") {
      return "Backend returned a structured error object, but the old API client could not format it. Replace frontend/lib/api.ts with the fixed version in this patch, then re-run the scan.";
    }

    return error.message;
  }

  if (typeof error === "string") {
    if (error === "[object Object]") {
      return "Backend returned a structured error object. Replace frontend/lib/api.ts with the fixed version in this patch.";
    }

    return error;
  }

  if (typeof error === "object") {
    const record = error as Record<string, unknown>;

    if (typeof record.message === "string") return record.message;
    if (typeof record.error === "string") return record.error;
    if (typeof record.detail === "string") return record.detail;

    if (record.detail) return readableClientError(record.detail);
    if (record.msg) return readableClientError(record.msg);

    return safeJsonStringify(error);
  }

  return String(error);
}

function getActionFixGuide(title: string, module?: string) {
  const text = `${title} ${module || ""}`.toLowerCase();

  if (text.includes("content-security-policy") || text.includes("csp")) {
    return {
      file: "frontend/next.config.mjs",
      why:
        "CSP reduces XSS impact by controlling which scripts, frames, images, and connections are allowed.",
      fix:
        "Add a Content-Security-Policy header in Next.js headers(). Allow only your domain, Supabase, backend API, and Razorpay if enabled.",
      verify:
        "Run curl -I https://your-domain.com and confirm Content-Security-Policy is present.",
    };
  }

  if (text.includes("rate limit")) {
    return {
      file: "backend middleware / scan routers",
      why:
        "Without rate limits, scan endpoints can be abused and your Render/Supabase quota can be exhausted.",
      fix:
        "Enforce per-user and per-IP limits for URL scan, GitHub scan, contract scan, and payment/order endpoints.",
      verify:
        "Send repeated requests and confirm the API returns 429 after the configured limit.",
    };
  }

  if (text.includes("webhook")) {
    return {
      file: "backend/app/routers/payments.py",
      why:
        "Payment status must not be trusted unless the Razorpay webhook signature is verified.",
      fix:
        "Verify X-Razorpay-Signature using the raw request body and RAZORPAY_WEBHOOK_SECRET before marking payment as paid.",
      verify:
        "Use Razorpay test webhook and confirm invalid signatures are rejected.",
    };
  }

  if (text.includes("bola") || text.includes("idor")) {
    return {
      file: "backend project/report/scan detail endpoints",
      why:
        "BOLA/IDOR allows one logged-in user to access another user's project, scan, or report.",
      fix:
        "For every object endpoint, verify JWT user id matches record.user_id before returning data.",
      verify:
        "Login as user A and try to open user B's project/report id. It should return 403/404.",
    };
  }

  if (text.includes("api docs") || text.includes("docs exposure")) {
    return {
      file: "backend/main.py",
      why:
        "Public /docs, /redoc, and /openapi.json can expose API structure in production.",
      fix:
        "Disable docs in production or protect them behind admin authentication.",
      verify:
        "Open /docs on production. It should be unavailable or protected.",
    };
  }

  if (text.includes("auth")) {
    return {
      file: "Supabase Auth + frontend auth pages",
      why:
        "Launch dashboards must prove signup, email confirmation, login, logout, and protected routes work correctly.",
      fix:
        "Test Supabase URL config, /auth/callback, dashboard protection, and logout session clearing.",
      verify:
        "Logout, then open /dashboard. It should require login and must not create a fake session.",
    };
  }

  return {
    file: "Manual review required",
    why:
      "This finding needs project-specific context before it can be safely auto-fixed.",
    fix:
      "Document the current setup, owner, data flow, and risk. Then add a specific control or checklist evidence.",
    verify:
      "Re-run the scan and confirm the finding is resolved or marked as manually accepted.",
  };
}

function moduleFixGuide(card: UnifiedModuleCard) {
  const module = card.module.toLowerCase();

  if (module === "wallet") {
    return "Add a wallet-flow checklist: connect wallet UX, transaction preview, phishing warning, chain mismatch handling, and no seed/private-key collection.";
  }

  if (module === "admin_opsec") {
    return "Add admin OpSec evidence: MFA, role separation, treasury multisig, timelock, key storage policy, and break-glass procedure.";
  }

  if (module === "contract") {
    return "Paste Solidity source or provide a verified testnet/mainnet contract address. Missing contract input stays Not assessed.";
  }

  if (module === "dapp") {
    return "Provide dApp source/GitHub repo and wallet-flow proof for deeper frontend scoring.";
  }

  if (module === "api") {
    return "Expose only intended API endpoints, add rate limits, auth checks, and production docs protection.";
  }

  if (module === "github") {
    return "Review exposed secrets, CI permissions, dependency hygiene, and branch protection settings.";
  }

  return "Review evidence, fix the listed gaps, then re-run the scan.";
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

function fixGuideForFinding(title: string, module?: string) {
  const guide = getActionFixGuide(title, module);
  return {
    where_to_fix: guide.file,
    why_it_matters: guide.why,
    how_to_fix: guide.fix,
    verify: guide.verify,
  };
}

function buildInlineMarkdownReport(report: Record<string, unknown>) {
  const findings = Array.isArray(report.top_findings) ? (report.top_findings as Array<Record<string, unknown>>) : [];
  const evidenceRequired = Array.isArray(report.evidence_required) ? (report.evidence_required as Array<Record<string, unknown>>) : [];
  const matrix = Array.isArray(report.module_matrix) ? (report.module_matrix as Array<Record<string, unknown>>) : [];

  const lines = [
    `# ${String(report.project_name || "Web3Guard Launch Surface Report")}`,
    "",
    `Report ID: ${String(report.report_id || "not-generated")}`,
    `Verification hash: ${String(report.report_hash || "not-available")}`,
    "",
    "## Important note",
    "This is generated from real scanner/checklist/passive data only. Missing modules remain Not assessed. This is not a certified audit.",
    "",
    "## Executive summary",
    String(report.executive_summary || "No executive summary provided."),
    "",
    "## Split readiness scores",
  ];

  const scoreSplit = (report.score_split || {}) as Record<string, any>;
  scoreSplitCards(scoreSplit).forEach((item) => {
    lines.push(
      `- **${String(item.label)}**: ${typeof item.score === "number" ? item.score : "Not assessed"} — ${String(item.status || "Not assessed")}`,
      `  - Evidence basis: ${String(item.source || "Not provided")}`
    );
  });

  lines.push(
    "",
    "## Real bugs / findings with fix hints",
  );

  if (findings.length) {
    findings.forEach((finding, index) => {
      const fix = (finding.fix_guidance || {}) as Record<string, unknown>;
      lines.push(
        `${index + 1}. **${String(finding.severity || "info").toUpperCase()} — ${String(finding.title || "Finding")}**`,
        `   - Module: ${String(finding.module || "unknown")}`,
        `   - Recommendation: ${String(finding.recommendation || "Review and fix before launch.")}`,
        `   - Where to fix: ${String(fix.where_to_fix || "Manual review required")}`,
        `   - How to fix: ${String(fix.how_to_fix || "Apply project-specific fix and re-run scan.")}`,
        `   - Verify: ${String(fix.verify || "Re-run scan after the fix.")}`
      );
    });
  } else {
    lines.push("No real assessed-module bugs were detected in the current scan payload.");
  }

  lines.push("", "## Evidence required / Not assessed modules");
  if (evidenceRequired.length) {
    evidenceRequired.forEach((item) => {
      lines.push(`- **${String(item.module_label || item.module || "Module")}**: ${String(item.required_input || "Missing evidence")}`);
    });
  } else {
    lines.push("No missing evidence was listed.");
  }

  lines.push("", "## Module matrix");
  matrix.forEach((row) => {
    lines.push(`- ${String(row.label || row.module || "Module")}: ${row.score ?? "Not assessed"} · ${String(row.status || "Not assessed")}`);
  });

  lines.push("", "## Disclaimer", String(report.disclaimer || "Not a certified audit."));
  return lines.join("\n");
}


function buildScoreSplit(result: UnifiedUrlScanResponse) {
  if (result.score_split) return result.score_split;

  const byModule = new Map(result.module_cards.map((card) => [card.module, card]));
  const moduleEntry = (module: string, label: string, source: string) => {
    const card = byModule.get(module);
    const assessed = Boolean(card?.assessed);
    return {
      label,
      score: assessed ? card?.score ?? null : null,
      status: card?.status || "Not assessed",
      risk_label: card?.risk_label || "Not assessed",
      source: assessed ? source : "Not Assessed — required evidence was not provided.",
    };
  };
  const total = result.module_cards.length || 1;
  const assessed = result.module_cards.filter((card) => card.assessed).length;
  const missing = result.module_cards.reduce((count, card) => count + (card.required_input?.length || 0), 0);
  const evidenceScore = Math.max(0, Math.min(100, Math.round((assessed / total) * 100 - Math.min(missing * 2, 24))));
  return {
    website_surface_score: moduleEntry("website", "Website Surface Score", "Passive public URL evidence: HTTP/HTTPS, headers, HTML hints, robots/sitemap/policy signals."),
    contract_rule_score: moduleEntry("contract", "Contract Rule Score", "Pasted Solidity or verified explorer source analyzed by local rules. External tools remain separate."),
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
      risk_label: result.risk_label || "Not assessed",
      source: "Uses all weighted modules only when all are assessed. Otherwise uses assessed-module available score and marks confidence as partial.",
    },
    no_full_audit_score: result.overall_score == null,
    note: "These are launch-readiness scores, not a certified audit score, penetration-test score, or guarantee of security.",
  };
}

function scoreSplitCards(scoreSplit: Record<string, any>) {
  return ["website_surface_score", "contract_rule_score", "launch_evidence_score", "overall_launch_confidence"]
    .map((key) => ({ key, ...(scoreSplit[key] || {}) }))
    .filter((item) => item.label);
}

function buildInlineReportFromResult(result: UnifiedUrlScanResponse) {
  const combined = (result.combined_report || {}) as Record<string, any>;
  const realFindings = (result.priority_actions || []).map((item) => ({
    severity: item.severity,
    module: item.module,
    title: item.title,
    confidence: "medium",
    recommendation: item.recommended_action,
    business_impact: item.business_impact || "Fix before launch if this affects production users or funds.",
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

  const evidenceSummary = result.module_cards.map((card) => ({
    module: card.module,
    module_label: card.label,
    status: card.status,
    score: card.score ?? null,
    evidence: card.evidence || [],
    limitations: card.limitations || [],
  }));

  const scoreSplit = buildScoreSplit(result);

  const moduleMatrix = result.module_cards.map((card) => ({
    label: card.label,
    module: card.module,
    weight_percent: card.assessed ? "assessed-only" : "not-scored",
    score: card.score ?? null,
    risk_label: card.risk_label || card.status || "Not assessed",
    assessed: Boolean(card.assessed || card.score !== null),
    status: card.status || "Not assessed",
    evidence: (card.evidence || []).slice(0, 4).join(" | ") || "No evidence provided",
  }));

  const report: Record<string, unknown> = {
    ...combined,
    report_id: result.report_id || combined.report_id,
    report_hash: combined.report_hash,
    generated_at: result.generated_at || combined.generated_at,
    project_name: result.project_name || combined.project_name || result.website_url,
    combined: {
      ...(combined.combined || {}),
      overall_score: result.overall_score ?? null,
      available_score: result.available_score ?? null,
      risk_label: result.risk_label || combined.combined?.risk_label || "Not assessed",
    },
    coverage: result.coverage || combined.coverage,
    score_split: scoreSplit,
    module_matrix: moduleMatrix,
    priority_action_plan: result.priority_actions || [],
    top_findings: realFindings,
    evidence_required: evidenceRequired,
    evidence_summary: evidenceSummary,
    executive_summary:
      result.safe_public_summary ||
      combined.executive_summary ||
      "Preliminary launch-surface report generated from real scanner evidence.",
    risk_narrative:
      result.realness_rule ||
      combined.risk_narrative ||
      "Only assessed modules receive scores. Missing modules remain Not assessed.",
    limitations: [
      result.disclaimer,
      "URL-only scans are partial by design.",
      "Missing modules remain Not assessed and are not fake-scored.",
      "This is not a certified audit, penetration test, or guarantee of security.",
    ].filter(Boolean),
    before_launch_checklist: combined.before_launch_checklist || [],
    package_recommendation: combined.package_recommendation || {
      package: "Complete missing evidence before public launch decisions",
      reason: "Report confidence depends on assessed modules and real evidence.",
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

function sortModuleCards(cards: UnifiedModuleCard[]) {
  return [...cards].sort((a, b) => {
    const aIndex = moduleOrder.indexOf(a.module);
    const bIndex = moduleOrder.indexOf(b.module);

    return (aIndex === -1 ? 999 : aIndex) - (bIndex === -1 ? 999 : bIndex);
  });
}


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

function formatDateTime(value?: string | null) {
  if (!value) return "Not available";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function getHistoryPayload(scan: ScanHistoryRecord) {
  return (scan.payload || {}) as Partial<UnifiedUrlScanResponse> & Record<string, unknown>;
}

function getHistoryWebsite(scan: ScanHistoryRecord) {
  const payload = getHistoryPayload(scan);
  const website = typeof payload.website_url === "string" ? payload.website_url : "";
  return website || "No URL stored";
}

function looksLikeUnifiedResult(payload: Record<string, unknown>): payload is UnifiedUrlScanResponse {
  return Boolean(
    typeof payload.website_url === "string" &&
      typeof payload.report_id === "string" &&
      Array.isArray(payload.module_cards)
  );
}

export function UnifiedUrlScannerClient() {
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [projectName, setProjectName] = useState("");
  const [projectMode, setProjectMode] = useState<ProjectMode>("new");
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [projectType, setProjectType] = useState(projectTypeOptions[0]);
  const [customProjectType, setCustomProjectType] = useState("");
  const [chain, setChain] = useState("Web only");
  const [customChain, setCustomChain] = useState("");
  const [contractAddress, setContractAddress] = useState("");
  const [apiBaseUrl, setApiBaseUrl] = useState("");
  const [githubRepoUrl, setGithubRepoUrl] = useState("");
  const [solidityCode, setSolidityCode] = useState("");
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);

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
  const [codeEditorOpen, setCodeEditorOpen] = useState(false);
  const [exportStatus, setExportStatus] = useState<string | null>(null);

  const currentStage = scanStages[Math.min(stageIndex, scanStages.length - 1)];
  const selectedProject = projects.find((project) => project.id === selectedProjectId) || null;
  const selectedHistory = scanHistory.find((scan) => scan.id === selectedHistoryId) || null;

  const resolvedProjectType = useMemo(() => {
    if (projectType === "Other") return customProjectType.trim() || "Other";
    return projectType.trim() || projectTypeOptions[0];
  }, [customProjectType, projectType]);

  const resolvedChain = useMemo(() => {
    if (chain === "Other") return customChain.trim() || "Other";
    return chain.trim() || "Web only";
  }, [chain, customChain]);

  const missingRequiredFields = useMemo(() => {
    const missing: string[] = [];

    if (!projectName.trim()) missing.push("Project name");
    if (!websiteUrl.trim()) missing.push("Website / dApp URL");
    if (projectMode === "existing" && !selectedProjectId) missing.push("Existing project");
    if (projectType === "Other" && !customProjectType.trim()) missing.push("Custom project type");
    if (!authorized) missing.push("authorization confirmation");
    if (!realOnly) missing.push("real-only acknowledgement");

    return missing;
  }, [authorized, customProjectType, projectMode, projectName, projectType, realOnly, selectedProjectId, websiteUrl]);

  const canRunScan = useMemo(() => {
    return !loading && !authLoading;
  }, [authLoading, loading]);

  function setKnownProjectType(value?: string | null) {
    if (!value) return;

    if (projectTypeOptions.includes(value)) {
      setProjectType(value);
      setCustomProjectType("");
      return;
    }

    setProjectType("Other");
    setCustomProjectType(value);
  }

  function setKnownChain(value?: string | null) {
    if (!value) return;

    if (chainOptions.includes(value)) {
      setChain(value);
      setCustomChain("");
      return;
    }

    setChain("Other");
    setCustomChain(value);
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

      const [projectData, scanData] = await Promise.all([
        apiGet<{ projects: ProjectRecord[] }>(`/projects?user_id=${queryUser}&limit=100`, { headers }),
        apiGet<{ scans: ScanHistoryRecord[] }>(`/scan-history?user_id=${queryUser}&limit=30`, { headers }),
      ]);

      setProjects(projectData.projects || []);
      setScanHistory(
        (scanData.scans || []).filter((scan) =>
          scan.module === "unified_url" || looksLikeUnifiedResult(getHistoryPayload(scan) as Record<string, unknown>)
        )
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
    setSaveMessage("Existing project loaded. Run a fresh scan or choose a saved scan history item.");
  }

  function startNewProject() {
    setProjectMode("new");
    setSelectedProjectId("");
    setProjectName("");
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
    const historyProjectName =
      scan.project_name || (typeof payload.project_name === "string" ? payload.project_name : "");
    const historyProjectType = typeof payload.project_type === "string" ? payload.project_type : null;
    const historyChain = typeof payload.chain === "string" ? payload.chain : null;

    if (historyWebsite) setWebsiteUrl(historyWebsite);
    if (historyProjectName) setProjectName(historyProjectName);
    setKnownProjectType(historyProjectType);
    setKnownChain(historyChain);

    if (scan.project_id) {
      setSelectedProjectId(scan.project_id);
      setProjectMode("existing");
    }

    if (looksLikeUnifiedResult(payload)) {
      setResult(payload);
      setSaveMessage(`Loaded saved scan from ${formatDateTime(scan.created_at)}. You can export it or re-run a fresh scan.`);
      return;
    }

    setSaveMessage(`Loaded history inputs from ${formatDateTime(scan.created_at)}. Run scan to generate a fresh result.`);
  }

  useEffect(() => {
    let mounted = true;

    async function checkAuth() {
      setAuthLoading(true);

      try {
        await getCurrentUserId();

        if (mounted) {
          setIsLoggedIn(true);
        }
      } catch {
        if (mounted) {
          setIsLoggedIn(false);
        }
      } finally {
        if (mounted) {
          setAuthLoading(false);
        }
      }
    }

    void checkAuth();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!isLoggedIn) return;
    void loadWorkspaceQuickData();
  }, [isLoggedIn]);

  useEffect(() => {
    if (!loading) return;

    setProgress(8);
    setStageIndex(0);

    const timer = window.setInterval(() => {
      setProgress((value) => {
        if (value >= 92) return value;
        return value + 7;
      });

      setStageIndex((value) => {
        if (value >= scanStages.length - 2) return value;
        return value + 1;
      });
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
      setError("Login required. Please login before running a real scan.");
      return;
    }

    if (missingRequiredFields.length) {
      const message = `Please fill required fields: ${missingRequiredFields.join(", ")}.`;
      setFieldPrompt(message);
      setError(message);
      return;
    }

    const cleanWebsiteUrl = normaliseUrl(websiteUrl);

    if (!cleanWebsiteUrl) {
      const message = "Please enter a valid website / dApp URL.";
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
      setTimeout(() => {
        setLoading(false);
      }, 350);
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
            name: projectName.trim() || result.project_name || "Unified URL Scan",
            website_url: websiteUrl,
            chain: resolvedChain,
            contract_address: contractAddress || null,
            github_repo_url: githubRepoUrl || null,
            project_type: resolvedProjectType,
            description:
              "Created from unified URL launch scanner. Only actually assessed modules were scored.",
          },
          { headers }
        );

        projectId = projectResponse.project.id;
        setSelectedProjectId(projectId);
        setProjectMode("existing");
      }

      const criticalHigh =
        result.priority_actions?.filter(
          (item) => item.severity === "critical" || item.severity === "high"
        ).length || 0;

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
          findings_count: result.module_cards.reduce(
            (sum, card) => sum + (card.findings_count || 0),
            0
          ),
          critical_high_count: criticalHigh,
          status: "saved_from_unified_url_scanner",
          payload: result,
        },
        { headers }
      );

      setSaveMessage(
        projectMode === "existing"
          ? "Scan saved under the selected project. It will now appear in History with date/time."
          : "Scan saved to dashboard and a new project was created. It will now appear in History."
      );
      await loadWorkspaceQuickData();
    } catch (err) {
      setError(readableClientError(err));
    } finally {
      setSaveLoading(false);
    }
  }

  async function exportCurrentReport(format: "pdf" | "html" | "markdown" | "json") {
    if (!result) return;

    setExportStatus(`Preparing ${format.toUpperCase()} export from this scan result...`);
    setError(null);

    try {
      const report = buildInlineReportFromResult(result);
      const baseName = String(report.report_id || "web3guard-launch-report");

      if (format === "pdf") {
        const blob = await postBlob("/report/export/pdf", { report }, "application/pdf");
        downloadBlob(blob, `${baseName}.pdf`);
      } else if (format === "html") {
        const blob = await postBlob("/report/export/html", { report }, "text/html");
        downloadBlob(blob, `${baseName}.html`);
      } else if (format === "markdown") {
        const blob = await postBlob("/report/export/markdown", { report }, "text/markdown");
        downloadBlob(blob, `${baseName}.md`);
      } else {
        const blob = await postBlob("/report/export/json", { report }, "application/json");
        downloadBlob(blob, `${baseName}.json`);
      }

      setExportStatus(`${format.toUpperCase()} downloaded from the current real scan result. Missing modules remain Not assessed.`);
    } catch (err) {
      setExportStatus(null);
      setError(readableClientError(err));
    }
  }

  function copyCodeToClipboard() {
    void navigator.clipboard.writeText(solidityCode || "");
  }

  const cards = result?.module_cards ? sortModuleCards(result.module_cards) : [];
  const splitCards = result ? scoreSplitCards(buildScoreSplit(result)) : [];
  const requiredInputs = result?.module_cards.flatMap((card) =>
    (card.required_input || []).map((item) => ({ label: card.label, item }))
  ) || [];

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#05070d,#0f172a_38%,#f8fafc_38%)] text-slate-950">
      {fieldPrompt ? (
        <div className="fixed right-4 top-24 z-50 w-[calc(100%-2rem)] max-w-md rounded-2xl border border-red-200 bg-white p-4 text-sm font-semibold text-red-700 shadow-xl">
          <div className="flex items-start justify-between gap-3">
            <span>{fieldPrompt}</span>
            <button type="button" className="text-red-400 transition hover:text-red-700" onClick={() => setFieldPrompt(null)}>×</button>
          </div>
        </div>
      ) : null}

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-3xl">
              <div className="inline-flex rounded-full border border-green-200 bg-green-50 px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] text-green-700">
                Real-only URL scanner
              </div>
              <h1 className="mt-4 text-3xl font-black tracking-tight text-slate-950 sm:text-5xl">Scan, fix, export</h1>
              <p className="mt-3 text-sm leading-6 text-slate-600 sm:text-base">
                Select an old project or create a new one, run a passive scan, view real bugs with fix hints, and export PDF/HTML/Markdown/JSON on the same page.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setCodeEditorOpen((value) => !value)}
                className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-900 transition hover:border-yellow-400 hover:bg-yellow-50"
              >
                {codeEditorOpen ? "Close editor" : "Code editor"}
              </button>
              <button
                type="button"
                onClick={() => void loadWorkspaceQuickData()}
                disabled={!isLoggedIn || historyLoading}
                className="rounded-full border border-green-200 bg-green-50 px-4 py-2 text-sm font-bold text-green-700 transition hover:bg-green-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {historyLoading ? "Refreshing..." : "Refresh history"}
              </button>
              {!authLoading && !isLoggedIn ? (
                <Link href="/auth/login" className="rounded-full border border-red-200 bg-red-50 px-4 py-2 text-sm font-bold text-red-700 transition hover:bg-red-100">
                  Login required
                </Link>
              ) : null}
            </div>
          </div>

          <div className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="font-black text-slate-950">Evidence only</p>
              <p className="mt-1 text-xs leading-5 text-slate-600">Missing modules stay Not assessed, never fake-scored.</p>
            </div>
            <div className="rounded-2xl border border-yellow-200 bg-yellow-50 p-4">
              <p className="font-black text-yellow-900">Passive checks</p>
              <p className="mt-1 text-xs leading-5 text-yellow-800">No exploit automation, wallet signing, or secrets collection.</p>
            </div>
            <div className="rounded-2xl border border-red-200 bg-red-50 p-4">
              <p className="font-black text-red-800">Not a certified audit</p>
              <p className="mt-1 text-xs leading-5 text-red-700">Use it for launch readiness and pre-audit cleanup.</p>
            </div>
          </div>
        </section>

        {codeEditorOpen ? (
          <section className="mt-5 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.18em] text-yellow-700">Code editor</p>
                <h2 className="mt-1 text-2xl font-black text-slate-950">Paste Solidity source</h2>
                <p className="mt-1 text-sm text-slate-600">This editor does not execute code. It only sends source to the passive rule-based scanner.</p>
              </div>
              <button
                type="button"
                onClick={copyCodeToClipboard}
                className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-900 transition hover:bg-slate-50"
              >
                Copy code
              </button>
            </div>
            <textarea
              className="mt-4 min-h-[320px] w-full rounded-2xl border border-slate-300 bg-slate-950 p-4 font-mono text-xs leading-5 text-slate-100 outline-none placeholder:text-slate-500 focus:border-yellow-400 focus:ring-4 focus:ring-yellow-100"
              value={solidityCode}
              onChange={(event) => setSolidityCode(event.target.value)}
              placeholder="Paste Solidity source here for real rule-based scanning."
            />
          </section>
        ) : null}

        <section className="mt-5 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">Setup</p>
              <h2 className="mt-1 text-2xl font-black text-slate-950">Project details</h2>
              <p className="mt-2 text-sm text-slate-600">Fields marked <span className="font-black text-red-600">*</span> are required.</p>
            </div>
            {selectedHistory ? (
              <div className="rounded-2xl border border-yellow-200 bg-yellow-50 px-4 py-3 text-xs font-bold text-yellow-900">
                Last selected: {formatDateTime(selectedHistory.created_at)}
              </div>
            ) : null}
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-3">
            <label className="block text-sm font-bold text-slate-800">
              Scan history
              <select
                className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition focus:border-black focus:ring-4 focus:ring-slate-100"
                value={selectedHistoryId}
                onChange={(event) => applyHistory(event.target.value)}
                disabled={!isLoggedIn || historyLoading}
              >
                <option value="">Select previous saved scan</option>
                {scanHistory.map((scan) => (
                  <option key={scan.id} value={scan.id}>
                    {scan.project_name || getHistoryWebsite(scan)} · {formatDateTime(scan.created_at)}
                  </option>
                ))}
              </select>
              <span className="mt-1 block text-xs font-medium text-slate-500">Reuse old URL/result with last scan date and time.</span>
            </label>

            <label className="block text-sm font-bold text-slate-800">
              Project mode
              <select
                className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition focus:border-black focus:ring-4 focus:ring-slate-100"
                value={projectMode}
                onChange={(event) => {
                  const value = event.target.value as ProjectMode;
                  if (value === "new") startNewProject();
                  else setProjectMode("existing");
                }}
              >
                <option value="new">Create new project</option>
                <option value="existing">Use existing project</option>
              </select>
            </label>

            <label className="block text-sm font-bold text-slate-800">
              Existing project {projectMode === "existing" ? <span className="text-red-600">*</span> : null}
              <select
                className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition focus:border-black focus:ring-4 focus:ring-slate-100 disabled:bg-slate-100 disabled:text-slate-400"
                value={selectedProjectId}
                onChange={(event) => applyProject(event.target.value)}
                disabled={projectMode !== "existing" || !isLoggedIn || !projects.length}
              >
                <option value="">Select project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name} · {formatDateTime(project.updated_at || project.created_at)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {historyError ? (
            <p className="mt-4 rounded-2xl border border-yellow-200 bg-yellow-50 p-3 text-sm font-semibold text-yellow-900">
              Could not load history/projects: {historyError}
            </p>
          ) : null}

          <div className="mt-5 grid gap-4 lg:grid-cols-12">
            <label className="block text-sm font-bold text-slate-800 lg:col-span-5">
              Website / dApp URL <span className="text-red-600">*</span>
              <input
                className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-black focus:ring-4 focus:ring-slate-100"
                value={websiteUrl}
                onChange={(event) => setWebsiteUrl(event.target.value)}
                placeholder="https://yourproject.com"
              />
            </label>

            <label className="block text-sm font-bold text-slate-800 lg:col-span-3">
              Project name <span className="text-red-600">*</span>
              <input
                className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-black focus:ring-4 focus:ring-slate-100"
                value={projectName}
                onChange={(event) => setProjectName(event.target.value)}
                placeholder="My Web3 Project"
              />
            </label>

            <label className="block text-sm font-bold text-slate-800 lg:col-span-4">
              Project type <span className="text-red-600">*</span>
              <select
                className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition focus:border-black focus:ring-4 focus:ring-slate-100"
                value={projectType}
                onChange={(event) => setProjectType(event.target.value)}
              >
                {projectTypeOptions.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>

            {projectType === "Other" ? (
              <label className="block text-sm font-bold text-slate-800 lg:col-span-3">
                Custom project type <span className="text-red-600">*</span>
                <input
                  className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-black focus:ring-4 focus:ring-slate-100"
                  value={customProjectType}
                  onChange={(event) => setCustomProjectType(event.target.value)}
                  placeholder="Example: RWA, DePIN"
                />
              </label>
            ) : null}

            <label className="block text-sm font-bold text-slate-800 lg:col-span-3">
              Chain
              <select
                className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition focus:border-black focus:ring-4 focus:ring-slate-100"
                value={chain}
                onChange={(event) => setChain(event.target.value)}
              >
                {chainOptions.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>

            {chain === "Other" ? (
              <label className="block text-sm font-bold text-slate-800 lg:col-span-3">
                Custom chain
                <input
                  className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-black focus:ring-4 focus:ring-slate-100"
                  value={customChain}
                  onChange={(event) => setCustomChain(event.target.value)}
                  placeholder="Example: Sui, Aptos"
                />
              </label>
            ) : null}

            <label className="block text-sm font-bold text-slate-800 lg:col-span-3">
              Contract address optional
              <input
                className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-black focus:ring-4 focus:ring-slate-100"
                value={contractAddress}
                onChange={(event) => setContractAddress(event.target.value)}
                placeholder="0x..."
              />
            </label>

            <label className="block text-sm font-bold text-slate-800 lg:col-span-3">
              API base URL optional
              <input
                className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-black focus:ring-4 focus:ring-slate-100"
                value={apiBaseUrl}
                onChange={(event) => setApiBaseUrl(event.target.value)}
                placeholder="https://api.yourproject.com"
              />
            </label>

            <label className="block text-sm font-bold text-slate-800 lg:col-span-3">
              GitHub repo optional
              <input
                className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-black focus:ring-4 focus:ring-slate-100"
                value={githubRepoUrl}
                onChange={(event) => setGithubRepoUrl(event.target.value)}
                placeholder="https://github.com/team/project"
              />
            </label>
          </div>

          <div className="mt-5 grid gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700 md:grid-cols-2">
            <label className="flex gap-3 font-medium">
              <input
                type="checkbox"
                checked={authorized}
                onChange={(event) => setAuthorized(event.target.checked)}
              />
              <span>I own this project or have authorization to run passive checks. <span className="font-black text-red-600">*</span></span>
            </label>

            <label className="flex gap-3 font-medium">
              <input
                type="checkbox"
                checked={realOnly}
                onChange={(event) => setRealOnly(event.target.checked)}
              />
              <span>I understand missing modules will be marked Not assessed. <span className="font-black text-red-600">*</span></span>
            </label>
          </div>

          {missingRequiredFields.length ? (
            <p className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-700">
              Required pending: {missingRequiredFields.join(", ")}
            </p>
          ) : null}

          {loading ? (
            <div className="mt-5 rounded-2xl border border-green-200 bg-green-50 p-4">
              <div className="flex items-center justify-between gap-4">
                <p className="text-sm font-black text-green-800">{currentStage}</p>
                <p className="text-sm font-bold text-green-700">{progress}%</p>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-green-100">
                <div className="h-full rounded-full bg-green-600 transition-all duration-500" style={{ width: `${progress}%` }} />
              </div>
            </div>
          ) : null}

          {error ? (
            <p className="mt-4 whitespace-pre-wrap rounded-2xl border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">
              {error}
            </p>
          ) : null}

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <button
              className="w3g-action-dark rounded-2xl border border-slate-950 bg-slate-950 px-6 py-4 text-sm font-black text-white shadow-sm transition hover:bg-slate-800 disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-500 disabled:shadow-none disabled:opacity-100"
              onClick={runScan}
              disabled={!canRunScan}
            >
              {loading ? "Scanning..." : missingRequiredFields.length ? "Fill required fields" : "Run URL Scan"}
            </button>
            <p className="text-xs leading-5 text-slate-500">Scan will not run until every required <span className="font-black text-red-600">*</span> field is completed.</p>
          </div>
        </section>

        <section className="mt-6 space-y-5">
          {!result ? (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-center shadow-sm">
              <p className="text-sm font-black uppercase tracking-[0.18em] text-slate-400">No result yet</p>
              <h2 className="mt-3 text-2xl font-black text-slate-950">Run a scan or select history</h2>
              <p className="mx-auto mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                Results, bug hints, missing evidence, and export buttons will appear here directly after the scan.
              </p>
            </div>
          ) : (
            <>
              <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                <div className="grid gap-5 lg:grid-cols-[240px_1fr]">
                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                    <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Assessed score</p>
                    <p className={`mt-2 text-6xl font-black ${scoreTone(result.available_score)}`}>{result.available_score ?? "N/A"}</p>
                    <p className="mt-2 text-sm font-bold text-slate-700">{result.risk_label || "Not assessed"}</p>
                    <div className="mt-4 grid gap-2 text-xs font-bold">
                      <span className="rounded-full border border-green-200 bg-green-50 px-3 py-2 text-green-700">{result.live_module_count} live/limited module(s)</span>
                      <span className="rounded-full border border-yellow-200 bg-yellow-50 px-3 py-2 text-yellow-800">{result.priority_actions?.length || 0} action(s)</span>
                    </div>
                  </div>

                  <div>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h2 className="text-2xl font-black text-slate-950">Scan report</h2>
                        <p className="mt-2 text-sm leading-6 text-slate-600">Export is generated from this real scan result. Missing modules remain Not assessed.</p>
                      </div>
                      <button type="button" disabled={saveLoading} onClick={saveUnifiedScanToDashboard} className="rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-black text-slate-900 transition hover:bg-slate-50 disabled:opacity-50">
                        {saveLoading ? "Saving..." : projectMode === "existing" && selectedProjectId ? "Save under project" : "Save + create project"}
                      </button>
                    </div>

                    <div className="mt-5 flex flex-wrap gap-3">
                      <button type="button" className="w3g-action-danger rounded-full bg-red-600 px-5 py-3 text-sm font-black text-white transition hover:bg-red-700" onClick={() => exportCurrentReport("pdf")}>Download PDF</button>
                      <button type="button" className="rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-black text-slate-900 transition hover:bg-slate-50" onClick={() => exportCurrentReport("html")}>HTML</button>
                      <button type="button" className="rounded-full border border-green-200 bg-green-50 px-5 py-3 text-sm font-black text-green-700 transition hover:bg-green-100" onClick={() => exportCurrentReport("markdown")}>Markdown</button>
                      <button type="button" className="rounded-full border border-yellow-200 bg-yellow-50 px-5 py-3 text-sm font-black text-yellow-900 transition hover:bg-yellow-100" onClick={() => exportCurrentReport("json")}>JSON</button>
                    </div>

                    {saveMessage ? <p className="mt-4 rounded-2xl border border-green-200 bg-green-50 p-4 text-sm font-semibold text-green-700">{saveMessage}</p> : null}
                    {exportStatus ? <p className="mt-4 rounded-2xl border border-green-200 bg-green-50 p-4 text-sm font-semibold text-green-700">{exportStatus}</p> : null}

                    <div className="mt-4 grid gap-3 md:grid-cols-2">
                      <p className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">{result.realness_rule}</p>
                      <p className="rounded-2xl border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-900">{result.safe_public_summary}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">Split readiness scores</p>
                    <h3 className="mt-2 text-2xl font-black text-slate-950">No misleading full audit score</h3>
                    <p className="mt-2 text-sm leading-6 text-slate-600">Website Surface Score, Contract Rule Score, Launch Evidence Score, and Overall Launch Confidence are separated so missing evidence remains visible.</p>
                  </div>
                  <div className="rounded-2xl border border-yellow-200 bg-yellow-50 px-4 py-3 text-xs font-black text-yellow-900">Pre-audit readiness only</div>
                </div>
                <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  {splitCards.map((item) => (
                    <div key={item.key} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p className="text-xs font-black uppercase tracking-wide text-slate-500">{item.label}</p>
                      <p className={`mt-2 text-3xl font-black ${scoreTone(item.score)}`}>{typeof item.score === "number" ? item.score : "Not assessed"}</p>
                      <p className="mt-2 text-sm font-bold text-slate-800">{item.status}</p>
                      <p className="mt-2 text-xs leading-5 text-slate-600">{item.source}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {cards.map((card) => (
                  <div key={card.module} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <h3 className="font-black text-slate-950">{card.label}</h3>
                      <span className={`rounded-full border px-3 py-1 text-xs font-black ${statusClass(card.status)}`}>{card.status}</span>
                    </div>
                    <p className="mt-3 text-sm text-slate-600">Score: <span className="font-black text-slate-950">{card.score ?? "Not assessed"}</span></p>

                    {!!card.evidence?.length ? (
                      <div className="mt-4">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-500">Evidence</p>
                        <ul className="mt-2 space-y-1 text-xs text-slate-600">
                          {card.evidence.slice(0, 4).map((item, index) => <li key={`${card.module}-evidence-${index}`}>• {item}</li>)}
                        </ul>
                      </div>
                    ) : null}

                    {!!card.required_input?.length ? (
                      <div className="mt-4 rounded-2xl border border-yellow-200 bg-yellow-50 p-3">
                        <p className="text-xs font-black uppercase tracking-wide text-yellow-900">Needed for real score</p>
                        <ul className="mt-2 space-y-1 text-xs text-yellow-900/90">
                          {card.required_input.map((item, index) => <li key={`${card.module}-required-${index}`}>• {item}</li>)}
                        </ul>
                      </div>
                    ) : null}

                    <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3">
                      <p className="text-xs font-black uppercase tracking-wide text-slate-500">Fix direction</p>
                      <p className="mt-2 text-xs leading-5 text-slate-600">{moduleFixGuide(card)}</p>
                    </div>
                  </div>
                ))}
              </div>

              {!!result.priority_actions?.length ? (
                <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                  <h3 className="text-2xl font-black text-slate-950">Bugs / findings with fix guidance</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">Real assessed findings only. Each item includes where to fix, why it matters, how to fix, and how to verify.</p>
                  <div className="mt-4 space-y-3">
                    {result.priority_actions.slice(0, 12).map((item) => {
                      const guide = getActionFixGuide(item.title, item.module);
                      return (
                        <div key={`${item.step}-${item.title}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                          <div className="flex flex-wrap items-center gap-3">
                            <SeverityBadge severity={item.severity} />
                            <p className="font-black text-slate-950">{item.title}</p>
                          </div>
                          <p className="mt-2 text-sm text-slate-700">{item.recommended_action}</p>
                          <div className="mt-4 grid gap-3 text-xs sm:grid-cols-2 lg:grid-cols-4">
                            <div className="rounded-xl border border-slate-200 bg-white p-3"><p className="font-black text-slate-500">Where to fix</p><p className="mt-1 text-slate-800">{guide.file}</p></div>
                            <div className="rounded-xl border border-slate-200 bg-white p-3"><p className="font-black text-slate-500">Why it matters</p><p className="mt-1 text-slate-800">{guide.why}</p></div>
                            <div className="rounded-xl border border-slate-200 bg-white p-3"><p className="font-black text-slate-500">How to fix</p><p className="mt-1 text-slate-800">{guide.fix}</p></div>
                            <div className="rounded-xl border border-slate-200 bg-white p-3"><p className="font-black text-slate-500">Verify</p><p className="mt-1 text-slate-800">{guide.verify}</p></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : null}

              <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-black uppercase tracking-[0.18em] text-yellow-700">Evidence required</p>
                    <h3 className="mt-2 text-2xl font-black text-slate-950">What to add for a deeper report</h3>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-black text-slate-700">{requiredInputs.length} missing evidence item(s)</div>
                </div>
                {requiredInputs.length ? (
                  <ul className="mt-5 grid gap-2 text-sm text-slate-700 md:grid-cols-2">
                    {requiredInputs.map((input, index) => (
                      <li key={`required-${index}`} className="rounded-2xl border border-yellow-200 bg-yellow-50 p-3 text-yellow-900"><strong>{input.label}:</strong> {input.item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-5 rounded-2xl border border-green-200 bg-green-50 p-4 text-sm font-semibold text-green-700">No missing evidence was listed by the current scan result.</p>
                )}
              </div>

              {!!result.blocked_claims?.length ? (
                <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                  <h3 className="text-2xl font-black text-slate-950">Blocked fake claims</h3>
                  <ul className="mt-4 space-y-2 text-sm text-slate-700">
                    {(result.blocked_claims || []).map((claim, index) => <li key={`blocked-claim-${index}`}>• {claim}</li>)}
                  </ul>
                </div>
              ) : null}
            </>
          )}
        </section>
      </div>
    </main>
  );
}
