"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mono max-h-72 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify(value, null, 2)}</pre>;
}

export function MonitoringLiteClient() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [dashboard, setDashboard] = useState<Record<string, any> | null>(null);
  const [projectName, setProjectName] = useState("RAADHANEX Monitored Project");
  const [chain, setChain] = useState("ethereum");
  const [address, setAddress] = useState("0x1111111111111111111111111111111111111111");
  const [ownership, setOwnership] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [createdConfig, setCreatedConfig] = useState<Record<string, any> | null>(null);
  const [manualAlertText, setManualAlertText] = useState("Owner/admin role change observed in deployment notes; review multisig evidence.");
  const [manualAlert, setManualAlert] = useState<Record<string, any> | null>(null);
  const [checkResult, setCheckResult] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setError(null);
    try {
      const [s, d] = await Promise.all([apiGet<Record<string, unknown>>("/monitoring/status"), apiGet<Record<string, any>>("/monitoring/dashboard")]);
      setStatus(s); setDashboard(d);
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to load monitoring status"); }
  }

  useEffect(() => { refresh(); }, []);

  async function createConfig() {
    setLoading(true); setError(null);
    try {
      const row = await apiPost<Record<string, any>>("/monitoring/configs", {
        project_name: projectName,
        contract_address: address,
        chain,
        watch_types: ["owner_changed", "role_granted", "pause", "unpause", "upgrade", "large_mint"],
        alert_channels: ["dashboard"],
        ownership_verified: ownership,
        authorization_confirmed: authorized,
        real_only_acknowledged: realOnly,
        notes: "Monitoring Lite MVP config. RPC must be configured separately for live read-only checks.",
      });
      setCreatedConfig(row); await refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "Create config failed"); }
    finally { setLoading(false); }
  }

  async function ingestManualAlert() {
    if (!createdConfig?.id) { setError("Create/select a config first"); return; }
    setLoading(true); setError(null);
    try {
      const row = await apiPost<Record<string, any>>("/monitoring/alerts/ingest", {
        config_id: createdConfig.id,
        event_type: "custom",
        severity: "medium",
        description: manualAlertText,
        source: "manual_admin",
        evidence: { source_note: "Manual/admin provided evidence only" },
        real_only_acknowledged: realOnly,
      });
      setManualAlert(row); await refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "Manual alert failed"); }
    finally { setLoading(false); }
  }

  async function runRpcCheck() {
    if (!createdConfig?.id) { setError("Create/select a config first"); return; }
    setLoading(true); setError(null);
    try {
      const result = await apiPost<Record<string, any>>("/monitoring/check", { config_id: createdConfig.id, real_only_acknowledged: realOnly });
      setCheckResult(result); await refresh();
    } catch (err) { setError(err instanceof Error ? err.message : "RPC check failed"); }
    finally { setLoading(false); }
  }

  return <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
    <div className="max-w-4xl">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Mega Phase C • Phase 23</p>
      <h1 className="mt-3 text-3xl font-black sm:text-5xl">Monitoring Lite</h1>
      <p className="mt-4 text-slate-400">Create real monitoring configs, store manual/admin alerts, and optionally run read-only RPC event checks when RPC env is configured. No fake live alerts, no wallet signing, no private keys.</p>
    </div>
    <div className="mt-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <div className="space-y-5">
        <div className="card space-y-4 p-6">
          <label className="block text-sm font-bold text-slate-200">Project name<input className="input mt-2" value={projectName} onChange={(e) => setProjectName(e.target.value)} /></label>
          <label className="block text-sm font-bold text-slate-200">Chain<select className="input mt-2" value={chain} onChange={(e) => setChain(e.target.value)}><option value="ethereum">Ethereum</option><option value="polygon">Polygon</option><option value="bsc">BNB Chain</option><option value="arbitrum">Arbitrum</option><option value="optimism">Optimism</option><option value="base">Base</option><option value="avalanche">Avalanche</option></select></label>
          <label className="block text-sm font-bold text-slate-200">Contract address<input className="input mt-2" value={address} onChange={(e) => setAddress(e.target.value)} /></label>
          <div className="space-y-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50">
            <label className="flex gap-3"><input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} /><span>I own this project or have authorization to monitor this contract.</span></label>
            <label className="flex gap-3"><input type="checkbox" checked={realOnly} onChange={(e) => setRealOnly(e.target.checked)} /><span>I understand disabled RPC/API means no fake live monitoring output.</span></label>
            <label className="flex gap-3"><input type="checkbox" checked={ownership} onChange={(e) => setOwnership(e.target.checked)} /><span>Ownership verification evidence exists for this monitoring config.</span></label>
          </div>
          <button className="btn-primary w-full" disabled={loading || !authorized || !realOnly} onClick={createConfig}>{loading ? "Working..." : "Create Monitoring Config"}</button>
        </div>
        <div className="card space-y-4 p-6">
          <p className="font-black text-white">Manual/admin alert ingest</p>
          <textarea className="input min-h-28" value={manualAlertText} onChange={(e) => setManualAlertText(e.target.value)} />
          <button className="btn-secondary w-full" disabled={loading || !createdConfig} onClick={ingestManualAlert}>Store Real Manual Alert</button>
          <button className="btn-secondary w-full" disabled={loading || !createdConfig} onClick={runRpcCheck}>Run Optional RPC Check</button>
          <p className="text-xs text-slate-400">RPC check only runs when MONITORING_ENABLED=true, MONITORING_RPC_ENABLED=true, and a chain RPC URL is configured.</p>
        </div>
        {error && <p className="rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</p>}
      </div>
      <div className="space-y-5">
        <div className="card p-6"><p className="font-black text-white">Status</p><div className="mt-4"><JsonBlock value={status} /></div></div>
        {createdConfig && <div className="card p-6"><p className="font-black text-white">Created config</p><div className="mt-4"><JsonBlock value={createdConfig} /></div></div>}
        {manualAlert && <div className="card p-6"><p className="font-black text-white">Manual alert record</p><div className="mt-4"><JsonBlock value={manualAlert} /></div></div>}
        {checkResult && <div className="card p-6"><p className="font-black text-white">RPC check result</p><div className="mt-4"><JsonBlock value={checkResult} /></div></div>}
        <div className="card p-6"><p className="font-black text-white">Dashboard summary</p><div className="mt-4"><JsonBlock value={dashboard} /></div></div>
      </div>
    </div>
  </div>;
}
