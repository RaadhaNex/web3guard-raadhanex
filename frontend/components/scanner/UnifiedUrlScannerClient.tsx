"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiPost } from "@/lib/api";
import { getCurrentUserId, getSessionToken } from "@/lib/supabase";
import type { UnifiedModuleCard, UnifiedUrlScanResponse } from "@/lib/types";
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

function sortModuleCards(cards: UnifiedModuleCard[]) {
  return [...cards].sort((a, b) => {
    const aIndex = moduleOrder.indexOf(a.module);
    const bIndex = moduleOrder.indexOf(b.module);

    return (aIndex === -1 ? 999 : aIndex) - (bIndex === -1 ? 999 : bIndex);
  });
}

export function UnifiedUrlScannerClient() {
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [projectName, setProjectName] = useState("");
  const [projectType, setProjectType] = useState("Website / dApp Frontend");
  const [chain, setChain] = useState("Web only");
  const [contractAddress, setContractAddress] = useState("");
  const [apiBaseUrl, setApiBaseUrl] = useState("");
  const [githubRepoUrl, setGithubRepoUrl] = useState("");
  const [solidityCode, setSolidityCode] = useState("");
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);

  const [authLoading, setAuthLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stageIndex, setStageIndex] = useState(0);

  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [result, setResult] = useState<UnifiedUrlScanResponse | null>(null);

  const currentStage = scanStages[Math.min(stageIndex, scanStages.length - 1)];

  const canRunScan = useMemo(() => {
    return (
      isLoggedIn &&
      authorized &&
      realOnly &&
      Boolean(websiteUrl.trim()) &&
      !loading
    );
  }, [authorized, isLoggedIn, loading, realOnly, websiteUrl]);

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
    setSaveMessage(null);
    setResult(null);

    if (!isLoggedIn) {
      setError("Login required. Please login before running a real scan.");
      return;
    }

    const cleanWebsiteUrl = normaliseUrl(websiteUrl);

    if (!cleanWebsiteUrl) {
      setError("Please enter a valid website / dApp URL.");
      return;
    }

    if (!authorized || !realOnly) {
      setError(
        "Please confirm authorization and real-only scoring before running the scan."
      );
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
          project_type: projectType.trim() || "Website / dApp Frontend",
          chain: chain.trim() || "Web only",
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

      const projectResponse = await apiPost<{ project: { id: string } }>(
        "/projects",
        {
          user_id: userId,
          name: projectName.trim() || result.project_name || "Unified URL Scan",
          website_url: websiteUrl,
          chain,
          contract_address: contractAddress || null,
          github_repo_url: githubRepoUrl || null,
          project_type: projectType,
          description:
            "Created from unified URL launch scanner. Only actually assessed modules were scored.",
        },
        { headers }
      );

      const criticalHigh =
        result.priority_actions?.filter(
          (item) => item.severity === "critical" || item.severity === "high"
        ).length || 0;

      await apiPost(
        "/scan-history",
        {
          user_id: userId,
          project_id: projectResponse.project.id,
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
        "Scan saved to your dashboard as a real record. Not assessed modules remain unscored."
      );
    } catch (err) {
      setError(readableClientError(err));
    } finally {
      setSaveLoading(false);
    }
  }

  const cards = result?.module_cards ? sortModuleCards(result.module_cards) : [];

  return (
    <main className="min-h-screen bg-[#f7fafc] text-slate-950">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_0.75fr] lg:items-center">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.32em] text-cyan-500">
                Real-only launch scanner
              </p>

              <h1 className="mt-4 max-w-4xl text-4xl font-black tracking-tight text-slate-950 sm:text-6xl">
                Unified Website URL Launch Scanner
              </h1>

              <p className="mt-5 max-w-3xl text-base leading-7 text-slate-600">
                Login required. This scanner runs passive evidence-based checks
                only. Missing contract, wallet, admin, and source inputs are
                shown as <strong>Not assessed</strong>, never fake-scored.
              </p>

              <div className="mt-6 flex flex-wrap gap-3">
                <span className="rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-bold text-emerald-700">
                  Evidence-based
                </span>
                <span className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-bold text-slate-700">
                  No exploit automation
                </span>
                <span className="rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-bold text-amber-700">
                  Not a certified audit
                </span>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm font-bold text-slate-500">
                Session status
              </p>

              {authLoading ? (
                <p className="mt-2 text-2xl font-black text-slate-800">
                  Checking login...
                </p>
              ) : isLoggedIn ? (
                <p className="mt-2 text-2xl font-black text-emerald-600">
                  Logged in
                </p>
              ) : (
                <>
                  <p className="mt-2 text-2xl font-black text-rose-600">
                    Login required
                  </p>
                  <Link
                    href="/auth/login"
                    className="mt-4 inline-flex rounded-2xl bg-slate-950 px-5 py-3 text-sm font-black text-white"
                  >
                    Login to scan
                  </Link>
                </>
              )}

              <p className="mt-4 text-sm leading-6 text-slate-600">
                Scan records can be saved only to the authenticated user’s
                dashboard.
              </p>
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-bold text-slate-800">
                Project name
                <input
                  className="input mt-2"
                  value={projectName}
                  onChange={(event) => setProjectName(event.target.value)}
                  placeholder="Example: My Web3 Launch"
                />
              </label>

              <label className="block text-sm font-bold text-slate-800">
                Project type
                <input
                  className="input mt-2"
                  value={projectType}
                  onChange={(event) => setProjectType(event.target.value)}
                  placeholder="Website / dApp Frontend"
                />
              </label>
            </div>

            <label className="mt-4 block text-sm font-bold text-slate-800">
              Website / dApp URL <span className="text-rose-500">*</span>
              <input
                className="input mt-2"
                value={websiteUrl}
                onChange={(event) => setWebsiteUrl(event.target.value)}
                placeholder="https://yourproject.com"
              />
            </label>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-bold text-slate-800">
                Chain
                <input
                  className="input mt-2"
                  value={chain}
                  onChange={(event) => setChain(event.target.value)}
                  placeholder="Web only / Ethereum / Polygon"
                />
              </label>

              <label className="block text-sm font-bold text-slate-800">
                Contract address optional
                <input
                  className="input mt-2"
                  value={contractAddress}
                  onChange={(event) => setContractAddress(event.target.value)}
                  placeholder="0x..."
                />
              </label>
            </div>

            <label className="mt-4 block text-sm font-bold text-slate-800">
              API base URL optional
              <input
                className="input mt-2"
                value={apiBaseUrl}
                onChange={(event) => setApiBaseUrl(event.target.value)}
                placeholder="https://api.yourproject.com"
              />
            </label>

            <label className="mt-4 block text-sm font-bold text-slate-800">
              GitHub repo URL optional
              <input
                className="input mt-2"
                value={githubRepoUrl}
                onChange={(event) => setGithubRepoUrl(event.target.value)}
                placeholder="https://github.com/team/project"
              />
            </label>

            <label className="mt-4 block text-sm font-bold text-slate-800">
              Solidity source optional for real contract score
              <textarea
                className="textarea mono mt-2 min-h-[150px]"
                value={solidityCode}
                onChange={(event) => setSolidityCode(event.target.value)}
                placeholder="Paste Solidity source here if you want the contract module scored."
              />
            </label>

            <div className="mt-5 space-y-3 rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              <label className="flex gap-3">
                <input
                  type="checkbox"
                  checked={authorized}
                  onChange={(event) => setAuthorized(event.target.checked)}
                />
                <span>
                  I own this project or have authorization to run passive checks.
                </span>
              </label>

              <label className="flex gap-3">
                <input
                  type="checkbox"
                  checked={realOnly}
                  onChange={(event) => setRealOnly(event.target.checked)}
                />
                <span>
                  I understand missing modules will be marked Not assessed.
                </span>
              </label>
            </div>

            {loading ? (
              <div className="mt-5 rounded-3xl border border-cyan-200 bg-cyan-50 p-4">
                <div className="flex items-center justify-between gap-4">
                  <p className="text-sm font-black text-cyan-900">
                    {currentStage}
                  </p>
                  <p className="text-sm font-bold text-cyan-700">
                    {progress}%
                  </p>
                </div>

                <div className="mt-3 h-3 overflow-hidden rounded-full bg-white">
                  <div
                    className="h-full rounded-full bg-cyan-400 transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>

                <p className="mt-3 text-xs leading-5 text-cyan-800">
                  Progress is estimated while the backend performs real passive
                  checks. Results are shown only after the API returns evidence.
                </p>
              </div>
            ) : null}

            {error ? (
              <p className="mt-4 whitespace-pre-wrap rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm font-semibold text-rose-800">
                {error}
              </p>
            ) : null}

            <button
              className="mt-5 w-full rounded-2xl bg-cyan-400 px-5 py-4 text-base font-black text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={runScan}
              disabled={!canRunScan}
            >
              {loading ? "Scanning..." : "Run Unified URL Scan"}
            </button>

            {!isLoggedIn && !authLoading ? (
              <p className="mt-3 text-center text-sm text-slate-500">
                Login is required before running a scan.
              </p>
            ) : null}
          </div>

          <div className="space-y-5">
            {!result ? (
              <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
                <p className="text-xl font-black text-slate-950">
                  What this scanner will do
                </p>

                <div className="mt-5 grid gap-3">
                  {[
                    "Check website reachability, HTTPS, and headers",
                    "Validate API URL if provided",
                    "Read public GitHub repository metadata if provided",
                    "Score Solidity source only if source is pasted",
                    "Mark missing wallet/admin/contract context as Not assessed",
                  ].map((item) => (
                    <div
                      key={item}
                      className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm font-semibold text-slate-700"
                    >
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {result ? (
              <>
                <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-bold text-slate-500">
                        Available partial score
                      </p>
                      <p
                        className={`mt-2 text-6xl font-black ${scoreTone(
                          result.available_score
                        )}`}
                      >
                        {result.available_score ?? "N/A"}
                      </p>
                      <p className="mt-2 text-sm font-semibold text-slate-600">
                        {result.risk_label || "Not assessed"}
                      </p>
                    </div>

                    <div className="rounded-2xl border border-cyan-200 bg-cyan-50 px-4 py-3 text-sm font-black text-cyan-700">
                      {result.live_module_count} live/limited module(s)
                    </div>
                  </div>

                  <button
                    type="button"
                    disabled={saveLoading}
                    onClick={saveUnifiedScanToDashboard}
                    className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-black text-slate-900 transition hover:bg-white disabled:opacity-50"
                  >
                    {saveLoading ? "Saving..." : "Save to Dashboard"}
                  </button>

                  {saveMessage ? (
                    <p className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-800">
                      {saveMessage}
                    </p>
                  ) : null}

                  <p className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                    {result.realness_rule}
                  </p>

                  <p className="mt-3 text-xs leading-5 text-amber-700">
                    {result.safe_public_summary}
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  {cards.map((card) => (
                    <div
                      key={card.module}
                      className="rounded-[1.6rem] border border-slate-200 bg-white p-5 shadow-sm"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <h3 className="font-black text-slate-950">
                          {card.label}
                        </h3>
                        <span
                          className={`rounded-full border px-3 py-1 text-xs font-black ${statusClass(
                            card.status
                          )}`}
                        >
                          {card.status}
                        </span>
                      </div>

                      <p className="mt-3 text-sm text-slate-600">
                        Score:{" "}
                        <span className="font-black text-slate-950">
                          {card.score ?? "Not assessed"}
                        </span>
                      </p>

                      {!!card.evidence?.length ? (
                        <div className="mt-4">
                          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                            Evidence
                          </p>
                          <ul className="mt-2 space-y-1 text-xs text-slate-700">
                            {card.evidence.slice(0, 4).map((item, index) => (
                              <li key={`${card.module}-evidence-${index}`}>
                                • {item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ) : null}

                      {!!card.required_input?.length ? (
                        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-3">
                          <p className="text-xs font-black uppercase tracking-wide text-amber-800">
                            Needed for real score
                          </p>
                          <ul className="mt-2 space-y-1 text-xs text-amber-900">
                            {card.required_input.map((item, index) => (
                              <li key={`${card.module}-required-${index}`}>
                                • {item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ) : null}

                      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                          Fix direction
                        </p>
                        <p className="mt-2 text-xs leading-5 text-slate-700">
                          {moduleFixGuide(card)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {!!result.priority_actions?.length ? (
                  <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
                    <h3 className="text-xl font-black text-slate-950">
                      Priority fixes with guidance
                    </h3>

                    <div className="mt-4 space-y-3">
                      {result.priority_actions.slice(0, 8).map((item) => {
                        const guide = getActionFixGuide(
                          item.title,
                          item.module
                        );

                        return (
                          <div
                            key={`${item.step}-${item.title}`}
                            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                          >
                            <div className="flex flex-wrap items-center gap-3">
                              <SeverityBadge severity={item.severity} />
                              <p className="font-black text-slate-950">
                                {item.title}
                              </p>
                            </div>

                            <p className="mt-2 text-sm text-slate-700">
                              {item.recommended_action}
                            </p>

                            <div className="mt-4 grid gap-3 text-xs sm:grid-cols-2">
                              <div className="rounded-xl bg-white p-3">
                                <p className="font-black text-slate-500">
                                  Where to fix
                                </p>
                                <p className="mt-1 text-slate-800">
                                  {guide.file}
                                </p>
                              </div>

                              <div className="rounded-xl bg-white p-3">
                                <p className="font-black text-slate-500">
                                  Why it matters
                                </p>
                                <p className="mt-1 text-slate-800">
                                  {guide.why}
                                </p>
                              </div>

                              <div className="rounded-xl bg-white p-3">
                                <p className="font-black text-slate-500">
                                  How to fix
                                </p>
                                <p className="mt-1 text-slate-800">
                                  {guide.fix}
                                </p>
                              </div>

                              <div className="rounded-xl bg-white p-3">
                                <p className="font-black text-slate-500">
                                  Verify
                                </p>
                                <p className="mt-1 text-slate-800">
                                  {guide.verify}
                                </p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : null}

                <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
                  <h3 className="text-xl font-black text-slate-950">
                    Blocked fake claims
                  </h3>

                  <ul className="mt-4 space-y-2 text-sm text-slate-700">
                    {result.blocked_claims.map((claim, index) => (
                      <li key={`blocked-claim-${index}`}>• {claim}</li>
                    ))}
                  </ul>
                </div>
              </>
            ) : null}
          </div>
        </section>
      </div>
    </main>
  );
}
