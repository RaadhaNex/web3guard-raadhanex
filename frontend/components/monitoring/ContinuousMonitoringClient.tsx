"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";

type JsonRecord = Record<string, any>;

const checks = [
  ["stale_report", "Stale report"],
  ["scan_age", "Scan age"],
  ["website_passive", "Website passive drift"],
  ["github_repo_change", "GitHub repo drift"],
  ["sentinel_alert_queue", "Sentinel alert queue"],
  ["rpc_event_monitoring", "RPC event records"],
];

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mono max-h-80 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{JSON.stringify(value, null, 2)}</pre>;
}

function StatusBadge({ value }: { value: string }) {
  const clean = value.toLowerCase();
  const cls = clean.includes("critical") || clean.includes("high")
    ? "badge-red"
    : clean.includes("medium")
      ? "badge-amber"
      : clean.includes("active") || clean.includes("ok") || clean.includes("assessed")
        ? "badge-green"
        : "badge-cyan";
  return <span className={`badge ${cls}`}>{value}</span>;
}

export function ContinuousMonitoringClient({ adminMode = false }: { adminMode?: boolean }) {
  const [status, setStatus] = useState<JsonRecord | null>(null);
  const [dashboard, setDashboard] = useState<JsonRecord | null>(null);
  const [configs, setConfigs] = useState<JsonRecord[]>([]);
  const [alerts, setAlerts] = useState<JsonRecord[]>([]);
  const [createdConfig, setCreatedConfig] = useState<JsonRecord | null>(null);
  const [recheckResult, setRecheckResult] = useState<JsonRecord | null>(null);
  const [userId, setUserId] = useState("local-demo-user");
  const [projectName, setProjectName] = useState("Web3Guard monitored project");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [githubRepoUrl, setGithubRepoUrl] = useState("");
  const [contractAddress, setContractAddress] = useState("");
  const [chain, setChain] = useState("ethereum");
  const [cadence, setCadence] = useState("manual");
  const [selectedChecks, setSelectedChecks] = useState<string[]>(checks.map(([key]) => key));
  const [authorized, setAuthorized] = useState(false);
  const [realOnly, setRealOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedConfigId = useMemo(() => createdConfig?.id || configs[0]?.id || "", [createdConfig, configs]);

  async function refresh() {
    setError(null);
    try {
      const [s, c, a, d] = await Promise.all([
        apiGet<JsonRecord>("/continuous-monitoring/status"),
        apiGet<{ configs: JsonRecord[] }>(`/continuous-monitoring/configs${adminMode ? "" : `?user_id=${encodeURIComponent(userId)}`}`),
        apiGet<{ alerts: JsonRecord[] }>(`/continuous-monitoring/alerts${adminMode ? "" : `?user_id=${encodeURIComponent(userId)}`}`),
        apiGet<JsonRecord>(adminMode ? "/continuous-monitoring/admin" : `/continuous-monitoring/user?user_id=${encodeURIComponent(userId)}`),
      ]);
      setStatus(s);
      setConfigs(c.configs || []);
      setAlerts(a.alerts || []);
      setDashboard(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load continuous monitoring data");
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [adminMode]);

  function toggleCheck(key: string) {
    setSelectedChecks((current) => current.includes(key) ? current.filter((item) => item !== key) : [...current, key]);
  }

  async function createConfig() {
    setLoading(true);
    setError(null);
    try {
      const row = await apiPost<JsonRecord>("/continuous-monitoring/configs", {
        user_id: userId,
        project_name: projectName,
        website_url: websiteUrl || null,
        github_repo_url: githubRepoUrl || null,
        contract_address: contractAddress || null,
        chain,
        cadence,
        checks: selectedChecks,
        alert_channels: ["dashboard"],
        authorization_confirmed: authorized,
        real_only_acknowledged: realOnly,
        notes: "Continuous Monitoring Lite config. External scheduler/network checks must be configured separately.",
      });
      setCreatedConfig(row);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create config failed");
    } finally {
      setLoading(false);
    }
  }

  async function runRecheck(force = true) {
    if (!selectedConfigId) {
      setError("Create or select a monitoring config first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await apiPost<JsonRecord>("/continuous-monitoring/recheck", {
        config_id: selectedConfigId,
        user_id: adminMode ? undefined : userId,
        force,
        real_only_acknowledged: realOnly,
      });
      setRecheckResult(result);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Recheck failed");
    } finally {
      setLoading(false);
    }
  }

  async function runDue() {
    setLoading(true);
    setError(null);
    try {
      const result = await apiPost<JsonRecord>("/continuous-monitoring/recheck-due", {
        limit: 10,
        real_only_acknowledged: realOnly,
      });
      setRecheckResult(result);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Due recheck failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="quantum-module-screen mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-4xl">
          <p className="section-label">Continuous Monitoring Lite</p>
          <h1 className="mt-3 text-3xl font-black sm:text-5xl">{adminMode ? "Admin monitoring intelligence" : "User project monitoring"}</h1>
          <p className="mt-4 text-sm leading-7 text-slate-400 sm:text-base">
            Opt-in monitoring configs, manual or scheduler-triggered rechecks, stale report detection, passive website drift readiness, Sentinel alert queue visibility, and clear no-fake-alert status.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href={adminMode ? "/continuous-monitoring" : "/continuous-monitoring/admin"} className="btn-secondary">
            {adminMode ? "User monitoring" : "Admin board"}
          </Link>
          <Link href="/sentinel" className="btn-secondary">Sentinel</Link>
          <Link href="/dashboard" className="btn-secondary">Dashboard</Link>
        </div>
      </div>

      <section className="mt-8 grid gap-4 md:grid-cols-4">
        <div className="stat-slab p-4"><p className="text-xs uppercase tracking-[0.2em] text-slate-500">Configs</p><p className="mt-2 text-2xl font-black text-white">{dashboard?.config_count ?? configs.length}</p></div>
        <div className="stat-slab p-4"><p className="text-xs uppercase tracking-[0.2em] text-slate-500">Alerts</p><p className="mt-2 text-2xl font-black text-white">{dashboard?.alert_count ?? alerts.length}</p></div>
        <div className="stat-slab p-4"><p className="text-xs uppercase tracking-[0.2em] text-slate-500">Due configs</p><p className="mt-2 text-2xl font-black text-white">{dashboard?.due_configs?.length ?? status?.due_config_count ?? 0}</p></div>
        <div className="stat-slab p-4"><p className="text-xs uppercase tracking-[0.2em] text-slate-500">Scheduler</p><p className="mt-2 text-lg font-black text-white">{status?.scheduler_configured ? "Configured" : "Manual"}</p></div>
      </section>

      {error ? <div className="mt-6 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</div> : null}

      <section className="mt-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-5">
          {!adminMode ? (
            <div className="glass-tile p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-2xl font-black">Create monitoring config</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-400">Only monitor projects you own or are authorized to monitor. Network/provider checks remain Not Assessed unless explicitly enabled.</p>
                </div>
                <StatusBadge value="Owner authorized only" />
              </div>

              <div className="mt-5 grid gap-4">
                <label className="grid gap-2 text-sm font-bold text-slate-300">User ID<input className="input" value={userId} onChange={(event) => setUserId(event.target.value)} /></label>
                <label className="grid gap-2 text-sm font-bold text-slate-300">Project name<input className="input" value={projectName} onChange={(event) => setProjectName(event.target.value)} /></label>
                <label className="grid gap-2 text-sm font-bold text-slate-300">Website URL<input className="input" value={websiteUrl} onChange={(event) => setWebsiteUrl(event.target.value)} placeholder="https://yourproject.com" /></label>
                <label className="grid gap-2 text-sm font-bold text-slate-300">GitHub repo URL<input className="input" value={githubRepoUrl} onChange={(event) => setGithubRepoUrl(event.target.value)} placeholder="https://github.com/org/repo" /></label>
                <label className="grid gap-2 text-sm font-bold text-slate-300">Contract address<input className="input" value={contractAddress} onChange={(event) => setContractAddress(event.target.value)} placeholder="0x... optional" /></label>
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="grid gap-2 text-sm font-bold text-slate-300">Chain<select className="input" value={chain} onChange={(event) => setChain(event.target.value)}><option value="ethereum">Ethereum</option><option value="polygon">Polygon</option><option value="base">Base</option><option value="bsc">BNB Chain</option><option value="arbitrum">Arbitrum</option><option value="optimism">Optimism</option></select></label>
                  <label className="grid gap-2 text-sm font-bold text-slate-300">Cadence<select className="input" value={cadence} onChange={(event) => setCadence(event.target.value)}><option value="manual">Manual</option><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option></select></label>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <p className="text-sm font-black text-white">Checks</p>
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
                    {checks.map(([key, label]) => (
                      <label key={key} className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-slate-300">
                        <input type="checkbox" checked={selectedChecks.includes(key)} onChange={() => toggleCheck(key)} />
                        <span>{label}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="space-y-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50">
                  <label className="flex gap-3"><input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} /><span>I own this project or have authorization to monitor it.</span></label>
                  <label className="flex gap-3"><input type="checkbox" checked={realOnly} onChange={(event) => setRealOnly(event.target.checked)} /><span>I understand disabled network/API/scheduler settings produce Not Assessed, not fake alerts.</span></label>
                </div>
                <button className="btn-primary w-full" disabled={loading || !authorized || !realOnly} onClick={createConfig}>{loading ? "Working..." : "Create config"}</button>
              </div>
            </div>
          ) : null}

          <div className="glass-tile p-6">
            <h2 className="text-2xl font-black">Recheck controls</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Manual checks are safe and real-only. Due checks require an external scheduler/cron to call the API; the app does not pretend a scheduler is running.</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <button className="btn-secondary" disabled={loading || !selectedConfigId} onClick={() => void runRecheck(true)}>Run selected recheck</button>
              <button className="btn-secondary" disabled={loading} onClick={() => void runDue()}>Run due configs</button>
            </div>
            <p className="mt-3 text-xs text-slate-500">Selected config: {selectedConfigId || "none"}</p>
          </div>
        </div>

        <div className="space-y-5">
          <div className="glass-tile p-6">
            <div className="flex items-center justify-between gap-3"><h2 className="text-2xl font-black">Monitoring status</h2><StatusBadge value={status?.network_checks_enabled ? "Network enabled" : "Network disabled"} /></div>
            <div className="mt-4"><JsonBlock value={status} /></div>
          </div>
          {recheckResult ? <div className="glass-tile p-6"><h2 className="text-2xl font-black">Latest recheck result</h2><div className="mt-4"><JsonBlock value={recheckResult} /></div></div> : null}
        </div>
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="glass-tile p-6">
          <h2 className="text-2xl font-black">Configs</h2>
          <div className="mt-4 grid gap-3">
            {configs.length ? configs.slice(0, 10).map((config) => (
              <div key={config.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div className="flex flex-wrap items-center justify-between gap-3"><p className="font-black text-white">{config.project_name}</p><StatusBadge value={config.cadence || "manual"} /></div>
                <p className="mt-2 text-xs text-slate-500">{config.id} · next due {config.next_due_at || "manual only"}</p>
                <p className="mt-2 text-sm text-slate-400">{config.website_url || "No website"} · {config.github_repo_url || "No GitHub repo"}</p>
              </div>
            )) : <p className="text-sm text-slate-500">No continuous monitoring configs saved yet.</p>}
          </div>
        </div>

        <div className="glass-tile p-6">
          <h2 className="text-2xl font-black">Alerts</h2>
          <div className="mt-4 grid gap-3">
            {alerts.length ? alerts.slice(0, 10).map((alert) => (
              <div key={alert.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <div className="flex flex-wrap items-center justify-between gap-3"><p className="font-black text-white">{alert.title}</p><StatusBadge value={alert.severity || "info"} /></div>
                <p className="mt-2 text-sm leading-6 text-slate-400">{alert.description}</p>
                <p className="mt-2 text-xs text-slate-500">{alert.check_type} · {alert.created_at}</p>
              </div>
            )) : <p className="text-sm text-slate-500">No real monitoring alerts recorded yet.</p>}
          </div>
        </div>
      </section>

      <section className="mt-8 glass-tile p-6">
        <h2 className="text-2xl font-black">Dashboard payload</h2>
        <div className="mt-4"><JsonBlock value={dashboard} /></div>
      </section>
    </main>
  );
}
