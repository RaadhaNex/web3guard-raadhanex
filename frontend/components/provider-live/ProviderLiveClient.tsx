"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { CommandEmptyState, CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";
import { StatusPill } from "@/components/ui/StatusPill";

type ProviderSurface = {
  key: string;
  name: string;
  status: string;
  configured: boolean;
  api_base?: string;
  backend_endpoint?: string;
  reuses_existing_scanner?: string;
  when_missing?: string;
  not_claimed?: string[];
  token_configured?: boolean;
  token_note?: string;
  source_matrix?: Array<{ key: string; name: string; status: string; requires_api_key: boolean; api_key_configured?: boolean }>;
};

type ProviderLiveStatus = {
  ok: boolean;
  version: string;
  provider_live_enabled: boolean;
  network_enabled: boolean;
  ready_count: number;
  total_count: number;
  readiness_label: string;
  surfaces: ProviderSurface[];
  limits: Record<string, number>;
  safe_env_to_add: string[];
  safety_boundaries: Record<string, boolean>;
};

type ExplorerSnapshot = {
  ok: boolean;
  status: string;
  source_available?: boolean;
  chain_id?: string;
  address?: string;
  contract_name?: string | null;
  compiler_version?: string | null;
  license_type?: string | null;
  source_hash?: string | null;
  abi_available?: boolean;
  abi_function_count?: number;
  source_metadata?: Record<string, unknown>;
  source_preview?: string | null;
  reason?: string;
  provider_error?: string;
  real_only_note?: string;
};

type GitHubCheck = {
  ok: boolean;
  status: string;
  repo?: Record<string, unknown>;
  root_file_hints?: string[];
  security_hints?: Record<string, boolean>;
  token_configured?: boolean;
  provider_error?: string;
  real_only_note?: string;
};

type AdvisoryResult = {
  ok: boolean;
  source: string;
  status: string;
  records: Array<Record<string, unknown>>;
  record_count?: number;
  reason?: string;
  provider_error?: string;
  real_only_note?: string;
};

function safeJson(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function SurfaceCard({ surface }: { surface: ProviderSurface }) {
  return (
    <article className="glass-tile p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.22em] text-slate-500">{surface.key.replaceAll("_", " ")}</p>
          <h3 className="mt-2 text-xl font-black text-white">{surface.name}</h3>
        </div>
        <StatusPill status={surface.status} />
      </div>
      <div className="mt-4 grid gap-2 text-xs text-slate-400 sm:grid-cols-2">
        <p><strong className="text-white">Configured:</strong> {surface.configured ? "yes" : "no"}</p>
        <p><strong className="text-white">When missing:</strong> {surface.when_missing || "Not Assessed"}</p>
        {surface.api_base ? <p className="break-all sm:col-span-2"><strong className="text-white">API:</strong> {surface.api_base}</p> : null}
        {surface.backend_endpoint ? <p className="sm:col-span-2"><strong className="text-white">Endpoint:</strong> <span className="mono">{surface.backend_endpoint}</span></p> : null}
        {surface.reuses_existing_scanner ? <p className="sm:col-span-2"><strong className="text-white">Deep scan:</strong> <span className="mono">{surface.reuses_existing_scanner}</span></p> : null}
        {typeof surface.token_configured === "boolean" ? <p><strong className="text-white">Token:</strong> {surface.token_configured ? "configured" : "optional/missing"}</p> : null}
      </div>
      {surface.token_note ? <p className="mt-3 text-xs leading-5 text-slate-500">{surface.token_note}</p> : null}
      {surface.source_matrix?.length ? (
        <div className="mt-4 grid gap-2">
          {surface.source_matrix.map((item) => (
            <div key={item.key} className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-white/10 bg-black/20 px-3 py-2 text-xs">
              <span className="font-bold text-slate-300">{item.name}</span>
              <StatusPill status={item.status} />
            </div>
          ))}
        </div>
      ) : null}
      {surface.not_claimed?.length ? (
        <ul className="mt-4 grid gap-1 text-xs text-slate-500">
          {surface.not_claimed.slice(0, 4).map((item) => <li key={item}>• {item}</li>)}
        </ul>
      ) : null}
    </article>
  );
}

export function ProviderLiveClient() {
  const [status, setStatus] = useState<ProviderLiveStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [realOnly, setRealOnly] = useState(true);

  const [chain, setChain] = useState("ethereum");
  const [address, setAddress] = useState("0x0000000000000000000000000000000000000000");
  const [includeAbi, setIncludeAbi] = useState(false);
  const [explorerResult, setExplorerResult] = useState<ExplorerSnapshot | null>(null);

  const [repoUrl, setRepoUrl] = useState("https://github.com/openzeppelin/openzeppelin-contracts");
  const [branch, setBranch] = useState("");
  const [githubResult, setGithubResult] = useState<GitHubCheck | null>(null);

  const [advisorySource, setAdvisorySource] = useState("osv");
  const [advisoryQuery, setAdvisoryQuery] = useState("CVE-2024-3094");
  const [ecosystem, setEcosystem] = useState("npm");
  const [packageName, setPackageName] = useState("");
  const [advisoryResult, setAdvisoryResult] = useState<AdvisoryResult | null>(null);

  async function loadStatus() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<ProviderLiveStatus>("/provider-live/status");
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load provider live status.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadStatus();
  }, []);

  const boundaryText = useMemo(() => {
    if (!status) return "Real-only provider layer";
    const enabled = Object.entries(status.safety_boundaries).filter(([, value]) => value).length;
    return `${enabled} safety boundaries active`;
  }, [status]);

  async function fetchExplorer(event: FormEvent) {
    event.preventDefault();
    setActionLoading("explorer");
    setError(null);
    setExplorerResult(null);
    try {
      const data = await apiPost<ExplorerSnapshot>("/provider-live/explorer/source", {
        chain,
        address,
        include_abi: includeAbi,
        real_only_acknowledged: realOnly,
      });
      setExplorerResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Explorer source fetch failed.");
    } finally {
      setActionLoading(null);
    }
  }

  async function checkGithub(event: FormEvent) {
    event.preventDefault();
    setActionLoading("github");
    setError(null);
    setGithubResult(null);
    try {
      const data = await apiPost<GitHubCheck>("/provider-live/github/repo-check", {
        repo_url: repoUrl,
        branch: branch || null,
        authorization_confirmed: true,
        real_only_acknowledged: realOnly,
      });
      setGithubResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "GitHub repo check failed.");
    } finally {
      setActionLoading(null);
    }
  }

  async function searchAdvisory(event: FormEvent) {
    event.preventDefault();
    setActionLoading("advisory");
    setError(null);
    setAdvisoryResult(null);
    try {
      const data = await apiPost<AdvisoryResult>("/provider-live/advisory/search", {
        source: advisorySource,
        query: advisoryQuery || null,
        ecosystem: ecosystem || null,
        package_name: packageName || null,
        real_only_acknowledged: realOnly,
      });
      setAdvisoryResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Advisory provider search failed.");
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) return <CommandLoadingState label="Loading provider live status..." />;
  if (error && !status) {
    return (
      <div className="mt-8 grid gap-4">
        <CommandNotice tone="warning" title="Provider live status could not load" text={error} />
        <button type="button" className="btn-secondary w-fit" onClick={() => void loadStatus()}>Retry</button>
      </div>
    );
  }
  if (!status) return <CommandEmptyState title="No provider live data" text="The backend did not return provider live integration data." />;

  return (
    <section className="mt-8 space-y-8">
      <div className="grid gap-4 md:grid-cols-4">
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Ready providers</p>
          <p className="mt-2 text-3xl font-black text-white">{status.ready_count}/{status.total_count}</p>
          <p className="mt-2 text-sm text-slate-400">{status.readiness_label}</p>
        </div>
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Network calls</p>
          <p className="mt-2 text-2xl font-black text-white">{status.network_enabled ? "Enabled" : "Disabled"}</p>
          <p className="mt-2 text-sm text-slate-400">Live requests only happen after explicit action.</p>
        </div>
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Boundary</p>
          <p className="mt-2 text-2xl font-black text-white">No fake data</p>
          <p className="mt-2 text-sm text-slate-400">{boundaryText}</p>
        </div>
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Deeper scanners</p>
          <Link href="/provider-readiness" className="mt-2 inline-flex text-2xl font-black text-cyan">Provider readiness →</Link>
          <p className="mt-2 text-sm text-slate-400">The provider readiness matrix still stays available.</p>
        </div>
      </div>

      {error ? <CommandNotice tone="warning" title="Action warning" text={error} /> : null}

      <div className="grid gap-5 lg:grid-cols-2">
        {status.surfaces.map((surface) => <SurfaceCard key={surface.key} surface={surface} />)}
      </div>

      <div className="glass-tile p-6">
        <p className="section-label">Live action acknowledgement</p>
        <label className="mt-4 flex gap-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm text-amber-50">
          <input type="checkbox" checked={realOnly} onChange={(event) => setRealOnly(event.target.checked)} />
          <span>I understand missing providers/tools must show Needs API Key / Provider Not Configured / Manual / Not Assessed. No fake output should be created.</span>
        </label>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <form onSubmit={fetchExplorer} className="glass-tile p-6">
          <p className="section-label">Explorer verified source</p>
          <h2 className="mt-2 text-2xl font-black text-white">Fetch source snapshot</h2>
          <label className="mt-5 block text-sm font-bold text-slate-300">Chain
            <input className="input mt-2" value={chain} onChange={(event) => setChain(event.target.value)} />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">Contract address
            <input className="input mt-2" value={address} onChange={(event) => setAddress(event.target.value)} />
          </label>
          <label className="mt-4 flex gap-2 text-sm font-bold text-slate-300">
            <input type="checkbox" checked={includeAbi} onChange={(event) => setIncludeAbi(event.target.checked)} /> Include ABI summary
          </label>
          <button className="btn-primary mt-5" disabled={!realOnly || actionLoading === "explorer"} type="submit">
            {actionLoading === "explorer" ? "Fetching..." : "Fetch verified source"}
          </button>
          {explorerResult ? (
            <div className="mt-5 rounded-2xl border border-white/10 bg-black/25 p-4">
              <StatusPill status={explorerResult.status} />
              <p className="mt-3 text-sm text-slate-300">Source available: {explorerResult.source_available ? "yes" : "no"}</p>
              {explorerResult.contract_name ? <p className="mt-2 text-sm text-slate-400">Contract: {explorerResult.contract_name}</p> : null}
              {explorerResult.reason || explorerResult.provider_error ? <p className="mt-2 text-sm text-amber-100">{explorerResult.reason || explorerResult.provider_error}</p> : null}
              <pre className="mono mt-4 max-h-72 overflow-auto rounded-2xl bg-black/40 p-3 text-xs text-slate-300">{safeJson(explorerResult)}</pre>
            </div>
          ) : null}
        </form>

        <form onSubmit={checkGithub} className="glass-tile p-6">
          <p className="section-label">GitHub provider</p>
          <h2 className="mt-2 text-2xl font-black text-white">Read-only repo metadata</h2>
          <label className="mt-5 block text-sm font-bold text-slate-300">Repository URL
            <input className="input mt-2" value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">Branch optional
            <input className="input mt-2" value={branch} onChange={(event) => setBranch(event.target.value)} placeholder="default branch" />
          </label>
          <button className="btn-primary mt-5" disabled={!realOnly || actionLoading === "github"} type="submit">
            {actionLoading === "github" ? "Checking..." : "Check GitHub metadata"}
          </button>
          {githubResult ? (
            <div className="mt-5 rounded-2xl border border-white/10 bg-black/25 p-4">
              <StatusPill status={githubResult.status} />
              {githubResult.provider_error ? <p className="mt-3 text-sm text-amber-100">{githubResult.provider_error}</p> : null}
              <pre className="mono mt-4 max-h-72 overflow-auto rounded-2xl bg-black/40 p-3 text-xs text-slate-300">{safeJson(githubResult)}</pre>
            </div>
          ) : null}
        </form>

        <form onSubmit={searchAdvisory} className="glass-tile p-6">
          <p className="section-label">Advisory source</p>
          <h2 className="mt-2 text-2xl font-black text-white">Search upstream advisory</h2>
          <label className="mt-5 block text-sm font-bold text-slate-300">Source
            <select className="input mt-2" value={advisorySource} onChange={(event) => setAdvisorySource(event.target.value)}>
              <option value="osv">OSV</option>
              <option value="nvd">NVD</option>
              <option value="github_advisory">GitHub Advisory</option>
              <option value="cisa_kev">CISA KEV</option>
            </select>
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">CVE / keyword
            <input className="input mt-2" value={advisoryQuery} onChange={(event) => setAdvisoryQuery(event.target.value)} />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">Ecosystem
            <input className="input mt-2" value={ecosystem} onChange={(event) => setEcosystem(event.target.value)} placeholder="npm, PyPI, Go, crates.io" />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">Package optional
            <input className="input mt-2" value={packageName} onChange={(event) => setPackageName(event.target.value)} placeholder="lodash" />
          </label>
          <button className="btn-primary mt-5" disabled={!realOnly || actionLoading === "advisory"} type="submit">
            {actionLoading === "advisory" ? "Searching..." : "Search advisory source"}
          </button>
          {advisoryResult ? (
            <div className="mt-5 rounded-2xl border border-white/10 bg-black/25 p-4">
              <StatusPill status={advisoryResult.status} />
              <p className="mt-3 text-sm text-slate-300">Records: {advisoryResult.record_count ?? advisoryResult.records.length}</p>
              {advisoryResult.reason || advisoryResult.provider_error ? <p className="mt-2 text-sm text-amber-100">{advisoryResult.reason || advisoryResult.provider_error}</p> : null}
              <pre className="mono mt-4 max-h-72 overflow-auto rounded-2xl bg-black/40 p-3 text-xs text-slate-300">{safeJson(advisoryResult)}</pre>
            </div>
          ) : null}
        </form>
      </div>

      <div className="glass-tile p-6">
        <p className="section-label">Safe env checklist</p>
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {status.safe_env_to_add.map((item) => <p key={item} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300">{item}</p>)}
        </div>
      </div>
    </section>
  );
}
