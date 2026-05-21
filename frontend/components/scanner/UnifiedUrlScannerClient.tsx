
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
  if (value.includes("not assessed") || value.includes("not installed") || value.includes("not configured") || value.includes("key")) return "badge";
  if (value.includes("manual") || value.includes("input") || value.includes("needed")) return "badge-amber";
  if (value.includes("live") || value.includes("assessed") || value.includes("complete")) return "badge-green";
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


type SimpleFindingGuide = {
  label: string;
  badgeClass: string;
  proofLabel: string;
  launchDecision: string;
  owner: string;
  effort: string;
  simpleProblem: string;
  simpleRisk: string;
  fixNow: string;
  verify: string;
  whyNotExploitClaim: string;
};

type FounderActionItem = {
  title: string;
  module: string;
  severity: string;
  type: string;
  badgeClass: string;
  plainProblem: string;
  plainRisk: string;
  fixNow: string;
  owner: string;
  effort: string;
  verify: string;
  launchDecision: string;
};

type GapClosurePlan = {
  staticAnalysis: {
    status: string;
    reason: string;
    safePaths: string[];
    tools: StaticToolUiRow[];
  };
  humanReview: {
    status: string;
    reason: string;
    safePaths: string[];
    needed: boolean;
  };
};

function simpleOwner(module?: string | null, title?: string | null) {
  const text = `${module || ""} ${title || ""}`.toLowerCase();
  if (text.includes("contract") || text.includes("solidity") || text.includes("slither") || text.includes("aderyn")) return "Smart contract developer / auditor";
  if (text.includes("api") || text.includes("cors") || text.includes("webhook") || text.includes("rate limit") || text.includes("bola") || text.includes("idor")) return "Backend developer";
  if (text.includes("github") || text.includes("secret") || text.includes("ci") || text.includes("workflow") || text.includes("dependency")) return "DevOps / repository owner";
  if (text.includes("wallet") || text.includes("signature") || text.includes("approval")) return "dApp frontend + wallet-flow developer";
  if (text.includes("csp") || text.includes("header") || text.includes("cookie") || text.includes("hsts") || text.includes("iframe")) return "Frontend / hosting developer";
  return "Project technical owner";
}

function simpleEffort(severity?: string | null, title?: string | null) {
  const text = String(title || "").toLowerCase();
  if (text.includes("csp") || text.includes("header") || text.includes("cookie") || text.includes("hsts")) return "Usually 30–90 minutes";
  if (text.includes("rate limit") || text.includes("webhook") || text.includes("auth") || text.includes("bola") || text.includes("idor")) return "Usually 2–6 hours";
  if (text.includes("contract") || text.includes("oracle") || text.includes("upgrade") || text.includes("signature")) return "Usually 1–3 days + reviewer check";
  if (severity === "critical" || severity === "high") return "Same day priority";
  if (severity === "medium") return "Before public beta";
  return "When polishing launch readiness";
}

function simpleProblemForTitle(title: string, module?: string | null) {
  const text = `${title} ${module || ""}`.toLowerCase();
  if (text.includes("content-security-policy") || text.includes("csp")) return "Your site is missing or has a weak browser safety rule that controls which scripts/assets may run.";
  if (text.includes("hsts")) return "Your site is not clearly telling browsers to always use HTTPS for future visits.";
  if (text.includes("cookie")) return "A cookie setting may be missing security flags, so browser-side session protection is weaker.";
  if (text.includes("cors")) return "Your API/browser access policy may be too open or not proven safe.";
  if (text.includes("rate limit")) return "A public route may allow too many requests without throttling.";
  if (text.includes("webhook")) return "A webhook/payment/integration event may not be proven signature-verified.";
  if (text.includes("bola") || text.includes("idor")) return "The scan needs proof that users cannot access another user’s private object/report/order by changing an ID.";
  if (text.includes("docs exposure") || text.includes("api docs") || text.includes("openapi")) return "Developer/API documentation may be exposed publicly on production.";
  if (text.includes("secret")) return "The repo or public files may contain paths or patterns that need a secret-leak review.";
  if (text.includes("dependency") || text.includes("osv")) return "A dependency/version risk was found or needs a real advisory check.";
  if (text.includes("slither") || text.includes("semgrep") || text.includes("aderyn")) return "A static-analysis tool did not run or produced a finding that needs developer review.";
  if (text.includes("contract") || text.includes("solidity")) return "Smart-contract code evidence is missing or a contract rule needs review.";
  if (text.includes("wallet") || text.includes("signature") || text.includes("approval")) return "The wallet/signing flow needs clearer proof that users are not approving unsafe actions.";
  return "The scanner found a launch-readiness issue or missing proof that should be checked before launch.";
}

function simpleRiskForTitle(title: string, severity?: string | null) {
  const text = String(title || "").toLowerCase();
  if (text.includes("content-security-policy") || text.includes("csp")) return "If an attacker finds a script-injection path, weak CSP can make account takeover, phishing, or wallet-drain pages easier.";
  if (text.includes("rate limit")) return "Attackers or bots can overload a route, abuse free scans, spam auth/payment flows, or increase infrastructure cost.";
  if (text.includes("webhook")) return "Fake webhook events can mark payments, reports, or trust states as valid if signature checks are missing.";
  if (text.includes("bola") || text.includes("idor")) return "This is a serious user-data risk: one user could potentially view or modify another user’s private data if authorization is weak.";
  if (text.includes("secret")) return "Leaked keys can give attackers access to APIs, cloud services, wallets, or private infrastructure.";
  if (text.includes("contract") || text.includes("solidity")) return "Contract bugs can directly affect funds, ownership, upgrades, or protocol logic.";
  if (text.includes("wallet") || text.includes("signature") || text.includes("approval")) return "Users may approve the wrong transaction, wrong chain, or unlimited token access if the flow is unclear.";
  if (severity === "critical" || severity === "high") return "This can block a safe public launch until it is fixed or reviewed.";
  if (severity === "medium") return "This may not be an active exploit yet, but it can become a real security problem after public traffic starts.";
  return "This is mostly a hardening or evidence gap, but fixing it improves trust and launch quality.";
}

function findingTypeLabel(action: UnifiedUrlScanResponse["priority_actions"][number]) {
  const text = `${action.title || ""} ${action.recommended_action || ""} ${action.module || ""}`.toLowerCase();
  if (text.includes("not assessed") || text.includes("missing evidence") || text.includes("provide") || text.includes("add evidence")) {
    return { label: "Evidence gap", badgeClass: "badge-amber", proofLabel: "Not enough proof to score this area" };
  }
  if (action.severity === "critical" || action.severity === "high") {
    return { label: "Possible vulnerability", badgeClass: "badge-red", proofLabel: "Scanner-observed risk; needs human verification" };
  }
  if (action.severity === "medium") {
    return { label: "Security issue", badgeClass: "badge-amber", proofLabel: "Observed hardening or configuration risk" };
  }
  return { label: "Hardening hint", badgeClass: "badge-cyan", proofLabel: "Improve before launch; not a confirmed exploit" };
}

function simpleLaunchDecision(severity?: string | null) {
  if (severity === "critical") return "Do not launch until fixed or reviewed";
  if (severity === "high") return "Fix before public launch";
  if (severity === "medium") return "Fix before beta or accept risk with proof";
  if (severity === "low") return "Good to fix during launch polish";
  return "Monitor / add evidence";
}

function simpleGuideForAction(action: UnifiedUrlScanResponse["priority_actions"][number]): SimpleFindingGuide {
  const type = findingTypeLabel(action);
  const technical = fixGuideForFinding(action.title, action.module);
  return {
    label: type.label,
    badgeClass: type.badgeClass,
    proofLabel: type.proofLabel,
    launchDecision: simpleLaunchDecision(action.severity),
    owner: simpleOwner(action.module, action.title),
    effort: simpleEffort(action.severity, action.title),
    simpleProblem: simpleProblemForTitle(action.title, action.module),
    simpleRisk: action.business_impact || simpleRiskForTitle(action.title, action.severity),
    fixNow: technical.how_to_fix,
    verify: technical.verify,
    whyNotExploitClaim: "This is scanner evidence, not proof that someone exploited you. Treat it as a fix/review task before making strong security claims.",
  };
}

function BeginnerBugSummaryCard({ result }: { result: UnifiedUrlScanResponse }) {
  const actions = result.priority_actions || [];
  const criticalHigh = actions.filter((item) => item.severity === "critical" || item.severity === "high").length;
  const medium = actions.filter((item) => item.severity === "medium").length;
  const notAssessed = result.module_cards.filter((card) => !isModuleAssessed(card)).length;
  const assessed = result.module_cards.filter((card) => isModuleAssessed(card)).length;
  const decision = criticalHigh > 0
    ? "Fix critical/high items before public launch."
    : medium > 0
      ? "No critical/high item in the priority list, but fix medium items before beta."
      : "No major priority blocker found in assessed modules.";

  return (
    <CardShell className="border-cyan/20 bg-cyan/[0.035]">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="section-label">Beginner view</p>
          <h2 className="mt-2 text-2xl font-black text-white">Simple bug explanation</h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-300">
            Read this like a launch checklist: a bug/security issue is something to fix, a vulnerability risk is something that can become dangerous, and Not Assessed means the scanner did not get enough evidence to judge that area.
          </p>
        </div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/25 p-4 text-sm leading-6 text-slate-300 lg:max-w-sm">
          <p className="font-black text-white">Plain decision</p>
          <p className="mt-2">{decision}</p>
          <p className="mt-2 text-xs text-slate-500">This is still not a certified audit or guarantee.</p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-red-400/15 bg-red-500/10 p-4">
          <p className="mono text-[10px] uppercase tracking-[0.16em] text-red-100/70">Fix first</p>
          <p className="mt-2 text-2xl font-black text-white">{criticalHigh}</p>
          <p className="mt-1 text-xs leading-5 text-red-100/80">Critical/high possible vulnerabilities</p>
        </div>
        <div className="rounded-2xl border border-amber-300/15 bg-amber-300/10 p-4">
          <p className="mono text-[10px] uppercase tracking-[0.16em] text-amber-100/70">Fix next</p>
          <p className="mt-2 text-2xl font-black text-white">{medium}</p>
          <p className="mt-1 text-xs leading-5 text-amber-100/80">Medium security or hardening issues</p>
        </div>
        <div className="rounded-2xl border border-emerald-400/15 bg-emerald-400/10 p-4">
          <p className="mono text-[10px] uppercase tracking-[0.16em] text-emerald-100/70">Checked</p>
          <p className="mt-2 text-2xl font-black text-white">{assessed}/{result.module_cards.length || 0}</p>
          <p className="mt-1 text-xs leading-5 text-emerald-100/80">Modules with real evidence</p>
        </div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/25 p-4">
          <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Unknown</p>
          <p className="mt-2 text-2xl font-black text-white">{notAssessed}</p>
          <p className="mt-1 text-xs leading-5 text-slate-400">Modules still Not Assessed</p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
          <p className="text-sm font-black text-white">Bug / issue</p>
          <p className="mt-2 text-xs leading-5 text-slate-400">A real signal from the scan that should be fixed or reviewed.</p>
        </div>
        <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
          <p className="text-sm font-black text-white">Vulnerability risk</p>
          <p className="mt-2 text-xs leading-5 text-slate-400">A weakness that could be abused if an attacker finds the right path. It needs priority review.</p>
        </div>
        <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
          <p className="text-sm font-black text-white">Not Assessed</p>
          <p className="mt-2 text-xs leading-5 text-slate-400">No proof was provided, so Web3Guard does not call it safe or unsafe.</p>
        </div>
      </div>
    </CardShell>
  );
}


type StaticToolUiRow = {
  id: string;
  label: string;
  state: string;
  status: string;
  installed: boolean | null;
  enabledByEnv: boolean | null;
  willRun: boolean | null;
  realFindings: number;
  evidenceSource: string;
  detail: string;
  action: string;
};

function boolOrNull(value: unknown) {
  return typeof value === "boolean" ? value : null;
}

function yesNo(value: boolean | null) {
  if (value === null) return "unknown";
  return value ? "yes" : "no";
}

function toolLabel(tool: string) {
  const clean = tool.replace(/_artifact$/i, "").toLowerCase();
  if (clean === "slither") return "Slither";
  if (clean === "semgrep") return "Semgrep";
  if (clean === "aderyn") return "Aderyn";
  return tool.replace(/_/g, " ");
}

function toolAction(state: string, label: string, evidenceSource: string) {
  const value = state.toLowerCase();
  if (evidenceSource.includes("artifact")) return `Review the parsed ${label} artifact findings and keep the raw JSON attached for reviewer verification.`;
  if (value.includes("not assessed")) return `Add Solidity source or a verified contract/source artifact, then rerun. URL-only scans do not execute ${label}.`;
  if (value.includes("not installed")) return `Install ${label} in the isolated tools environment, or paste a valid ${label} JSON artifact in Expert Evidence.`;
  if (value.includes("assessed")) return `Review real ${label} output and fix confirmed findings before public launch.`;
  if (value.includes("provider not configured") || value.includes("not configured")) return `Enable ${label} only in a safe tools/worker environment, or paste a valid ${label} JSON artifact.`;
  if (value.includes("manual")) return `Check backend tool logs for ${label}; if the tool cannot run safely, attach manual reviewer notes or a valid artifact.`;
  return `Add Solidity source or a verified contract/source artifact, then rerun. URL-only scans do not execute ${label}.`;
}

function buildStaticToolRows(result: UnifiedUrlScanResponse | null): StaticToolUiRow[] {
  if (!result) return [];
  const staticSummary = plainRecord(result.surface_hints?.static_analysis);
  const staticCard = result.module_cards.find((card) => card.module === "static_analysis");
  const rawTools = unknownArray(staticSummary.tools).filter(isPlainRecord);
  const expected = ["slither", "semgrep", "aderyn"];
  const rows: StaticToolUiRow[] = [];

  expected.forEach((id) => {
    const tool = rawTools.find((item) => String(item.tool || "").toLowerCase() === id);
    const label = toolLabel(id);
    const state = tool ? unknownString(tool.state, "Not Assessed") : staticCard?.status || "Not Assessed";
    const status = tool ? unknownString(tool.status, "not_run") : "not_reported";
    const installed = tool ? boolOrNull(tool.installed) : null;
    const enabledByEnv = tool ? boolOrNull(tool.enabled_by_env) : null;
    const willRun = tool ? boolOrNull(tool.will_run) : null;
    const realFindings = tool ? unknownNumber(tool.real_findings) ?? 0 : 0;
    const evidenceSource = tool ? unknownString(tool.evidence_source, "backend_tool_status") : "not_reported";
    rows.push({
      id,
      label,
      state,
      status,
      installed,
      enabledByEnv,
      willRun,
      realFindings,
      evidenceSource,
      detail: `installed: ${yesNo(installed)} · enabled: ${yesNo(enabledByEnv)} · will run: ${yesNo(willRun)} · findings: ${realFindings}`,
      action: toolAction(state, label, evidenceSource),
    });
  });

  rawTools
    .filter((item) => String(item.tool || "").toLowerCase().endsWith("_artifact"))
    .forEach((tool) => {
      const id = String(tool.tool || "artifact");
      const label = `${toolLabel(id)} artifact`;
      const state = unknownString(tool.state, "User Artifact");
      const status = unknownString(tool.status, "artifact_status");
      const realFindings = unknownNumber(tool.real_findings) ?? 0;
      const evidenceSource = unknownString(tool.evidence_source, "user_supplied_json_artifact");
      rows.push({
        id,
        label,
        state,
        status,
        installed: false,
        enabledByEnv: true,
        willRun: false,
        realFindings,
        evidenceSource,
        detail: `user artifact parsed · findings: ${realFindings}`,
        action: toolAction(state, label, evidenceSource),
      });
    });

  return rows;
}

function staticToolSummary(result: UnifiedUrlScanResponse | null) {
  if (!result) return null;
  const staticSummary = plainRecord(result.surface_hints?.static_analysis);
  const verification = plainRecord(staticSummary.tool_verification);
  const staticCard = result.module_cards.find((card) => card.module === "static_analysis");
  return {
    state: unknownString(staticSummary.state, staticCard?.status || "Not Assessed"),
    score: typeof staticSummary.score === "number" ? staticSummary.score : staticCard?.score ?? null,
    riskLabel: unknownString(staticSummary.risk_label, staticCard?.risk_label || "Not Assessed"),
    completedCount: unknownNumber(verification.completed_count) ?? 0,
    ranCount: unknownNumber(verification.ran_count) ?? 0,
    failedCount: unknownNumber(verification.failed_count) ?? 0,
    realFindingsCount: unknownNumber(verification.real_findings_count) ?? staticCard?.findings_count ?? 0,
    evidenceRule: unknownString(verification.evidence_rule, "Only real executed tool output or valid supplied artifacts count. Missing tools are not fake vulnerabilities."),
    note: unknownString(staticSummary.real_only_note, "URL-only scans do not run Slither/Semgrep/Aderyn. Add source/artifacts for static-analysis evidence."),
  };
}

function buildFounderActionPlan(result: UnifiedUrlScanResponse, limit = 5): FounderActionItem[] {
  const actions = [...(result.priority_actions || [])].sort((a, b) => severityRank(a.severity) - severityRank(b.severity));
  const mapped = actions.map((action) => {
    const simple = simpleGuideForAction(action);
    return {
      title: action.title || "Launch-readiness issue",
      module: action.module_label || action.module || "general",
      severity: action.severity || "info",
      type: simple.label,
      badgeClass: simple.badgeClass,
      plainProblem: simple.simpleProblem,
      plainRisk: simple.simpleRisk,
      fixNow: simple.fixNow,
      owner: simple.owner,
      effort: simple.effort,
      verify: simple.verify,
      launchDecision: simple.launchDecision,
    };
  });

  if (mapped.length) return mapped.slice(0, limit);

  const missingCards = result.module_cards.filter((card) => !isModuleAssessed(card));
  return missingCards.slice(0, limit).map((card) => ({
    title: `${card.label} was not assessed`,
    module: card.module,
    severity: "info",
    type: "Missing evidence",
    badgeClass: "badge-amber",
    plainProblem: `${card.label} could not be judged because the scan did not receive the needed proof.`,
    plainRisk: "Unknown areas should not be called safe. Add evidence before making strong launch/security claims.",
    fixNow: moduleFixGuide(card),
    owner: card.module === "contract" || card.module === "static_analysis" ? "Smart contract developer / auditor" : "Project technical owner",
    effort: "Depends on evidence availability",
    verify: "Add the evidence, rerun the scan, and confirm the module is no longer Not Assessed.",
    launchDecision: "Add evidence before strong public claims",
  }));
}

function buildGapClosurePlan(result: UnifiedUrlScanResponse): GapClosurePlan {
  const tools = buildStaticToolRows(result);
  const staticCovered = tools.some((tool) => tool.realFindings > 0 || tool.evidenceSource.includes("artifact") || tool.willRun === true);
  const missingToolCount = tools.filter((tool) => tool.state.toLowerCase().includes("not") || tool.willRun === false || tool.willRun === null).length;
  const reviewSeverityCount = (result.priority_actions || []).filter((item) => ["critical", "high", "medium"].includes(String(item.severity || "").toLowerCase())).length;
  const notAssessedCount = result.module_cards.filter((card) => !isModuleAssessed(card)).length;
  const humanReviewNeeded = reviewSeverityCount > 0 || notAssessedCount > 0;

  return {
    staticAnalysis: {
      status: staticCovered ? "Partly covered with real tool/artifact evidence" : "Gap open: tools are not live by default",
      reason: staticCovered
        ? "At least one static-analysis path has real evidence. Keep raw output attached for reviewer verification."
        : `Slither/Semgrep/Aderyn are not faked. ${missingToolCount || 3} tool path(s) still need pasted JSON artifacts or an isolated worker setup.`,
      safePaths: [
        "Paste real Slither/Semgrep/Aderyn JSON in Expert Evidence.",
        "Use a separate isolated worker service for live execution; do not enable execution in the main backend.",
        "Attach Solidity source or verified contract evidence so static tools have code to analyze.",
      ],
      tools,
    },
    humanReview: {
      status: humanReviewNeeded ? "Manual reviewer recommended" : "Manual reviewer optional",
      reason: humanReviewNeeded
        ? "Scanner output is useful for triage, but critical/high/medium issues and Not Assessed modules need a real human reviewer before strong security wording."
        : "No priority blocker is visible in assessed modules, but a human review still improves trust before public claims.",
      safePaths: [
        "Create a reviewer handoff pack from this report.",
        "Assign a real reviewer/admin in the manual review workflow.",
        "Do not show verified-auditor, certified-audit, or marketplace claims until real reviewers are onboarded and approved.",
      ],
      needed: humanReviewNeeded,
    },
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
  const founderPlan = Array.isArray(report.founder_action_plan) ? (report.founder_action_plan as Array<Record<string, unknown>>) : [];
  const gapClosure = plainRecord(report.gap_closure_plan);
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

  lines.push("", "## Founder action plan");
  if (founderPlan.length) {
    founderPlan.forEach((item, index) => {
      lines.push(
        `${index + 1}. **${String(item.title || "Action item")}**`,
        `   - Simple meaning: ${String(item.plainProblem || "Review this item.")}`,
        `   - Risk: ${String(item.plainRisk || "This may affect launch safety or trust.")}`,
        `   - Fix: ${String(item.fixNow || "Apply the recommended fix.")}`,
        `   - Owner: ${String(item.owner || "Project owner")}`,
        `   - Effort: ${String(item.effort || "Project-specific")}`,
        `   - Verify: ${String(item.verify || "Rerun scan after the fix.")}`,
        `   - Launch decision: ${String(item.launchDecision || "Review before launch")}`
      );
    });
  } else {
    lines.push("No priority action was generated from the assessed modules.");
  }

  lines.push("", "## Gap closure plan");
  const staticGap = plainRecord(gapClosure.staticAnalysis);
  const humanGap = plainRecord(gapClosure.humanReview);
  lines.push(`- **Static tools:** ${String(staticGap.status || "Not Assessed")} — ${String(staticGap.reason || "No static-analysis gap data attached.")}`);
  unknownArray(staticGap.safePaths).forEach((step) => lines.push(`  - ${String(step)}`));
  lines.push(`- **Human reviewer:** ${String(humanGap.status || "Manual Review Required")} — ${String(humanGap.reason || "No human-review gap data attached.")}`);
  unknownArray(humanGap.safePaths).forEach((step) => lines.push(`  - ${String(step)}`));

  lines.push("", "## Findings and fix hints");
  if (findings.length) {
    findings.forEach((finding, index) => {
      const fix = (finding.fix_guidance || {}) as Record<string, unknown>;
      lines.push(
        `${index + 1}. **${String(finding.severity || "info").toUpperCase()} — ${String(finding.title || "Finding")}**`,
        `   - Module: ${String(finding.module || "unknown")}`,
        `   - Recommendation: ${String(finding.recommendation || "Review before launch.")}`,
        `   - Simple meaning: ${String(((finding.beginner_explanation || {}) as Record<string, unknown>).plain_problem || "Review this issue before launch.")}`,
        `   - Risk in plain words: ${String(((finding.beginner_explanation || {}) as Record<string, unknown>).plain_risk || "This may affect launch safety or user trust.")}`,
        `   - Owner: ${String(((finding.beginner_explanation || {}) as Record<string, unknown>).owner || "Project technical owner")}`,
        `   - Effort: ${String(((finding.beginner_explanation || {}) as Record<string, unknown>).effort || "Project-specific")}`,
        `   - Launch decision: ${String(((finding.beginner_explanation || {}) as Record<string, unknown>).launch_decision || "Review before launch")}`,
        `   - Where to fix: ${String(fix.where_to_fix || "Manual review required")}`,
        `   - How to fix: ${String(fix.how_to_fix || "Apply project-specific fix.")}`,
        `   - Verify: ${String(fix.verify || "Re-run scan after the fix.")}`
      );
    });
  } else {
    lines.push("No findings were detected in the assessed modules of this scan payload.");
  }

  const staticToolRows = Array.isArray(report.static_analysis_tool_status) ? (report.static_analysis_tool_status as Array<Record<string, unknown>>) : [];
  const staticSummary = (report.static_analysis_summary || {}) as Record<string, unknown>;

  lines.push("", "## Static-analysis tool status");
  if (staticToolRows.length) {
    lines.push(`State: ${String(staticSummary.state || "Not Assessed")}`);
    staticToolRows.forEach((tool) => {
      lines.push(`- **${String(tool.label || tool.id || "Tool")}**: ${String(tool.state || "Not Assessed")} · ${String(tool.detail || "No detail")}`);
      lines.push(`  - Next action: ${String(tool.action || "Add valid evidence and rerun.")}`);
    });
  } else {
    lines.push("No Slither/Semgrep/Aderyn status was attached to this scan payload.");
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
  const staticToolRows = buildStaticToolRows(result);
  const staticToolsSummary = staticToolSummary(result);
  const realFindings = (result.priority_actions || []).map((item) => {
    const simpleGuide = simpleGuideForAction(item);
    return {
      severity: item.severity,
      module: item.module,
      title: item.title,
      confidence: "medium",
      recommendation: item.recommended_action,
      business_impact: item.business_impact || simpleGuide.simpleRisk,
      fix_guidance: fixGuideForFinding(item.title, item.module),
      beginner_explanation: {
        type: simpleGuide.label,
        proof: simpleGuide.proofLabel,
        plain_problem: simpleGuide.simpleProblem,
        plain_risk: simpleGuide.simpleRisk,
        fix_now: simpleGuide.fixNow,
        verify_after_fix: simpleGuide.verify,
        owner: simpleGuide.owner,
        effort: simpleGuide.effort,
        launch_decision: simpleGuide.launchDecision,
      },
    };
  });

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
    founder_action_plan: buildFounderActionPlan(result, 8),
    gap_closure_plan: buildGapClosurePlan(result),
    human_review_handoff: {
      status: buildGapClosurePlan(result).humanReview.status,
      recommended: buildGapClosurePlan(result).humanReview.needed,
      safe_route: "/manual-review",
      note: "A real reviewer/admin must confirm findings before reviewed-report or strong security wording. No fake marketplace/team claim is created.",
    },
    evidence_summary: result.module_cards.map((card) => ({
      module: card.module,
      module_label: card.label,
      status: card.status,
      score: card.score ?? null,
      evidence: card.evidence || [],
      limitations: card.limitations || [],
    })),
    static_analysis_tool_status: staticToolRows,
    static_analysis_summary: staticToolsSummary,
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
    founder_action_plan: report.founder_action_plan,
    gap_closure_plan: report.gap_closure_plan,
    human_review_handoff: report.human_review_handoff,
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


function StaticToolStatusCard({ result }: { result: UnifiedUrlScanResponse }) {
  const rows = buildStaticToolRows(result);
  const summary = staticToolSummary(result);
  if (!summary) return null;
  const staticCard = result.module_cards.find((card) => card.module === "static_analysis");
  return (
    <CardShell>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="section-label">Static analysis</p>
          <h2 className="mt-2 text-2xl font-black text-white">Slither / Semgrep / Aderyn status</h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
            This block explains whether external static-analysis tools actually ran, were not installed, were disabled by configuration, or were only supplied as JSON artifacts.
          </p>
          <p className="mt-2 text-xs leading-5 text-slate-500">{summary.evidenceRule}</p>
        </div>
        <div className="grid min-w-[280px] gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">State</p>
            <p className="mt-2 text-sm font-black text-white">{summary.state}</p>
          </div>
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Tools ran</p>
            <p className="mt-2 text-2xl font-black text-white">{summary.ranCount}</p>
          </div>
          <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
            <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Real findings</p>
            <p className="mt-2 text-2xl font-black text-white">{summary.realFindingsCount}</p>
          </div>
        </div>
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {rows.map((tool) => (
          <div key={tool.id} className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-base font-black text-white">{tool.label}</p>
                <p className="mt-1 text-xs font-semibold text-slate-500">{tool.status} · {tool.evidenceSource}</p>
              </div>
              <span className={`badge ${statusBadgeClass(tool.state)}`}>{tool.state}</span>
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-400">{tool.detail}</p>
            <p className="mt-3 rounded-xl border border-cyan/10 bg-cyan/5 p-3 text-xs leading-5 text-cyan-50">{tool.action}</p>
          </div>
        ))}
      </div>
      <div className="mt-5 rounded-2xl border border-amber-300/15 bg-amber-300/10 p-4 text-sm leading-6 text-amber-100">
        <p className="font-black">Why it may show Not Assessed</p>
        <p className="mt-2">{summary.note}</p>
        {staticCard?.required_input?.length ? <p className="mt-2 text-xs text-amber-100/80">Next evidence: {staticCard.required_input[0]}</p> : null}
      </div>
    </CardShell>
  );
}

function FindingCard({ action }: { action: UnifiedUrlScanResponse["priority_actions"][number] }) {
  const severity = (action.severity || "info") as Severity;
  const guide = fixGuideForFinding(action.title, action.module);
  const simple = simpleGuideForAction(action);
  return (
    <details className="group rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4 open:border-cyan/20 open:bg-cyan/[0.035]">
      <summary className="flex cursor-pointer list-none flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge severity={severity} />
            <span className={`badge ${simple.badgeClass}`}>{simple.label}</span>
            <span className="badge badge-cyan">{simple.launchDecision}</span>
          </div>
          <h3 className="mt-3 text-lg font-black text-white">{action.title}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-300"><b className="text-white">Simple meaning:</b> {simple.simpleProblem}</p>
          <p className="mt-2 text-xs leading-5 text-slate-500">{simple.proofLabel}</p>
        </div>
        <span className="badge badge-cyan shrink-0">{action.module_label || action.module}</span>
      </summary>

      <div className="mt-4 border-t border-white/[0.07] pt-4">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-xl border border-red-400/15 bg-red-500/10 p-3">
            <p className="mono text-[10px] font-bold uppercase tracking-[0.16em] text-red-100/70">Why this matters</p>
            <p className="mt-2 text-sm leading-6 text-red-50/90">{simple.simpleRisk}</p>
          </div>
          <div className="rounded-xl border border-cyan/10 bg-cyan/5 p-3">
            <p className="mono text-[10px] font-bold uppercase tracking-[0.16em] text-cyan">Fix now</p>
            <p className="mt-2 text-sm leading-6 text-cyan-50">{simple.fixNow}</p>
          </div>
          <div className="rounded-xl border border-white/[0.06] bg-black/20 p-3">
            <p className="mono text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Who should fix</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">{simple.owner}</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">Expected effort: {simple.effort}</p>
          </div>
          <div className="rounded-xl border border-white/[0.06] bg-black/20 p-3">
            <p className="mono text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">How to confirm fixed</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">{simple.verify}</p>
          </div>
        </div>

        <div className="mt-3 rounded-xl border border-amber-300/15 bg-amber-300/10 p-3 text-xs leading-5 text-amber-100/90">
          <p className="font-black text-amber-50">Important</p>
          <p className="mt-1">{simple.whyNotExploitClaim}</p>
        </div>

        <details className="mt-3 rounded-xl border border-white/[0.06] bg-black/20 p-3">
          <summary className="cursor-pointer text-xs font-black uppercase tracking-[0.12em] text-slate-300">Show technical fix details</summary>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {[
              ["Where to fix", guide.where_to_fix],
              ["Technical reason", guide.why_it_matters],
              ["Developer fix", guide.how_to_fix],
              ["Verification", guide.verify],
            ].map(([title, text]) => (
              <div key={title} className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-3">
                <p className="mono text-[10px] font-bold uppercase tracking-[0.16em] text-cyan">{title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">{text}</p>
              </div>
            ))}
          </div>
          {action.recommended_action ? <p className="mt-3 text-xs leading-5 text-slate-500">Original scanner recommendation: {action.recommended_action}</p> : null}
        </details>
      </div>
    </details>
  );
}

function isModuleAssessed(card: UnifiedModuleCard) {
  return Boolean(card.assessed || card.score !== null);
}

function severityRank(severity?: string | null) {
  const value = String(severity || "info").toLowerCase();
  if (value === "critical") return 0;
  if (value === "high") return 1;
  if (value === "medium") return 2;
  if (value === "low") return 3;
  return 4;
}

function FounderReportPolishCard({ result }: { result: UnifiedUrlScanResponse }) {
  const tasks = buildFounderActionPlan(result, 5);
  const gaps = buildGapClosurePlan(result);
  const criticalHigh = (result.priority_actions || []).filter((item) => item.severity === "critical" || item.severity === "high").length;
  const unknownModules = result.module_cards.filter((card) => !isModuleAssessed(card)).length;
  const launchLine = criticalHigh > 0
    ? "Do not launch with strong security claims until the top red items are fixed or reviewed."
    : unknownModules > 0
      ? "Assessed modules look usable, but unknown modules still need evidence before strong claims."
      : "No priority launch blocker is visible in assessed modules; keep the report wording limited and honest.";

  return (
    <CardShell className="border-emerald-400/15 bg-emerald-400/[0.035]">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="section-label">Phase Y report view</p>
          <h2 className="mt-2 text-2xl font-black text-white">Founder-friendly report</h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-300">
            This turns scanner output into simple launch tasks: what is the issue, why it matters, who should fix it, and how to confirm it is fixed.
          </p>
        </div>
        <div className="rounded-2xl border border-emerald-400/15 bg-emerald-400/10 p-4 text-sm leading-6 text-emerald-50 lg:max-w-sm">
          <p className="font-black text-white">Launch reading</p>
          <p className="mt-2">{launchLine}</p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
          <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Fix first</p>
          <p className="mt-2 text-lg font-black text-white">Top launch tasks</p>
          <p className="mt-2 text-xs leading-5 text-slate-400">Sorted by severity so non-technical users do not need to read every raw finding.</p>
        </div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
          <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Static tools</p>
          <p className="mt-2 text-lg font-black text-white">{gaps.staticAnalysis.status}</p>
          <p className="mt-2 text-xs leading-5 text-slate-400">Slither, Semgrep, and Aderyn are never faked. Add real artifacts or use an isolated worker.</p>
        </div>
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
          <p className="mono text-[10px] uppercase tracking-[0.16em] text-slate-500">Human review</p>
          <p className="mt-2 text-lg font-black text-white">{gaps.humanReview.status}</p>
          <p className="mt-2 text-xs leading-5 text-slate-400">Reviewer/team status must be real. This UI prepares the handoff; it does not invent auditors.</p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {tasks.length ? tasks.map((task, index) => (
          <div key={`${task.title}-${index}`} className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="flex flex-wrap gap-2">
                  <span className="badge badge-cyan">#{index + 1}</span>
                  <span className={`badge ${task.badgeClass}`}>{task.type}</span>
                  <SeverityBadge severity={task.severity as Severity} />
                </div>
                <h3 className="mt-3 text-base font-black text-white">{task.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-300"><b className="text-white">Meaning:</b> {task.plainProblem}</p>
                <p className="mt-1 text-sm leading-6 text-slate-400"><b className="text-white">Risk:</b> {task.plainRisk}</p>
              </div>
              <div className="shrink-0 rounded-xl border border-white/[0.07] bg-black/20 p-3 text-xs leading-5 text-slate-300 sm:max-w-[260px]">
                <p><b className="text-white">Owner:</b> {task.owner}</p>
                <p className="mt-1"><b className="text-white">Effort:</b> {task.effort}</p>
                <p className="mt-1"><b className="text-white">Decision:</b> {task.launchDecision}</p>
              </div>
            </div>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <p className="rounded-xl border border-cyan/10 bg-cyan/5 p-3 text-sm leading-6 text-cyan-50"><b>Fix:</b> {task.fixNow}</p>
              <p className="rounded-xl border border-white/[0.07] bg-black/20 p-3 text-sm leading-6 text-slate-300"><b>Confirm:</b> {task.verify}</p>
            </div>
          </div>
        )) : (
          <p className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm leading-6 text-emerald-100">No priority action is visible in the assessed modules. Still review Not Assessed modules before strong security claims.</p>
        )}
      </div>
    </CardShell>
  );
}

function GapClosureCard({ result, onOpenEvidence }: { result: UnifiedUrlScanResponse; onOpenEvidence: (fieldId: string) => void }) {
  const gaps = buildGapClosurePlan(result);
  const toolButtons = [
    { id: "slither-json", label: "Add Slither JSON" },
    { id: "semgrep-json", label: "Add Semgrep JSON" },
    { id: "aderyn-json", label: "Add Aderyn JSON" },
  ];

  return (
    <CardShell className="border-amber-300/15 bg-amber-300/[0.035]">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="section-label">Gap closure</p>
          <h2 className="mt-2 text-2xl font-black text-white">Cover the two real gaps safely</h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-300">
            Web3Guard will not pretend that tools ran or that a reviewer team exists. Use these two paths to move from scanner output to stronger professional evidence.
          </p>
        </div>
        <span className="badge badge-amber w-fit">No fake audit claim</span>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="section-label">Gap 1</p>
              <h3 className="mt-2 text-lg font-black text-white">Slither / Semgrep / Aderyn live execution</h3>
            </div>
            <span className="badge badge-amber">{gaps.staticAnalysis.status}</span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-300">{gaps.staticAnalysis.reason}</p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-400">
            {gaps.staticAnalysis.safePaths.map((step) => <li key={step}>• {step}</li>)}
          </ul>
          <div className="mt-4 flex flex-wrap gap-2">
            {toolButtons.map((button) => (
              <button key={button.id} type="button" onClick={() => onOpenEvidence(button.id)} className="btn-secondary !px-3 !py-2 text-xs">
                {button.label}
              </button>
            ))}
            <Link href="/professional/setup" className="btn-secondary !px-3 !py-2 text-xs">Worker setup guide</Link>
          </div>
        </div>

        <div className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="section-label">Gap 2</p>
              <h3 className="mt-2 text-lg font-black text-white">Human reviewer handoff</h3>
            </div>
            <span className="badge badge-cyan">{gaps.humanReview.status}</span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-300">{gaps.humanReview.reason}</p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-400">
            {gaps.humanReview.safePaths.map((step) => <li key={step}>• {step}</li>)}
          </ul>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link href="/manual-review" className="btn-primary !px-3 !py-2 text-xs">Open manual review</Link>
            <Link href="/contact" className="btn-secondary !px-3 !py-2 text-xs">Request human review</Link>
          </div>
          <p className="mt-3 rounded-xl border border-red-400/15 bg-red-500/10 p-3 text-xs leading-5 text-red-100/90">
            Do not display verified marketplace/team claims until real reviewers are onboarded, verified, assigned, and logged.
          </p>
        </div>
      </div>
    </CardShell>
  );
}

function ModuleCard({ card }: { card: UnifiedModuleCard }) {
  const assessed = isModuleAssessed(card);
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

  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stageIndex, setStageIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [fieldPrompt, setFieldPrompt] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [result, setResult] = useState<UnifiedUrlScanResponse | null>(null);
  const [exportStatus, setExportStatus] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<"all" | Severity>("all");

  const selectedProject = projects.find((project) => project.id === selectedProjectId) || null;
  const selectedHistory = scanHistory.find((scan) => scan.id === selectedHistoryId) || null;
  const currentStage = scanStages[Math.min(stageIndex, scanStages.length - 1)];
  const activeScanMode = scanModeOptions.find((option) => option.id === scanMode) ?? scanModeOptions[0];

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
    if (projectType === "Other" && !customProjectType.trim()) missing.push("Custom project type");
    if (chain === "Other" && !customChain.trim()) missing.push("Custom chain");
    if (!authorized) missing.push("Permission confirmation");
    return missing;
  }, [authorized, chain, customChain, customProjectType, projectType, websiteUrl]);

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
  const priorityActions = result?.priority_actions || [];
  const sortedPriorityActions = [...priorityActions].sort((a, b) => severityRank(a.severity) - severityRank(b.severity));
  const filteredPriorityActions = severityFilter === "all" ? sortedPriorityActions : sortedPriorityActions.filter((action) => action.severity === severityFilter);
  const fixFirstActions = sortedPriorityActions.slice(0, 3);
  const severityCounts = priorityActions.reduce<Record<string, number>>((counts, action) => {
    const severity = action.severity || "info";
    counts[severity] = (counts[severity] || 0) + 1;
    return counts;
  }, {});
  const assessedCards = cards.filter(isModuleAssessed);
  const notAssessedCards = cards.filter((card) => !isModuleAssessed(card));
  const coverageCtaText = requiredInputs.length
    ? "Add GitHub, contract, API, HAR, wallet-flow, or test artifacts to unlock deeper coverage."
    : "Coverage evidence looks complete for the modules returned in this scan.";

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
    setAdvancedOpen(false);
    setScanMode("quick");
    setResult(null);
    clearLatestUnifiedScan();
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
          real_only_acknowledged: true,
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
      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl space-y-6">
          <CardShell className="scanner-premium-console scanner-premium-console-clean card-glow">
            <div className="scanner-premium-aurora" aria-hidden="true" />
            <div className="scanner-premium-grid scanner-premium-grid-single">
              <div className="scanner-input-panel scanner-input-panel-wide">

                <div className="rounded-3xl border border-cyan-300/10 bg-cyan-300/[0.04] p-4 sm:p-5">
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                    <div className="min-w-0 flex-1">
                      <p className="section-label">Step 1 · Beginner friendly</p>
                      <h2 className="mt-2 text-2xl font-black text-white">Paste your website link</h2>
                      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
                        For a normal user, only this one URL is needed. Web3Guard will check public website evidence and will clearly mark anything deeper as Not Assessed instead of guessing.
                      </p>
                    </div>
                    <span className="badge badge-cyan w-fit">No code setup needed</span>
                  </div>

                  <div className="mt-4">
                    <FieldLabel label="Website / dApp URL" required>
                      <input
                        className="input scanner-input-xl scanner-premium-url"
                        value={websiteUrl}
                        onChange={(event) => setWebsiteUrl(event.target.value)}
                        placeholder="https://yourproject.com"
                      />
                    </FieldLabel>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-400">
                    <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1">Checks headers/CSP/cookies</span>
                    <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1">Finds public exposure hints</span>
                    <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1">No cloning or exploit testing</span>
                    <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1">Missing proof = Not Assessed</span>
                  </div>
                </div>

                <div className="rounded-3xl border border-white/10 bg-white/[0.025] p-4 sm:p-5">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="section-label">Step 2 · Scan depth</p>
                      <h3 className="mt-2 text-xl font-black text-white">Choose how much evidence you want to add</h3>
                      <p className="mt-2 text-sm leading-6 text-slate-400">
                        Stay on Simple Scan if you are new. Developers can open Deep or Expert mode for repo, API, contract, and tool artifacts.
                      </p>
                    </div>
                    <span className="badge">Current: {activeScanMode.title}</span>
                  </div>

                  <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 p-3">
                    <div className="grid gap-2 sm:grid-cols-3">
                      {scanModeOptions.map((option) => {
                        const selected = scanMode === option.id;
                        const simpleTitle = option.id === "quick" ? "1. Simple" : option.id === "deep" ? "2. Developer" : "3. Expert";
                        const simpleSubtitle = option.id === "quick"
                          ? "Website only"
                          : option.id === "deep"
                            ? "Add GitHub/API/contract"
                            : "Add tool JSON/artifacts";
                        return (
                          <button
                            key={option.id}
                            type="button"
                            onClick={() => {
                              setScanMode(option.id);
                              setAdvancedOpen(option.id !== "quick");
                              setActiveEvidenceEditor(null);
                            }}
                            className={`rounded-xl border px-3 py-3 text-left transition ${selected ? "border-cyan-300/35 bg-cyan-300/[0.10] text-white" : "border-white/10 bg-white/[0.03] text-slate-400 hover:border-cyan-300/20 hover:text-white"}`}
                          >
                            <span className="block text-sm font-black">{simpleTitle}</span>
                            <span className="mt-1 block text-xs leading-5">{simpleSubtitle}</span>
                          </button>
                        );
                      })}
                    </div>
                    <p className="mt-3 text-xs leading-5 text-slate-500">
                      Beginner? Keep <b className="text-slate-300">Simple</b>. Web3Guard will not ask for GitHub, contracts, Slither, Semgrep, or Aderyn unless you choose Developer/Expert.
                    </p>
                  </div>

                  {scanMode !== "quick" ? (
                    <div className="mt-5 space-y-4 rounded-3xl border border-cyan-300/10 bg-cyan-300/[0.035] p-4">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <p className="text-sm font-black text-white">Developer evidence fields</p>
                          <p className="mt-1 text-xs leading-5 text-slate-400">Optional fields. Add what you have; empty areas will stay Not Assessed.</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => setAdvancedOpen((value) => !value)}
                          className="w-fit rounded-full border border-cyan-300/20 bg-cyan-300/[0.08] px-3 py-1.5 text-[11px] font-semibold text-cyan-100 transition hover:border-cyan-300/40 hover:bg-cyan-300/[0.14]"
                        >
                          {advancedOpen ? "Hide fields" : "Open fields"}
                        </button>
                      </div>

                      {advancedOpen ? (
                        <>
                          <div className="grid gap-3 lg:grid-cols-2">
                            <FieldLabel label="Project type (optional)">
                              <select className="select scanner-choice-select" value={projectType} onChange={(event) => setProjectType(event.target.value)}>
                                <option value="">Auto / not sure</option>
                                {projectTypeOptions.map((option) => <option key={option} value={option}>{option}</option>)}
                              </select>
                            </FieldLabel>

                            <FieldLabel label="Chain / surface (optional)">
                              <select className="select scanner-choice-select" value={chain} onChange={(event) => setChain(event.target.value)}>
                                <option value="">Auto / Web only</option>
                                {chainOptions.map((option) => <option key={option} value={option}>{option}</option>)}
                              </select>
                            </FieldLabel>
                          </div>

                          {(projectType === 'Other' || chain === 'Other') ? (
                            <div className="grid gap-3 lg:grid-cols-2">
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

                          <div className="grid gap-3 lg:grid-cols-3">
                            <FieldLabel label="GitHub repo URL (optional)">
                              <input className="input" value={githubRepoUrl} onChange={(event) => setGithubRepoUrl(event.target.value)} placeholder="https://github.com/org/repo" />
                            </FieldLabel>
                            <FieldLabel label="API base URL (optional)">
                              <input className="input" value={apiBaseUrl} onChange={(event) => setApiBaseUrl(event.target.value)} placeholder="https://api.yourproject.com" />
                            </FieldLabel>
                            <FieldLabel label="Contract address (optional)">
                              <input className="input" value={contractAddress} onChange={(event) => setContractAddress(event.target.value)} placeholder="0x..." />
                            </FieldLabel>
                          </div>

                          <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-3">
                            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                              <div>
                                <p className="text-sm font-black text-white">Paste advanced evidence only if you have it</p>
                                <p className="mt-1 text-xs leading-5 text-slate-400">New users can skip this. Experts can open one editor at a time.</p>
                              </div>
                              <span className="badge badge-amber">Optional</span>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2">
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
                  ) : (
                    <div className="mt-4 rounded-2xl border border-emerald-400/15 bg-emerald-400/10 p-4 text-sm leading-6 text-emerald-50">
                      Simple Scan selected: only paste the website URL, confirm permission, then run. GitHub, contract, API, Slither, Semgrep, and Aderyn will stay Not Assessed unless you switch to Deep/Expert mode and provide evidence.
                    </div>
                  )}
                </div>

                <div className="scanner-consent-grid">
                  <label className={`scanner-check-card ${authorized ? "scanner-check-card-on" : ""}`}>
                    <input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} />
                    <span>
                      <strong>I have permission to scan this project</strong>
                      <small>Only scan your own project or a project you are allowed to review.</small>
                    </span>
                  </label>
                  <div className="scanner-check-card scanner-check-card-on">
                    <span>
                      <strong>Real-only result is always on</strong>
                      <small>No fake audit claim. Missing proof stays Not Assessed.</small>
                    </span>
                  </div>
                </div>

                {fieldPrompt ? <p className="mt-4 rounded-xl border border-amber-300/20 bg-amber-300/10 p-3 text-sm text-amber-100">{fieldPrompt}</p> : null}

                <div className="scanner-action-row">
                  <button type="button" onClick={() => void runScan()} disabled={!canRunScan} className="btn-primary scanner-run-button">
                    {loading ? 'Scanning...' : 'Start scan →'}
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
                  <div className="mt-5 grid gap-3 sm:grid-cols-4">
                    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                      <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Assessed</p>
                      <p className="mt-1 text-2xl font-black text-white">{assessedCards.length || result.live_module_count || 0}</p>
                    </div>
                    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                      <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Need evidence</p>
                      <p className="mt-1 text-2xl font-black text-white">{notAssessedCards.length}</p>
                    </div>
                    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                      <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Critical/High</p>
                      <p className="mt-1 text-2xl font-black text-white">{(severityCounts.critical || 0) + (severityCounts.high || 0)}</p>
                    </div>
                    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                      <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Actions</p>
                      <p className="mt-1 text-2xl font-black text-white">{priorityActions.length}</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardShell>

            <CardShell className="border-cyan/15 bg-cyan/[0.04]">
              <div className="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
                <div>
                  <p className="section-label">Public beta summary</p>
                  <h2 className="mt-2 text-2xl font-black text-white">What to fix first</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-400">This view is compressed for founders: fix the highest-risk items first, then add missing evidence for deeper assessment.</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="badge badge-amber">Pre-audit readiness only</span>
                    <span className="badge badge-cyan">{coverageCtaText}</span>
                  </div>
                </div>
                <div className="space-y-3">
                  {fixFirstActions.length ? fixFirstActions.map((action, index) => (
                    <div key={`${action.title}-${index}-fix-first`} className="rounded-2xl border border-white/[0.07] bg-black/20 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm font-black text-white">{index + 1}. {action.title}</p>
                        <SeverityBadge severity={(action.severity || "info") as Severity} />
                      </div>
                      <p className="mt-2 text-xs leading-5 text-slate-400">{action.recommended_action}</p>
                    </div>
                  )) : (
                    <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-100">No priority fixes were returned for the assessed evidence.</div>
                  )}
                </div>
              </div>
            </CardShell>

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

            <BeginnerBugSummaryCard result={result} />

            <FounderReportPolishCard result={result} />

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

            <StaticToolStatusCard result={result} />

            <GapClosureCard
              result={result}
              onOpenEvidence={(fieldId) => {
                setScanMode("expert");
                setAdvancedOpen(true);
                setActiveEvidenceEditor(fieldId);
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
            />

            <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
              <CardShell>
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="section-label">Priority actions</p>
                    <h2 className="mt-2 text-2xl font-black text-white">Findings with fix hints</h2>
                    <p className="mt-2 text-sm leading-6 text-slate-400">Use the filter to focus on the highest-impact work first.</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(["all", "critical", "high", "medium", "low", "info"] as Array<"all" | Severity>).map((severity) => (
                      <button
                        key={severity}
                        type="button"
                        onClick={() => setSeverityFilter(severity)}
                        className={`rounded-full border px-3 py-2 text-xs font-black uppercase tracking-[0.12em] transition ${severityFilter === severity ? "border-cyan/40 bg-cyan/15 text-cyan-50" : "border-white/[0.08] bg-white/[0.03] text-slate-400 hover:border-white/20 hover:text-white"}`}
                      >
                        {severity === "all" ? "All" : `${severity} ${severityCounts[severity] || 0}`}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="mt-5 space-y-3">
                  {filteredPriorityActions.length ? filteredPriorityActions.map((action, index) => <FindingCard key={`${action.title}-${index}-${severityFilter}`} action={action} />) : <p className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-100">No priority findings matched this filter.</p>}
                </div>
              </CardShell>

              <CardShell>
                <p className="section-label">Deep scan coverage</p>
                <h2 className="mt-2 text-2xl font-black text-white">Add evidence to unlock deeper results</h2>
                <p className="mt-2 text-sm leading-6 text-slate-400">Not Assessed does not mean safe or unsafe. It means Web3Guard did not receive enough real evidence to score that module.</p>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <button type="button" className="btn-secondary !justify-center" onClick={() => { setScanMode("deep"); setAdvancedOpen(true); }}>Add GitHub / Contract</button>
                  <button type="button" className="btn-secondary !justify-center" onClick={() => { setScanMode("deep"); setAdvancedOpen(true); }}>Add API evidence</button>
                  <button type="button" className="btn-secondary !justify-center" onClick={() => { setScanMode("expert"); setAdvancedOpen(true); }}>Add expert artifacts</button>
                </div>
                <details className="mt-5 rounded-2xl border border-amber-300/15 bg-amber-300/10 p-4">
                  <summary className="cursor-pointer list-none text-sm font-black text-amber-50">Show Not Assessed queue ({requiredInputs.length})</summary>
                  <div className="mt-4 space-y-3">
                    {requiredInputs.length ? requiredInputs.map(({ label, item, guide }) => (
                      <div key={`${label}-${item}`} className="rounded-2xl border border-amber-300/15 bg-black/20 p-4">
                        <p className="text-sm font-black text-amber-50">{label}</p>
                        <p className="mt-2 text-sm leading-6 text-amber-100/90">{item}</p>
                        <p className="mt-3 text-xs leading-5 text-amber-100/70">{guide}</p>
                      </div>
                    )) : <p className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-100">No missing evidence listed in this result.</p>}
                  </div>
                </details>
              </CardShell>
            </div>

            <CardShell>
              <p className="section-label">Module matrix</p>
              <h2 className="mt-2 text-2xl font-black text-white">Assessed modules first</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">Public beta output now keeps assessed evidence visible and moves evidence gaps into a collapsible section.</p>
              <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {(assessedCards.length ? assessedCards : cards.slice(0, 3)).map((card) => <ModuleCard key={card.module} card={card} />)}
              </div>
              {notAssessedCards.length ? (
                <details className="mt-5 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                  <summary className="cursor-pointer list-none text-sm font-black text-white">Show {notAssessedCards.length} Not Assessed modules</summary>
                  <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {notAssessedCards.map((card) => <ModuleCard key={card.module} card={card} />)}
                  </div>
                </details>
              ) : null}
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
