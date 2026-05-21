"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { CommandEmptyState, CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";
import { StatusPill } from "@/components/ui/StatusPill";

type TrustSurface = {
  key: string;
  name: string;
  status: string;
  endpoint: string;
  stores: string[];
  not_claimed: string[];
};

type TrustMetricsStatus = {
  ok: boolean;
  version: string;
  readiness_label: string;
  surfaces: TrustSurface[];
  safe_public_wording: string;
  real_only_note: string;
  safety_boundaries: Record<string, boolean>;
};

type Snapshot = {
  id: string;
  project_id?: string | null;
  project_name?: string | null;
  external_advisory_count: number;
  web3guard_generated_finding_count: number;
  community_review_count: number;
  disclosure_count: number;
  resolved_disclosure_count: number;
  unresolved_disclosure_count: number;
  public_metric_note: string;
  created_at: string;
};

type AdvisoryMapping = {
  id: string;
  project_id: string;
  advisory_source: string;
  advisory_id: string;
  advisory_title?: string | null;
  severity: string;
  affected_component?: string | null;
  mapping_status: string;
  created_at: string;
};

type DisclosureRecord = {
  id: string;
  project_id: string;
  origin: string;
  title: string;
  severity: string;
  status: string;
  recipient?: string | null;
  public_reference?: string | null;
  created_at: string;
};

type PublicSummary = {
  ok: boolean;
  latest_snapshot?: Snapshot | null;
  metrics: {
    snapshot_count: number;
    advisory_mapping_count: number;
    disclosure_count: number;
    external_advisory_mapping_count: number;
    web3guard_generated_finding_count: number;
    community_review_count: number;
    resolved_disclosure_count: number;
    open_disclosure_count: number;
    disclosure_status_counts: Record<string, number>;
    disclosure_origin_counts: Record<string, number>;
    advisory_severity_counts: Record<string, number>;
  };
  safe_public_wording: string;
  not_claimed: string[];
};

type WordingCheck = {
  ok: boolean;
  safe: boolean;
  blocked_claim?: string | null;
  detected_cves: string[];
  safe_rewrite_hint?: string | null;
};

type SnapshotResponse = { ok: boolean; snapshot: Snapshot };
type MappingResponse = { ok: boolean; mapping: AdvisoryMapping };
type DisclosureResponse = { ok: boolean; disclosure: DisclosureRecord };
type SnapshotListResponse = { ok: boolean; snapshots: Snapshot[]; count: number };
type MappingListResponse = { ok: boolean; advisory_mappings: AdvisoryMapping[]; count: number };
type DisclosureListResponse = { ok: boolean; disclosures: DisclosureRecord[]; count: number };

const OWNER_ID = "local-demo-user";

function safeJson(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function SurfaceCard({ surface }: { surface: TrustSurface }) {
  return (
    <article className="glass-tile p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.22em] text-slate-500">{surface.key.replaceAll("_", " ")}</p>
          <h3 className="mt-2 text-xl font-black text-white">{surface.name}</h3>
        </div>
        <StatusPill status={surface.status} />
      </div>
      <p className="mono mt-3 text-xs text-cyan">{surface.endpoint}</p>
      <div className="mt-4 grid gap-2 text-xs text-slate-400 sm:grid-cols-2">
        {surface.stores.map((item) => (
          <p key={item} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">{item}</p>
        ))}
      </div>
      <ul className="mt-4 grid gap-1 text-xs text-slate-500">
        {surface.not_claimed.map((item) => <li key={item}>• {item}</li>)}
      </ul>
    </article>
  );
}

function MetricCard({ label, value, note }: { label: string; value: number; note: string }) {
  return (
    <div className="stat-slab p-5">
      <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-black text-white">{value}</p>
      <p className="mt-2 text-sm text-slate-400">{note}</p>
    </div>
  );
}

export function TrustMetricsClient() {
  const [status, setStatus] = useState<TrustMetricsStatus | null>(null);
  const [summary, setSummary] = useState<PublicSummary | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [mappings, setMappings] = useState<AdvisoryMapping[]>([]);
  const [disclosures, setDisclosures] = useState<DisclosureRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [projectId, setProjectId] = useState("local-project");
  const [projectName, setProjectName] = useState("Local Launch Project");
  const [externalCount, setExternalCount] = useState(1);
  const [web3guardCount, setWeb3guardCount] = useState(0);
  const [communityCount, setCommunityCount] = useState(1);
  const [disclosureCount, setDisclosureCount] = useState(1);
  const [resolvedCount, setResolvedCount] = useState(0);
  const [metricNote, setMetricNote] = useState("Public transparency metric only. Not a certified audit or safety guarantee.");

  const [advisorySource, setAdvisorySource] = useState("osv");
  const [advisoryId, setAdvisoryId] = useState("GHSA-example-1234");
  const [advisoryTitle, setAdvisoryTitle] = useState("Example dependency advisory mapping");
  const [severity, setSeverity] = useState("medium");
  const [mappingStatus, setMappingStatus] = useState("needs_review");
  const [affectedComponent, setAffectedComponent] = useState("frontend dependency");

  const [disclosureOrigin, setDisclosureOrigin] = useState("external_advisory");
  const [disclosureTitle, setDisclosureTitle] = useState("Manual disclosure tracking item");
  const [disclosureStatus, setDisclosureStatus] = useState("draft");
  const [recipient, setRecipient] = useState("project owner / security contact");
  const [disclosureSummary, setDisclosureSummary] = useState("Manual record for owner-reviewed advisory or finding lifecycle.");

  const [wordingText, setWordingText] = useState("External advisories are mapped separately from Web3Guard-generated findings.");
  const [wordingResult, setWordingResult] = useState<WordingCheck | null>(null);

  async function loadAll() {
    setLoading(true);
    setError(null);
    try {
      const [statusData, summaryData, snapshotData, mappingData, disclosureData] = await Promise.all([
        apiGet<TrustMetricsStatus>("/trust-metrics/status"),
        apiGet<PublicSummary>(`/trust-metrics/public-summary?owner_user_id=${OWNER_ID}&project_id=${encodeURIComponent(projectId)}`),
        apiGet<SnapshotListResponse>(`/trust-metrics/snapshots?owner_user_id=${OWNER_ID}&project_id=${encodeURIComponent(projectId)}&limit=10`),
        apiGet<MappingListResponse>(`/trust-metrics/advisory-mappings?owner_user_id=${OWNER_ID}&project_id=${encodeURIComponent(projectId)}&limit=10`),
        apiGet<DisclosureListResponse>(`/trust-metrics/disclosures?owner_user_id=${OWNER_ID}&project_id=${encodeURIComponent(projectId)}&limit=10`),
      ]);
      setStatus(statusData);
      setSummary(summaryData);
      setSnapshots(snapshotData.snapshots);
      setMappings(mappingData.advisory_mappings);
      setDisclosures(disclosureData.disclosures);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load trust metrics engine.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeBoundaryCount = useMemo(() => {
    if (!status) return 0;
    return Object.values(status.safety_boundaries).filter(Boolean).length;
  }, [status]);

  async function refreshProjectData(nextProjectId = projectId) {
    const [summaryData, snapshotData, mappingData, disclosureData] = await Promise.all([
      apiGet<PublicSummary>(`/trust-metrics/public-summary?owner_user_id=${OWNER_ID}&project_id=${encodeURIComponent(nextProjectId)}`),
      apiGet<SnapshotListResponse>(`/trust-metrics/snapshots?owner_user_id=${OWNER_ID}&project_id=${encodeURIComponent(nextProjectId)}&limit=10`),
      apiGet<MappingListResponse>(`/trust-metrics/advisory-mappings?owner_user_id=${OWNER_ID}&project_id=${encodeURIComponent(nextProjectId)}&limit=10`),
      apiGet<DisclosureListResponse>(`/trust-metrics/disclosures?owner_user_id=${OWNER_ID}&project_id=${encodeURIComponent(nextProjectId)}&limit=10`),
    ]);
    setSummary(summaryData);
    setSnapshots(snapshotData.snapshots);
    setMappings(mappingData.advisory_mappings);
    setDisclosures(disclosureData.disclosures);
  }

  async function saveSnapshot(event: FormEvent) {
    event.preventDefault();
    setActionLoading("snapshot");
    setError(null);
    setNotice(null);
    try {
      await apiPost<SnapshotResponse>("/trust-metrics/snapshots", {
        owner_user_id: OWNER_ID,
        project_id: projectId,
        project_name: projectName,
        external_advisory_count: externalCount,
        web3guard_generated_finding_count: web3guardCount,
        community_review_count: communityCount,
        disclosure_count: disclosureCount,
        resolved_disclosure_count: resolvedCount,
        public_metric_note: metricNote,
        metric_sources: ["manual evidence ledger", "security passport", "public trust page"],
        safe_public_metrics_acknowledged: true,
      });
      await refreshProjectData();
      setNotice("Metric snapshot saved with safe public wording.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save metric snapshot.");
    } finally {
      setActionLoading(null);
    }
  }

  async function saveMapping(event: FormEvent) {
    event.preventDefault();
    setActionLoading("mapping");
    setError(null);
    setNotice(null);
    try {
      await apiPost<MappingResponse>("/trust-metrics/advisory-mappings", {
        owner_user_id: OWNER_ID,
        project_id: projectId,
        project_name: projectName,
        advisory_source: advisorySource,
        advisory_id: advisoryId,
        advisory_title: advisoryTitle,
        severity,
        affected_component: affectedComponent,
        mapping_status: mappingStatus,
        authorization_confirmed: true,
      });
      await refreshProjectData();
      setNotice("Advisory mapping saved without claiming discovery or audit status.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save advisory mapping.");
    } finally {
      setActionLoading(null);
    }
  }

  async function saveDisclosure(event: FormEvent) {
    event.preventDefault();
    setActionLoading("disclosure");
    setError(null);
    setNotice(null);
    try {
      await apiPost<DisclosureResponse>("/trust-metrics/disclosures", {
        owner_user_id: OWNER_ID,
        project_id: projectId,
        project_name: projectName,
        origin: disclosureOrigin,
        title: disclosureTitle,
        severity,
        status: disclosureStatus,
        recipient,
        summary: disclosureSummary,
        authorization_confirmed: true,
        manual_send_acknowledged: true,
      });
      await refreshProjectData();
      setNotice("Disclosure lifecycle record saved. Nothing was auto-sent.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save disclosure record.");
    } finally {
      setActionLoading(null);
    }
  }

  async function checkWording(event: FormEvent) {
    event.preventDefault();
    setActionLoading("wording");
    setError(null);
    setWordingResult(null);
    try {
      const data = await apiPost<WordingCheck>("/trust-metrics/wording-check", { text: wordingText });
      setWordingResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not check wording.");
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) return <CommandLoadingState label="Loading trust metrics engine..." />;
  if (error && !status) {
    return (
      <div className="mt-8 grid gap-4">
        <CommandNotice tone="warning" title="Trust metrics engine could not load" text={error} />
        <button type="button" className="btn-secondary w-fit" onClick={() => void loadAll()}>Retry</button>
      </div>
    );
  }
  if (!status) return <CommandEmptyState title="No trust metrics data" text="The backend did not return trust metrics engine status." />;

  return (
    <section className="mt-8 space-y-8">
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="External mappings" value={summary?.metrics.external_advisory_mapping_count ?? 0} note="OSV/NVD/GitHub/CISA records mapped separately." />
        <MetricCard label="Web3Guard findings" value={summary?.metrics.web3guard_generated_finding_count ?? 0} note="Only owner-recorded Web3Guard-generated findings." />
        <MetricCard label="Disclosures" value={summary?.metrics.disclosure_count ?? 0} note="Manual lifecycle records; no auto-send." />
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Safety boundaries</p>
          <p className="mt-2 text-3xl font-black text-white">{activeBoundaryCount}</p>
          <p className="mt-2 text-sm text-slate-400">No fake score, no audit claim, no 100% secure badge.</p>
        </div>
      </div>

      {error ? <CommandNotice tone="warning" title="Action warning" text={error} /> : null}
      {notice ? <CommandNotice tone="success" title="Saved" text={notice} /> : null}

      <div className="glass-tile p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="section-label">Public safe summary</p>
            <h2 className="mt-2 text-2xl font-black text-white">Metrics are transparency indicators, not an audit score.</h2>
            <p className="mt-3 max-w-4xl text-sm leading-7 text-slate-400">{summary?.safe_public_wording || status.safe_public_wording}</p>
          </div>
          <Link href="/security-passport" className="btn-secondary">Open Security Passport →</Link>
        </div>
        {summary ? (
          <pre className="mono mt-5 max-h-80 overflow-auto rounded-2xl bg-black/35 p-4 text-xs text-slate-300">{safeJson(summary.metrics)}</pre>
        ) : null}
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        {status.surfaces.map((surface) => <SurfaceCard key={surface.key} surface={surface} />)}
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <form onSubmit={saveSnapshot} className="glass-tile p-6">
          <p className="section-label">Snapshot</p>
          <h2 className="mt-2 text-2xl font-black text-white">Save metrics snapshot</h2>
          <label className="mt-5 block text-sm font-bold text-slate-300">Project ID
            <input className="input mt-2" value={projectId} onChange={(event) => setProjectId(event.target.value)} onBlur={(event) => { void refreshProjectData(event.currentTarget.value); }} />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">Project name
            <input className="input mt-2" value={projectName} onChange={(event) => setProjectName(event.target.value)} />
          </label>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="block text-sm font-bold text-slate-300">External advisories
              <input className="input mt-2" type="number" min={0} value={externalCount} onChange={(event) => setExternalCount(Number(event.target.value))} />
            </label>
            <label className="block text-sm font-bold text-slate-300">Web3Guard findings
              <input className="input mt-2" type="number" min={0} value={web3guardCount} onChange={(event) => setWeb3guardCount(Number(event.target.value))} />
            </label>
            <label className="block text-sm font-bold text-slate-300">Community items
              <input className="input mt-2" type="number" min={0} value={communityCount} onChange={(event) => setCommunityCount(Number(event.target.value))} />
            </label>
            <label className="block text-sm font-bold text-slate-300">Disclosures
              <input className="input mt-2" type="number" min={0} value={disclosureCount} onChange={(event) => setDisclosureCount(Number(event.target.value))} />
            </label>
            <label className="block text-sm font-bold text-slate-300 sm:col-span-2">Resolved disclosures
              <input className="input mt-2" type="number" min={0} value={resolvedCount} onChange={(event) => setResolvedCount(Number(event.target.value))} />
            </label>
          </div>
          <label className="mt-4 block text-sm font-bold text-slate-300">Public note
            <textarea className="input mt-2 min-h-28" value={metricNote} onChange={(event) => setMetricNote(event.target.value)} />
          </label>
          <button className="btn-primary mt-5" disabled={actionLoading === "snapshot"} type="submit">
            {actionLoading === "snapshot" ? "Saving..." : "Save snapshot"}
          </button>
        </form>

        <form onSubmit={saveMapping} className="glass-tile p-6">
          <p className="section-label">Advisory mapping</p>
          <h2 className="mt-2 text-2xl font-black text-white">Map advisory to project</h2>
          <label className="mt-5 block text-sm font-bold text-slate-300">Source
            <select className="input mt-2" value={advisorySource} onChange={(event) => setAdvisorySource(event.target.value)}>
              <option value="osv">OSV</option>
              <option value="nvd">NVD</option>
              <option value="github_advisory">GitHub Advisory</option>
              <option value="cisa_kev">CISA KEV</option>
              <option value="manual">Manual</option>
              <option value="other">Other</option>
            </select>
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">Advisory ID
            <input className="input mt-2" value={advisoryId} onChange={(event) => setAdvisoryId(event.target.value)} />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">Title
            <input className="input mt-2" value={advisoryTitle} onChange={(event) => setAdvisoryTitle(event.target.value)} />
          </label>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="block text-sm font-bold text-slate-300">Severity
              <select className="input mt-2" value={severity} onChange={(event) => setSeverity(event.target.value)}>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
                <option value="informational">Informational</option>
                <option value="unknown">Unknown</option>
              </select>
            </label>
            <label className="block text-sm font-bold text-slate-300">Status
              <select className="input mt-2" value={mappingStatus} onChange={(event) => setMappingStatus(event.target.value)}>
                <option value="needs_review">Needs review</option>
                <option value="mapped">Mapped</option>
                <option value="affected">Affected</option>
                <option value="not_affected">Not affected</option>
                <option value="resolved">Resolved</option>
                <option value="watching">Watching</option>
              </select>
            </label>
          </div>
          <label className="mt-4 block text-sm font-bold text-slate-300">Affected component
            <input className="input mt-2" value={affectedComponent} onChange={(event) => setAffectedComponent(event.target.value)} />
          </label>
          <button className="btn-primary mt-5" disabled={actionLoading === "mapping"} type="submit">
            {actionLoading === "mapping" ? "Saving..." : "Save mapping"}
          </button>
        </form>

        <form onSubmit={saveDisclosure} className="glass-tile p-6">
          <p className="section-label">Disclosure lifecycle</p>
          <h2 className="mt-2 text-2xl font-black text-white">Track manual disclosure</h2>
          <label className="mt-5 block text-sm font-bold text-slate-300">Origin
            <select className="input mt-2" value={disclosureOrigin} onChange={(event) => setDisclosureOrigin(event.target.value)}>
              <option value="external_advisory">External advisory</option>
              <option value="web3guard_generated_finding">Web3Guard-generated finding</option>
              <option value="owner_reported">Owner reported</option>
              <option value="community_review">Community review</option>
              <option value="manual">Manual</option>
            </select>
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">Title
            <input className="input mt-2" value={disclosureTitle} onChange={(event) => setDisclosureTitle(event.target.value)} />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">Recipient
            <input className="input mt-2" value={recipient} onChange={(event) => setRecipient(event.target.value)} />
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">Status
            <select className="input mt-2" value={disclosureStatus} onChange={(event) => setDisclosureStatus(event.target.value)}>
              <option value="draft">Draft</option>
              <option value="sent_manually">Sent manually</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="triaged">Triaged</option>
              <option value="fix_in_progress">Fix in progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
              <option value="not_applicable">Not applicable</option>
            </select>
          </label>
          <label className="mt-4 block text-sm font-bold text-slate-300">Summary
            <textarea className="input mt-2 min-h-28" value={disclosureSummary} onChange={(event) => setDisclosureSummary(event.target.value)} />
          </label>
          <button className="btn-primary mt-5" disabled={actionLoading === "disclosure"} type="submit">
            {actionLoading === "disclosure" ? "Saving..." : "Save disclosure"}
          </button>
        </form>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={checkWording} className="glass-tile p-6">
          <p className="section-label">Safe wording guard</p>
          <h2 className="mt-2 text-2xl font-black text-white">Check public metric text</h2>
          <textarea className="input mt-5 min-h-32" value={wordingText} onChange={(event) => setWordingText(event.target.value)} />
          <button className="btn-secondary mt-4" disabled={actionLoading === "wording"} type="submit">
            {actionLoading === "wording" ? "Checking..." : "Check wording"}
          </button>
          {wordingResult ? (
            <div className="mt-5 rounded-2xl border border-white/10 bg-black/25 p-4">
              <StatusPill status={wordingResult.safe ? "Ready" : "Manual"} />
              <p className="mt-3 text-sm text-slate-300">Safe: {wordingResult.safe ? "yes" : "no"}</p>
              {wordingResult.blocked_claim ? <p className="mt-2 text-sm text-amber-100">Blocked claim: {wordingResult.blocked_claim}</p> : null}
              {wordingResult.detected_cves.length ? <p className="mt-2 text-sm text-slate-400">Detected CVEs: {wordingResult.detected_cves.join(", ")}</p> : null}
            </div>
          ) : null}
        </form>

        <div className="glass-tile p-6">
          <p className="section-label">Recent records</p>
          <h2 className="mt-2 text-2xl font-black text-white">Latest project trust ledger</h2>
          <div className="mt-5 grid gap-4">
            <div>
              <p className="text-sm font-black text-white">Snapshots</p>
              {snapshots.length ? snapshots.map((item) => (
                <p key={item.id} className="mt-2 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-xs text-slate-400">
                  {item.project_name || item.project_id} · external {item.external_advisory_count} · Web3Guard {item.web3guard_generated_finding_count} · disclosures {item.disclosure_count}
                </p>
              )) : <p className="mt-2 text-sm text-slate-500">No snapshot saved yet.</p>}
            </div>
            <div>
              <p className="text-sm font-black text-white">Advisory mappings</p>
              {mappings.length ? mappings.map((item) => (
                <p key={item.id} className="mt-2 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-xs text-slate-400">
                  {item.advisory_source.toUpperCase()} · {item.advisory_id} · {item.severity} · {item.mapping_status}
                </p>
              )) : <p className="mt-2 text-sm text-slate-500">No advisory mapping saved yet.</p>}
            </div>
            <div>
              <p className="text-sm font-black text-white">Disclosures</p>
              {disclosures.length ? disclosures.map((item) => (
                <p key={item.id} className="mt-2 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-xs text-slate-400">
                  {item.origin} · {item.title} · {item.status}
                </p>
              )) : <p className="mt-2 text-sm text-slate-500">No disclosure record saved yet.</p>}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
