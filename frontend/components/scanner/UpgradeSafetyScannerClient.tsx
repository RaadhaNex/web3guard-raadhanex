"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";
import type { ScanResponse } from "@/lib/types";
import { ScoreCard } from "@/components/ui/ScoreCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

const currentCode = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
contract UpgradeableToken is UUPSUpgradeable {
  address public owner;
  uint256 public feeBps;
  function initialize(address _owner) public { owner = _owner; }
  function _authorizeUpgrade(address newImplementation) internal {}
  function setFee(uint256 fee) external { feeBps = fee; }
}`;
const previousCode = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract UpgradeableTokenV1 {
  address public owner;
}`;

export function UpgradeSafetyScannerClient() {
  const [projectName, setProjectName] = useState("Upgrade Safety Project");
  const [currentSource, setCurrentSource] = useState(currentCode);
  const [previousSource, setPreviousSource] = useState(previousCode);
  const [proxyNotes, setProxyNotes] = useState("Proxy admin is currently a single hot wallet. Multisig migration planned later.");
  const [ownershipVerified, setOwnershipVerified] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  async function runScan() { setLoading(true); setError(null); setResult(null); try { const data = await apiPost<ScanResponse>("/scan/upgrade-safety", { project_name: projectName, current_code: currentSource, previous_code: previousSource || null, proxy_admin_notes: proxyNotes || null, ownership_verified: ownershipVerified, authorization_confirmed: authorized, real_only_acknowledged: realOnly }); setResult(data); } catch (err) { setError(err instanceof Error ? err.message : "Upgrade safety scan failed"); } finally { setLoading(false); } }
  const storage = result?.scan_metadata?.storage_layout_hint as { previous_variables?: unknown[]; current_variables?: unknown[]; changes?: unknown[] } | undefined;
  const proxy = (result?.scan_metadata?.proxy_types_detected || []) as Array<{ type?: string }>;
  return <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8"><div className="max-w-4xl"><p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Web3Guard AI</p><h1 className="mt-3 text-3xl font-black sm:text-5xl">Upgrade Safety Analyzer</h1><p className="mt-4 text-slate-400">Detect proxy hints, initializer issues, upgrade authorization evidence, and old/new storage-order changes. This is not a certified storage-layout proof.</p></div><div className="mt-8 grid gap-6 lg:grid-cols-2"><div className="card p-6"><label className="block text-sm font-bold text-slate-200">Project name<input className="input mt-2" value={projectName} onChange={(e) => setProjectName(e.target.value)} /></label><label className="mt-4 block text-sm font-bold text-slate-200">Current Solidity source<textarea className="mono mt-2 min-h-72 w-full rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-200 outline-none focus:border-cyan/60" value={currentSource} onChange={(e) => setCurrentSource(e.target.value)} /></label><label className="mt-4 block text-sm font-bold text-slate-200">Previous Solidity source optional<textarea className="mono mt-2 min-h-56 w-full rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-200 outline-none focus:border-cyan/60" value={previousSource} onChange={(e) => setPreviousSource(e.target.value)} /></label><label className="mt-4 block text-sm font-bold text-slate-200">Proxy admin / governance notes optional<textarea className="input mt-2 min-h-24" value={proxyNotes} onChange={(e) => setProxyNotes(e.target.value)} /></label><div className="mt-5 space-y-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50"><label className="flex gap-3"><input type="checkbox" checked={ownershipVerified} onChange={(e) => setOwnershipVerified(e.target.checked)} /><span>Ownership/admin evidence has been verified outside this scanner.</span></label><label className="flex gap-3"><input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} /><span>I own this project or have authorization to review upgrade safety.</span></label><label className="flex gap-3"><input type="checkbox" checked={realOnly} onChange={(e) => setRealOnly(e.target.checked)} /><span>I understand this does not perform an upgrade, connect wallet, or prove storage safety.</span></label></div><button className="btn-primary mt-5 w-full" onClick={runScan} disabled={loading || !authorized || !realOnly}>{loading ? "Analyzing..." : "Run Upgrade Safety Scan"}</button>{error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}</div><div className="space-y-5">{!result && <div className="card p-6"><p className="font-black text-white">Real-only upgrade mode</p><p className="mt-3 text-sm text-slate-400">Provide current source, and previous source when comparing upgrades. For final production upgrades, compiler storageLayout output + manual review are still required.</p></div>}{result && <><ScoreCard label={result.module_score.risk_label} score={result.module_score.score} /><div className="card p-6"><p className="font-black text-white">Proxy patterns</p><p className="mt-3 text-sm text-slate-400">{proxy.length ? proxy.map((item) => item.type).join(", ") : "No common proxy pattern detected from provided source."}</p></div><div className="card p-6"><p className="font-black text-white">Storage layout hint</p><p className="mt-3 text-sm text-slate-400">Previous vars: {storage?.previous_variables?.length || 0} • Current vars: {storage?.current_variables?.length || 0} • Changes: {storage?.changes?.length || 0}</p><p className="mt-3 text-xs text-amber-100">Compiler storageLayout output is still required for final proof.</p></div><div className="card p-6"><p className="font-black text-white">Findings</p><div className="mt-4 space-y-4">{result.findings.map((finding) => <div key={finding.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><SeverityBadge severity={finding.severity} /><p className="mt-2 font-bold text-white">{finding.title}</p><p className="mt-2 text-sm text-slate-400">{finding.recommendation}</p>{finding.affected_code && <pre className="mono mt-3 overflow-auto rounded-xl bg-black/30 p-3 text-xs text-slate-300">{finding.affected_code}</pre>}</div>)}</div></div></>}</div></div></div>;
}
