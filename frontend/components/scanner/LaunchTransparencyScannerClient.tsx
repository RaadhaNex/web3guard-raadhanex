"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";
import type { ScanResponse } from "@/lib/types";
import { ScoreCard } from "@/components/ui/ScoreCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

const sampleCode = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract LaunchToken {
  address public owner;
  address public treasury;
  uint256 public feeBps;
  mapping(address => bool) public blacklisted;
  modifier onlyOwner(){ require(msg.sender == owner, "owner"); _; }
  function mint(address to, uint256 amount) external onlyOwner {}
  function pause() external onlyOwner {}
  function setFee(uint256 newFeeBps) external onlyOwner { feeBps = newFeeBps; }
  function setBlacklist(address user, bool blocked) external onlyOwner { blacklisted[user] = blocked; }
  function withdraw() external onlyOwner { payable(treasury).transfer(address(this).balance); }
}`;

export function LaunchTransparencyScannerClient() {
  const [projectName, setProjectName] = useState("Token Launch Transparency");
  const [projectType, setProjectType] = useState("erc20");
  const [solidityCode, setSolidityCode] = useState(sampleCode);
  const [tokenomicsNotes, setTokenomicsNotes] = useState("Max supply not finalized. Owner can mint during launch campaign.");
  const [ownerPowerNotes, setOwnerPowerNotes] = useState("Owner can mint, pause, set fee, blacklist, and withdraw. Multisig not moved yet.");
  const [liquidityEvidence, setLiquidityEvidence] = useState("");
  const [metadataEvidence, setMetadataEvidence] = useState("");
  const [websiteText, setWebsiteText] = useState("Mint, claim, token launch, fee, treasury, roadmap");
  const [multisig, setMultisig] = useState<"unknown" | "yes" | "no">("no");
  const [timelock, setTimelock] = useState<"unknown" | "yes" | "no">("no");
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runScan() {
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await apiPost<ScanResponse>("/scan/launch-transparency", {
        project_name: projectName,
        project_type: projectType,
        solidity_code: solidityCode || null,
        website_text: websiteText || null,
        tokenomics_notes: tokenomicsNotes || null,
        liquidity_lock_evidence: liquidityEvidence || null,
        metadata_freeze_evidence: metadataEvidence || null,
        owner_power_notes: ownerPowerNotes || null,
        multisig_enabled: multisig === "unknown" ? null : multisig === "yes",
        timelock_enabled: timelock === "unknown" ? null : timelock === "yes",
        authorization_confirmed: authorized,
        real_only_acknowledged: realOnly,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Launch transparency scan failed");
    } finally { setLoading(false); }
  }

  const checklist = (result?.scan_metadata?.launch_checklist || []) as string[];
  const detected = (result?.scan_metadata?.detected_controls || []) as Array<Record<string, string>>;

  return <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
    <div className="max-w-4xl"><p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Mega Phase A • Phase 17</p><h1 className="mt-3 text-3xl font-black sm:text-5xl">Token / NFT / Launch Transparency Scanner</h1><p className="mt-4 text-slate-400">Detect founder disclosure gaps from real source, website copy, and notes. It never accuses a project of fraud and never certifies safety.</p></div>
    <div className="mt-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <div className="space-y-5">
        <div className="card p-6 space-y-4">
          <label className="block text-sm font-bold text-slate-200">Project name<input className="input mt-2" value={projectName} onChange={(e) => setProjectName(e.target.value)} /></label>
          <label className="block text-sm font-bold text-slate-200">Project type<select className="input mt-2" value={projectType} onChange={(e) => setProjectType(e.target.value)}><option value="erc20">ERC20 token</option><option value="nft">NFT mint</option><option value="staking">Staking</option><option value="dao">DAO</option><option value="presale">Presale</option><option value="airdrop">Airdrop/claim</option><option value="marketplace">Marketplace</option></select></label>
          <div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-bold text-slate-200">Multisig evidence<select className="input mt-2" value={multisig} onChange={(e) => setMultisig(e.target.value as "unknown" | "yes" | "no")}><option value="unknown">Unknown</option><option value="yes">Yes</option><option value="no">No</option></select></label><label className="text-sm font-bold text-slate-200">Timelock evidence<select className="input mt-2" value={timelock} onChange={(e) => setTimelock(e.target.value as "unknown" | "yes" | "no")}><option value="unknown">Unknown</option><option value="yes">Yes</option><option value="no">No</option></select></label></div>
          <label className="block text-sm font-bold text-slate-200">Tokenomics / launch notes<textarea className="input mt-2 min-h-24" value={tokenomicsNotes} onChange={(e) => setTokenomicsNotes(e.target.value)} /></label>
          <label className="block text-sm font-bold text-slate-200">Owner/admin power notes<textarea className="input mt-2 min-h-24" value={ownerPowerNotes} onChange={(e) => setOwnerPowerNotes(e.target.value)} /></label>
          <label className="block text-sm font-bold text-slate-200">Liquidity lock evidence optional<textarea className="input mt-2 min-h-20" value={liquidityEvidence} onChange={(e) => setLiquidityEvidence(e.target.value)} /></label>
          <label className="block text-sm font-bold text-slate-200">Metadata freeze evidence optional<textarea className="input mt-2 min-h-20" value={metadataEvidence} onChange={(e) => setMetadataEvidence(e.target.value)} /></label>
          <label className="block text-sm font-bold text-slate-200">Website/landing copy optional<textarea className="input mt-2 min-h-20" value={websiteText} onChange={(e) => setWebsiteText(e.target.value)} /></label>
        </div>
        <div className="card p-6"><label className="block text-sm font-bold text-slate-200">Solidity source optional<textarea className="mono mt-2 min-h-80 w-full rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-200 outline-none focus:border-cyan/60" value={solidityCode} onChange={(e) => setSolidityCode(e.target.value)} /></label><div className="mt-5 space-y-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50"><label className="flex gap-3"><input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} /><span>I own this project or have authorization to review launch transparency.</span></label><label className="flex gap-3"><input type="checkbox" checked={realOnly} onChange={(e) => setRealOnly(e.target.checked)} /><span>I understand this report uses only real provided evidence and is not a certified audit or legal advice.</span></label></div><button className="btn-primary mt-5 w-full" onClick={runScan} disabled={loading || !authorized || !realOnly}>{loading ? "Scanning..." : "Run Launch Transparency Scan"}</button>{error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}</div>
      </div>
      <div className="space-y-5">{!result && <div className="card p-6"><p className="font-black text-white">Real-only transparency mode</p><p className="mt-3 text-sm text-slate-400">Provide source, website copy, or founder notes. Missing evidence stays missing; app does not invent liquidity locks, multisig, timelock, or metadata freeze.</p></div>}{result && <><ScoreCard label={result.module_score.risk_label} score={result.module_score.score} /><div className="card p-6"><p className="font-black text-white">Project checklist</p><ul className="mt-4 space-y-2 text-sm text-slate-300">{checklist.map((item) => <li key={item}>• {item}</li>)}</ul></div><div className="card p-6"><p className="font-black text-white">Detected launch controls</p><div className="mt-4 space-y-3">{detected.length ? detected.map((item, i) => <div key={i} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3"><p className="font-bold text-white">{item.title}</p><p className="text-xs text-slate-500">{item.evidence}</p></div>) : <p className="text-sm text-slate-400">No privileged control detected from provided input.</p>}</div></div><div className="card p-6"><p className="font-black text-white">Findings</p><div className="mt-4 space-y-4">{result.findings.map((finding) => <div key={finding.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"><SeverityBadge severity={finding.severity} /><p className="mt-2 font-bold text-white">{finding.title}</p><p className="mt-2 text-sm text-slate-400">{finding.recommendation}</p></div>)}</div></div></>}</div>
    </div>
  </div>;
}
