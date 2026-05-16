"use client";

import { useState } from "react";
import { apiPost, apiGet } from "@/lib/api";
import type { ScanResponse } from "@/lib/types";
import { ScoreCard } from "@/components/ui/ScoreCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

type Mode = "website-advanced" | "api-deep" | "wallet-risk";

const configs = {
  "website-advanced": {
    eyebrow: "Web3Guard AI",
    title: "Advanced Website URL Launch Scanner",
    description: "Safe passive website intelligence: Web3 keywords, policy links, visible contract addresses, API hints, social links, scripts, and launch trust gaps.",
    endpoint: "/scan/website-advanced",
  },
  "api-deep": {
    eyebrow: "Web3Guard AI",
    title: "API Backend Deep Readiness Scanner",
    description: "Safe API readiness review using OpenAPI/code/notes and passive URL checks. No fuzzing, no exploit payloads, no auth bypass.",
    endpoint: "/scan/api-deep",
  },
  "wallet-risk": {
    eyebrow: "Web3Guard AI",
    title: "Wallet Risk API Integration Scanner",
    description: "Read-only wallet/token/spender risk context. External GoPlus provider is used only when enabled; missing provider never creates fake results.",
    endpoint: "/scan/wallet-risk",
  },
} as const;

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mono max-h-80 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify(value, null, 2)}</pre>;
}

export function MegaPhaseBScannerClient({ mode }: { mode: Mode }) {
  const config = configs[mode];
  const [projectName, setProjectName] = useState("RAADHANEX Launch Review");
  const [websiteUrl, setWebsiteUrl] = useState("https://example.com");
  const [apiUrl, setApiUrl] = useState("https://api.example.com");
  const [openapiJson, setOpenapiJson] = useState('{"openapi":"3.0.0","paths":{"/admin/withdraw":{"post":{}},"/webhook/razorpay":{"post":{}}}}');
  const [apiCode, setApiCode] = useState('app.add_middleware(CORSMiddleware, allow_origins=["*"])\napp = FastAPI(debug=True)');
  const [notes, setNotes] = useState("Admin reward and allowlist APIs exist. Webhook signature not finalized.");
  const [chain, setChain] = useState("ethereum");
  const [token, setToken] = useState("0x1111111111111111111111111111111111111111");
  const [spender, setSpender] = useState("0x2222222222222222222222222222222222222222");
  const [wallet, setWallet] = useState("");
  const [approvalContract, setApprovalContract] = useState("");
  const [ownershipVerified, setOwnershipVerified] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadStatus() {
    setError(null);
    try { setStatus(await apiGet<Record<string, unknown>>(`${config.endpoint}/status`)); } catch (err) { setError(err instanceof Error ? err.message : "Status failed"); }
  }

  async function runScan() {
    setLoading(true); setError(null); setResult(null);
    try {
      let payload: Record<string, unknown> = { project_name: projectName, authorization_confirmed: authorized, real_only_acknowledged: realOnly };
      if (mode === "website-advanced") payload = { ...payload, website_url: websiteUrl, ownership_verified: ownershipVerified, max_internal_pages: 4 };
      if (mode === "api-deep") payload = { ...payload, api_base_url: apiUrl || null, openapi_json: openapiJson || null, api_code: apiCode || null, notes: notes || null, ownership_verified: ownershipVerified };
      if (mode === "wallet-risk") payload = { ...payload, chain, token_address: token || null, spender_address: spender || null, wallet_address: wallet || null, approval_contract_address: approvalContract || null };
      setResult(await apiPost<ScanResponse>(config.endpoint, payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally { setLoading(false); }
  }

  return <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
    <div className="max-w-4xl">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">{config.eyebrow}</p>
      <h1 className="mt-3 text-3xl font-black sm:text-5xl">{config.title}</h1>
      <p className="mt-4 text-slate-400">{config.description}</p>
    </div>
    <div className="mt-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <div className="space-y-5">
        <div className="card p-6 space-y-4">
          <label className="block text-sm font-bold text-slate-200">Project name<input className="input mt-2" value={projectName} onChange={(e) => setProjectName(e.target.value)} /></label>
          {mode === "website-advanced" && <>
            <label className="block text-sm font-bold text-slate-200">Website URL<input className="input mt-2" value={websiteUrl} onChange={(e) => setWebsiteUrl(e.target.value)} /></label>
            <label className="flex gap-3 rounded-2xl border border-cyan/20 bg-cyan/10 p-4 text-sm text-cyan-50"><input type="checkbox" checked={ownershipVerified} onChange={(e) => setOwnershipVerified(e.target.checked)} /><span>Ownership verified / allow limited same-domain page checks. Without this, scan stays homepage-only.</span></label>
          </>}
          {mode === "api-deep" && <>
            <label className="block text-sm font-bold text-slate-200">API base URL optional<input className="input mt-2" value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} /></label>
            <label className="block text-sm font-bold text-slate-200">OpenAPI JSON optional<textarea className="input mt-2 min-h-32" value={openapiJson} onChange={(e) => setOpenapiJson(e.target.value)} /></label>
            <label className="block text-sm font-bold text-slate-200">API code/config snippet optional<textarea className="input mt-2 min-h-32" value={apiCode} onChange={(e) => setApiCode(e.target.value)} /></label>
            <label className="block text-sm font-bold text-slate-200">API security notes optional<textarea className="input mt-2 min-h-24" value={notes} onChange={(e) => setNotes(e.target.value)} /></label>
          </>}
          {mode === "wallet-risk" && <>
            <label className="block text-sm font-bold text-slate-200">Chain<select className="input mt-2" value={chain} onChange={(e) => setChain(e.target.value)}><option value="ethereum">Ethereum</option><option value="polygon">Polygon</option><option value="bsc">BNB Chain</option><option value="arbitrum">Arbitrum</option><option value="base">Base</option><option value="avalanche">Avalanche</option></select></label>
            <label className="block text-sm font-bold text-slate-200">Token address optional<input className="input mt-2" value={token} onChange={(e) => setToken(e.target.value)} /></label>
            <label className="block text-sm font-bold text-slate-200">Spender address optional<input className="input mt-2" value={spender} onChange={(e) => setSpender(e.target.value)} /></label>
            <label className="block text-sm font-bold text-slate-200">Wallet address optional/read-only<input className="input mt-2" value={wallet} onChange={(e) => setWallet(e.target.value)} placeholder="Never paste seed/private key" /></label>
            <label className="block text-sm font-bold text-slate-200">Approval contract optional<input className="input mt-2" value={approvalContract} onChange={(e) => setApprovalContract(e.target.value)} /></label>
          </>}
          <div className="space-y-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50">
            <label className="flex gap-3"><input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} /><span>I own this project or have authorization for this safe readiness review.</span></label>
            <label className="flex gap-3"><input type="checkbox" checked={realOnly} onChange={(e) => setRealOnly(e.target.checked)} /><span>I understand missing provider/input means Not Run/Not Assessed, never fake output.</span></label>
          </div>
          <div className="grid gap-3 sm:grid-cols-2"><button className="btn-secondary" onClick={loadStatus}>Check Engine Status</button><button className="btn-primary" onClick={runScan} disabled={loading || !authorized || !realOnly}>{loading ? "Scanning..." : "Run Scanner"}</button></div>
          {error && <p className="rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}
        </div>
        {status && <div className="card p-6"><p className="font-black text-white">Engine status</p><div className="mt-4"><JsonBlock value={status} /></div></div>}
      </div>
      <div className="space-y-5">
        {!result && <div className="card p-6"><p className="font-black text-white">Real-only scanner behavior</p><p className="mt-3 text-sm text-slate-400">The scanner only reports evidence from provided inputs, safe passive checks, or enabled providers. No fake score is generated for missing modules or disabled APIs.</p></div>}
        {result && <><ScoreCard label={result.module_score.risk_label} score={result.module_score.score} /><div className="card p-6"><p className="font-black text-white">Findings</p><div className="mt-4 space-y-4">{result.findings.length ? result.findings.map((finding) => <div key={finding.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><SeverityBadge severity={finding.severity} /><p className="mt-2 font-bold text-white">{finding.title}</p><p className="mt-2 text-sm text-slate-400">{finding.description}</p><p className="mt-2 text-xs text-cyan-100">Recommendation: {finding.recommendation}</p></div>) : <p className="text-sm text-slate-400">No findings from provided evidence.</p>}</div></div><div className="card p-6"><p className="font-black text-white">Evidence metadata</p><div className="mt-4"><JsonBlock value={result.scan_metadata || {}} /></div></div></>}
      </div>
    </div>
  </div>;
}
