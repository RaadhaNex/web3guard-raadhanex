"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { getCurrentUserId } from "@/lib/supabase";
import { CommandEmptyState, CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";

type SentinelStatus = {
  ok: boolean;
  phase: string;
  version: string;
  enabled: boolean;
  live_ingestion_enabled: boolean;
  user_monitoring_enabled: boolean;
  admin_intelligence_enabled: boolean;
  counts: Record<string, number>;
  real_only_note: string;
  public_stats_wording: { safe: string[]; blocked: string[] };
};

type SentinelSource = {
  id: string;
  name: string;
  type: string;
  status: string;
  safe_wording: string;
  unsafe_wording: string;
  official_endpoint_hint?: string;
};

type IntelligenceItem = {
  id: string;
  source: string;
  title: string;
  severity: string;
  summary?: string;
  package?: string | null;
  ecosystem?: string | null;
  published_at?: string;
  safe_counting_bucket?: string;
};

type RiskPattern = {
  id: string;
  title: string;
  severity: string;
  tags: string[];
  mapped_to: string[];
  fix_direction: string;
  status: string;
};

type Alert = {
  id: string;
  type: string;
  severity: string;
  title: string;
  detail: string;
  project_id?: string | null;
  href?: string | null;
  status: string;
};

type SentinelMode = "overview" | "intelligence" | "admin" | "disclosure" | "project";

function severityClass(severity: string) {
  const clean = severity.toLowerCase();
  if (clean === "critical") return "sev-critical";
  if (clean === "high") return "sev-high";
  if (clean === "medium") return "sev-medium";
  if (clean === "low") return "sev-low";
  return "sev-info";
}

function statusBadge(status: string) {
  const s = status.toLowerCase();
  if (s.includes("configured") && !s.includes("not")) return "badge-green";
  if (s.includes("not") || s.includes("needs") || s.includes("manual") || s.includes("required")) return "badge-amber";
  return "badge-cyan";
}

function StatCard({ label, value, note }: { label: string; value: string | number; note?: string }) {
  return (
    <div className="stat-slab p-5">
      <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-black text-white">{value}</p>
      {note ? <p className="mt-2 text-xs leading-5 text-slate-400">{note}</p> : null}
    </div>
  );
}

function PageShell({ children, mode }: { children: React.ReactNode; mode: SentinelMode }) {
  const titles: Record<SentinelMode, string> = {
    overview: "Sentinel monitoring + vulnerability intelligence core",
    intelligence: "Public vulnerability intelligence index",
    admin: "Admin intelligence monitoring",
    disclosure: "Responsible disclosure draft console",
    project: "Project Sentinel monitoring",
  };
  const texts: Record<SentinelMode, string> = {
    overview: "User-side project monitoring and admin-side intelligence stay separate. Public advisories are tracked/indexed, not claimed as Web3Guard-discovered vulnerabilities.",
    intelligence: "Normalize NVD, OSV, GitHub Advisory, CISA KEV, DeFi incident, provider, and manual advisory records into one safe intelligence layer.",
    admin: "Admin-only style overview for source health, counts, alerts, and disclosure queue. It uses stored records and does not invent project impact.",
    disclosure: "Prepare legally safer disclosure drafts after manual validation. Web3Guard does not send disclosures automatically.",
    project: "Project-specific monitoring view generated only from stored project, scan, report, and indexed advisory records.",
  };

  return (
    <main className="relative overflow-hidden">
      <section className="trust-shell border-b border-white/10">
        <div className="pointer-events-none absolute inset-0 w3g-cyber-grid opacity-60" />
        <div className="relative mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
          <p className="section-label">Web3Guard Sentinel</p>
          <h1 className="mt-4 max-w-5xl text-4xl font-black sm:text-6xl">{titles[mode]}</h1>
          <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">{texts[mode]}</p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link href="/sentinel" className="btn-secondary">Overview</Link>
            <Link href="/sentinel/intelligence" className="btn-secondary">Intelligence</Link>
            <Link href="/sentinel/admin" className="btn-secondary">Admin board</Link>
            <Link href="/sentinel/disclosure" className="btn-secondary">Disclosure draft</Link>
            <Link href="/dashboard" className="btn-primary">Dashboard</Link>
          </div>
        </div>
      </section>
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">{children}</div>
    </main>
  );
}

export function SentinelClient({ mode = "overview", projectId }: { mode?: SentinelMode; projectId?: string }) {
  const [status, setStatus] = useState<SentinelStatus | null>(null);
  const [sources, setSources] = useState<SentinelSource[]>([]);
  const [intel, setIntel] = useState<IntelligenceItem[]>([]);
  const [patterns, setPatterns] = useState<RiskPattern[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [admin, setAdmin] = useState<any>(null);
  const [userId, setUserId] = useState("local-demo-user");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<any>(null);
  const [draftForm, setDraftForm] = useState({
    target: "Project security team",
    contact: "security@example.com",
    finding_summary: "Potential public security misconfiguration observed during authorized launch-readiness review.",
    evidence_summary: "Passive evidence only. No exploit attempt, wallet signing, or private data access was performed.",
    confidence: "needs_manual_validation",
  });

  const alertSummary = useMemo(() => {
    return alerts.reduce<Record<string, number>>((acc, alert) => {
      acc[alert.severity] = (acc[alert.severity] || 0) + 1;
      return acc;
    }, {});
  }, [alerts]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const resolvedUserId = await getCurrentUserId().catch(() => "local-demo-user");
      setUserId(resolvedUserId);
      const [statusData, sourceData, intelData, alertsData] = await Promise.all([
        apiGet<SentinelStatus>("/sentinel/status"),
        apiGet<{ sources: SentinelSource[] }>("/sentinel/sources"),
        apiGet<{ items: IntelligenceItem[]; patterns: RiskPattern[] }>("/sentinel/intelligence?limit=25"),
        apiGet<{ alerts: Alert[] }>(`/sentinel/project-alerts?user_id=${encodeURIComponent(resolvedUserId)}${projectId ? `&project_id=${encodeURIComponent(projectId)}` : ""}`),
      ]);
      setStatus(statusData);
      setSources(sourceData.sources || []);
      setIntel(intelData.items || []);
      setPatterns(intelData.patterns || []);
      setAlerts(alertsData.alerts || []);
      if (mode === "admin") {
        const adminData = await apiGet<any>(`/sentinel/admin/overview?user_id=${encodeURIComponent(resolvedUserId)}`);
        setAdmin(adminData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sentinel data load failed.");
    } finally {
      setLoading(false);
    }
  }

  async function buildDraft() {
    setError(null);
    try {
      const response = await apiPost<any>("/sentinel/disclosure/draft", {
        ...draftForm,
        real_only_acknowledged: true,
      });
      setDraft(response.draft);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not build disclosure draft.");
    }
  }

  useEffect(() => {
    void load();
  }, [mode, projectId]);

  if (loading) {
    return (
      <PageShell mode={mode}>
        <CommandLoadingState label="Loading Sentinel intelligence..." />
      </PageShell>
    );
  }

  return (
    <PageShell mode={mode}>
      {error ? <CommandNotice tone="danger" title="Sentinel data issue" text={error} /> : null}

      {mode === "overview" || mode === "project" ? (
        <div className="grid gap-6">
          <section className="grid gap-4 md:grid-cols-4">
            <StatCard label="Indexed advisories" value={status?.counts.indexed_public_advisories ?? 0} note="Tracked/indexed, not claimed as discovered." />
            <StatCard label="Risk patterns" value={status?.counts.educational_risk_patterns ?? 0} note="Launch-readiness mappings." />
            <StatCard label="Project alerts" value={alerts.length} note="Derived only from stored records." />
            <StatCard label="Live ingestion" value={status?.live_ingestion_enabled ? "ON" : "OFF"} note="Manual/provider-ready until enabled." />
          </section>

          <CommandNotice
            tone="info"
            title="Real-only Sentinel rule"
            text={status?.real_only_note || "Public advisories and Web3Guard findings are counted separately."}
          />

          <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="glass-tile p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-2xl font-black">Project monitoring alerts</h2>
                <span className="badge badge-cyan">User: {userId}</span>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-5">
                {["critical", "high", "medium", "low", "info"].map((key) => (
                  <div key={key} className="rounded-2xl border border-white/10 bg-black/20 p-3">
                    <p className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-500">{key}</p>
                    <p className="mt-1 text-xl font-black text-white">{alertSummary[key] || 0}</p>
                  </div>
                ))}
              </div>
              <div className="mt-5 grid gap-3">
                {alerts.length ? alerts.slice(0, 12).map((alert) => (
                  <Link key={alert.id} href={alert.href || "/sentinel"} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-cyan/25 hover:bg-cyan/[0.05]">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="font-black text-white">{alert.title}</p>
                        <p className="mt-1 text-sm leading-6 text-slate-400">{alert.detail}</p>
                      </div>
                      <span className={severityClass(alert.severity)}>{alert.severity}</span>
                    </div>
                  </Link>
                )) : (
                  <CommandEmptyState title="No project alerts yet" text="Sentinel does not create fake alerts. Add projects, run scans, save reports, or ingest public advisories to generate real mappings." actionHref="/scanner/unified-url" actionLabel="Run scanner" />
                )}
              </div>
            </div>

            <div className="glass-tile p-6">
              <h2 className="text-2xl font-black">Source readiness</h2>
              <div className="mt-5 grid gap-3">
                {sources.slice(0, 8).map((source) => (
                  <div key={source.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-black text-white">{source.name}</p>
                      <span className={`badge ${statusBadge(source.status)}`}>{source.status}</span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-400">{source.safe_wording}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      ) : null}

      {mode === "intelligence" ? (
        <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
          <div className="glass-tile p-6">
            <h2 className="text-2xl font-black">Indexed public advisories</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Use safe wording: indexed, tracked, mapped. Do not call these Web3Guard-discovered vulnerabilities.</p>
            <div className="mt-5 grid gap-3">
              {intel.length ? intel.map((item) => (
                <div key={`${item.source}-${item.id}`} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-black text-white">{item.title}</p>
                      <p className="mt-1 text-xs text-slate-500">{item.source} · {item.id} · {item.published_at || "date not provided"}</p>
                    </div>
                    <span className={severityClass(item.severity)}>{item.severity}</span>
                  </div>
                  {item.summary ? <p className="mt-3 text-sm leading-6 text-slate-400">{item.summary}</p> : null}
                  {item.package ? <p className="mt-3 text-xs text-cyan">Package: {item.ecosystem || "ecosystem"}/{item.package}</p> : null}
                </div>
              )) : (
                <CommandEmptyState title="No advisories ingested yet" text="Connect a real source or manually ingest public advisory records. Until then, counts stay zero instead of fake." />
              )}
            </div>
          </div>

          <div className="glass-tile p-6">
            <h2 className="text-2xl font-black">Risk mapping patterns</h2>
            <div className="mt-5 grid gap-3">
              {patterns.map((pattern) => (
                <div key={pattern.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-black text-white">{pattern.title}</p>
                    <span className={severityClass(pattern.severity)}>{pattern.severity}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{pattern.fix_direction}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {pattern.tags.slice(0, 6).map((tag) => <span key={tag} className="badge badge-cyan">{tag}</span>)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}

      {mode === "admin" ? (
        <div className="grid gap-6">
          <section className="grid gap-4 md:grid-cols-4">
            <StatCard label="Projects observed" value={admin?.counts?.projects_observed ?? 0} />
            <StatCard label="Scans observed" value={admin?.counts?.scans_observed ?? 0} />
            <StatCard label="Advisories indexed" value={admin?.counts?.indexed_public_advisories ?? 0} />
            <StatCard label="Open alerts" value={admin?.counts?.open_project_alerts ?? 0} />
          </section>
          <CommandNotice tone="warning" title="Admin/public separation" text={admin?.scope_note || "Admin intelligence should not expose private customer data publicly."} />
          <section className="grid gap-6 lg:grid-cols-2">
            <div className="glass-tile p-6">
              <h2 className="text-2xl font-black">Safe public stats</h2>
              <pre className="mt-5 overflow-auto rounded-2xl border border-white/10 bg-black/40 p-4 text-xs leading-6 text-slate-300">{JSON.stringify(admin?.safe_public_stats || {}, null, 2)}</pre>
            </div>
            <div className="glass-tile p-6">
              <h2 className="text-2xl font-black">Blocked wording</h2>
              <div className="mt-5 grid gap-3">
                {(admin?.blocked_stats_wording || []).map((item: string) => <CommandNotice key={item} tone="danger" title="Do not claim" text={item} />)}
              </div>
            </div>
          </section>
        </div>
      ) : null}

      {mode === "disclosure" ? (
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="glass-tile p-6">
            <h2 className="text-2xl font-black">Draft responsible disclosure</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">This creates a draft only. Validate authorization, evidence, and contact before sending manually.</p>
            <div className="mt-5 grid gap-4">
              {Object.entries(draftForm).map(([key, value]) => (
                <label key={key} className="grid gap-2 text-sm font-bold text-slate-300">
                  {key.replaceAll("_", " ")}
                  {key.includes("summary") ? (
                    <textarea className="textarea !min-h-[120px]" value={value} onChange={(event) => setDraftForm((prev) => ({ ...prev, [key]: event.target.value }))} />
                  ) : (
                    <input className="input" value={value} onChange={(event) => setDraftForm((prev) => ({ ...prev, [key]: event.target.value }))} />
                  )}
                </label>
              ))}
              <button className="btn-primary" type="button" onClick={() => void buildDraft()}>Build draft</button>
            </div>
          </div>
          <div className="glass-tile p-6">
            <h2 className="text-2xl font-black">Draft output</h2>
            {draft ? (
              <pre className="mt-5 whitespace-pre-wrap rounded-2xl border border-white/10 bg-black/40 p-4 text-sm leading-7 text-slate-300">{draft.draft}</pre>
            ) : (
              <CommandEmptyState title="No draft generated" text="Fill in validated evidence and build a draft. Nothing is sent automatically." />
            )}
          </div>
        </div>
      ) : null}
    </PageShell>
  );
}
