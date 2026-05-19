"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type PassportProject = {
  project_id: string;
  project_name: string;
  website_url?: string | null;
  chain?: string | null;
  project_type?: string | null;
  passport_id: string;
  readiness_score?: number | null;
  readiness_label?: string | null;
  open_actions?: number;
  not_assessed_modules?: number;
};

type Passport = {
  ok: boolean;
  error?: string;
  passport_id: string;
  passport_hash: string;
  generated_at: string;
  project: Record<string, any>;
  readiness_snapshot: { score?: number | null; label?: string | null; components?: Array<Record<string, any>>; blocked_wording?: string[] };
  latest_report?: Record<string, any> | null;
  module_summary: { modules?: Array<Record<string, any>>; counts?: Record<string, number>; not_assessed_count?: number; assessed_count?: number };
  evidence_summary: { entries_count: number; latest_entries?: Array<Record<string, any>>; note?: string };
  monitoring_status: { configs_count: number; alerts_count: number; latest_alerts?: Array<Record<string, any>> };
  sentinel_status: { alerts_count: number; latest_alerts?: Array<Record<string, any>> };
  community_review_status: { requests_count: number; feedback_count: number; triage_count: number; latest_triage?: Array<Record<string, any>> };
  external_links: Array<Record<string, any>>;
  action_summary: Record<string, number>;
  public_share_card: Record<string, any>;
  safe_wording: string;
  real_only_note: string;
};

type Mode = "index" | "project" | "admin";

function shortHash(value?: string | null) {
  if (!value) return "Not available";
  return value.length > 20 ? `${value.slice(0, 12)}…${value.slice(-8)}` : value;
}

function labelTone(label?: string | null) {
  const text = String(label || "").toLowerCase();
  if (text.includes("ready") || text.includes("reviewed")) return "badge-green";
  if (text.includes("critical") || text.includes("block")) return "badge-red";
  if (text.includes("needed") || text.includes("partial") || text.includes("manual")) return "badge-amber";
  return "badge-cyan";
}

function Stat({ label, value, tone = "cyan" }: { label: string; value: string | number | null | undefined; tone?: "cyan" | "green" | "amber" | "red" }) {
  const toneClass = tone === "green" ? "text-emerald-200" : tone === "amber" ? "text-amber-200" : tone === "red" ? "text-red-200" : "text-cyan";
  return (
    <div className="stat-slab p-4">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className={`mt-2 truncate text-2xl font-black ${toneClass}`}>{value ?? "—"}</p>
    </div>
  );
}

function Notice({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-3xl border border-amber-300/20 bg-amber-300/10 p-5 text-amber-50">
      <p className="font-black">{title}</p>
      <p className="mt-2 text-sm leading-6 text-amber-100/80">{text}</p>
    </div>
  );
}

export function SecurityPassportClient({ mode, projectId, initialUserId = "" }: { mode: Mode; projectId?: string; initialUserId?: string }) {
  const [userId, setUserId] = useState(initialUserId);
  const [projects, setProjects] = useState<PassportProject[]>([]);
  const [passport, setPassport] = useState<Passport | null>(null);
  const [adminOverview, setAdminOverview] = useState<Record<string, any> | null>(null);
  const [status, setStatus] = useState<Record<string, any> | null>(null);
  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [linkTitle, setLinkTitle] = useState("");
  const [linkUrl, setLinkUrl] = useState("");
  const [linkType, setLinkType] = useState("audit");

  const project = passport?.project;
  const score = passport?.readiness_snapshot?.score;
  const scoreTone = typeof score === "number" ? (score >= 75 ? "green" : score >= 50 ? "amber" : "red") : "cyan";

  async function loadStatus() {
    try {
      const data = await apiGet<Record<string, any>>("/security-passport/status");
      setStatus(data);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load passport status.");
    }
  }

  async function loadIndex(event?: FormEvent) {
    event?.preventDefault();
    if (!userId.trim()) {
      setMessage("Enter user_id to load security passports.");
      return;
    }
    setLoading(true);
    setMessage("");
    try {
      const data = await apiGet<{ projects: PassportProject[] }>(`/security-passport/projects?user_id=${encodeURIComponent(userId.trim())}`);
      setProjects(data.projects || []);
      if (!data.projects?.length) setMessage("No project passports found yet. Create a project and generate scans/reports first.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load passports.");
    } finally {
      setLoading(false);
    }
  }

  async function loadProject() {
    if (!userId.trim() || !projectId) {
      setMessage("user_id and project_id are required.");
      return;
    }
    setLoading(true);
    setMessage("");
    try {
      const data = await apiGet<Passport>(`/security-passport/project/${encodeURIComponent(projectId)}?user_id=${encodeURIComponent(userId.trim())}`);
      setPassport(data);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load passport.");
    } finally {
      setLoading(false);
    }
  }

  async function loadAdmin() {
    setLoading(true);
    setMessage("");
    try {
      const data = await apiGet<Record<string, any>>("/security-passport/admin/overview");
      setAdminOverview(data);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load admin overview.");
    } finally {
      setLoading(false);
    }
  }

  async function addLink(event: FormEvent) {
    event.preventDefault();
    if (!passport || !projectId) return;
    setLoading(true);
    setMessage("");
    try {
      await apiPost("/security-passport/external-links", {
        user_id: userId.trim(),
        project_id: projectId,
        title: linkTitle,
        url: linkUrl,
        link_type: linkType,
      });
      setLinkTitle("");
      setLinkUrl("");
      await loadProject();
      setMessage("External link added. It remains an owner-supplied reference, not a Web3Guard certification claim.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not add external link.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadStatus();
    if (mode === "admin") void loadAdmin();
    if (mode === "project" && initialUserId) void loadProject();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, projectId]);

  const shareText = useMemo(() => {
    if (!passport) return "";
    return `${passport.public_share_card?.title}\n${passport.public_share_card?.subtitle}\nReadiness: ${passport.public_share_card?.score ?? "Not Assessed"} · ${passport.public_share_card?.readiness_label ?? "Not Assessed"}\nReport hash: ${passport.public_share_card?.report_hash || "Not available"}\nPassport hash: ${passport.public_share_card?.passport_hash}\n${passport.public_share_card?.safe_wording}`;
  }, [passport]);

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8 grid gap-6 lg:grid-cols-[1fr_0.72fr] lg:items-end">
        <div>
          <p className="section-label">Security Passport / Trust Network</p>
          <h1 className="mt-3 text-4xl font-black tracking-[-0.05em] sm:text-5xl">
            Pre-audit readiness passport for projects, not a certificate.
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400">
            Summarize trust readiness, report hash, evidence ledger, monitoring, Sentinel alerts, community review, and external links in one shareable view. No fake audited/certified claim is generated.
          </p>
        </div>
        <div className="glass-tile p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan">Safe wording</p>
          <p className="mt-2 text-lg font-black text-white">{status?.label || "Pre-audit readiness passport"}</p>
          <p className="mt-2 text-sm leading-6 text-slate-400">{status?.real_only_note || "Passport summarizes readiness evidence only."}</p>
        </div>
      </div>

      {message ? <Notice title="Status" text={message} /> : null}

      {mode === "index" ? (
        <section className="mt-6 grid gap-6">
          <form onSubmit={loadIndex} className="glass-tile grid gap-4 p-5 md:grid-cols-[1fr_auto]">
            <input className="input" value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="Enter user_id to load project passports" />
            <button className="btn-primary" disabled={loading}>{loading ? "Loading..." : "Load passports"}</button>
          </form>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {projects.map((item) => (
              <Link key={item.project_id} href={`/security-passport/project/${item.project_id}?user_id=${encodeURIComponent(userId)}`} className="glass-tile p-5 transition hover:-translate-y-1 hover:border-cyan/30">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xl font-black text-white">{item.project_name}</p>
                    <p className="mt-1 text-sm text-slate-500">{item.chain || "Chain not set"} · {item.project_type || "Project type not set"}</p>
                  </div>
                  <span className={`badge ${labelTone(item.readiness_label)}`}>{item.readiness_label || "Not Assessed"}</span>
                </div>
                <div className="mt-5 grid grid-cols-3 gap-2">
                  <Stat label="Score" value={item.readiness_score ?? "—"} tone="cyan" />
                  <Stat label="Open" value={item.open_actions ?? 0} tone="amber" />
                  <Stat label="N/A" value={item.not_assessed_modules ?? 0} tone="red" />
                </div>
                <p className="mt-4 mono text-xs text-slate-500">{item.passport_id}</p>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {mode === "project" ? (
        <section className="mt-6 grid gap-6">
          {!initialUserId ? (
            <form onSubmit={(event) => { event.preventDefault(); void loadProject(); }} className="glass-tile grid gap-4 p-5 md:grid-cols-[1fr_auto]">
              <input className="input" value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="Enter user_id to open this passport" />
              <button className="btn-primary" disabled={loading}>{loading ? "Loading..." : "Open passport"}</button>
            </form>
          ) : null}

          {passport ? (
            <>
              <div className="quantum-stage p-6">
                <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p className="badge badge-cyan">{passport.safe_wording}</p>
                    <h2 className="mt-4 text-3xl font-black text-white">{project?.name || "Project passport"}</h2>
                    <p className="mt-2 text-sm text-slate-400">{project?.website_url || "No URL saved"} · {project?.chain || "Chain not set"}</p>
                    <p className="mt-4 mono text-xs text-slate-500">Passport ID: {passport.passport_id}</p>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2 lg:w-[30rem]">
                    <Stat label="Readiness" value={score ?? "—"} tone={scoreTone} />
                    <Stat label="Open actions" value={passport.action_summary?.open_actions ?? 0} tone="amber" />
                    <Stat label="Report hash" value={shortHash(passport.latest_report?.report_hash)} tone="cyan" />
                    <Stat label="Passport hash" value={shortHash(passport.passport_hash)} tone="green" />
                  </div>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
                <div className="glass-tile p-5">
                  <h3 className="text-2xl font-black text-white">Module readiness</h3>
                  <div className="mt-5 grid gap-3">
                    {(passport.module_summary.modules || []).map((module) => (
                      <div key={module.id || module.label} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <p className="font-black text-white">{module.label || module.id}</p>
                          <span className={`badge ${labelTone(module.status || module.public_label)}`}>{module.status || module.public_label || "Unknown"}</span>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-slate-400">{module.description || module.summary || "Stored module status from public trust/evidence records."}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid gap-6">
                  <div className="glass-tile p-5">
                    <h3 className="text-2xl font-black text-white">Evidence summary</h3>
                    <p className="mt-2 text-sm text-slate-400">{passport.evidence_summary.note}</p>
                    <div className="mt-4 grid gap-3">
                      {(passport.evidence_summary.latest_entries || []).map((entry, index) => (
                        <div key={`${entry.evidence_hash || index}`} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                          <p className="text-sm font-black text-white">{entry.title || entry.kind || `Evidence ${index + 1}`}</p>
                          <p className="mt-1 mono text-xs text-slate-500">{shortHash(entry.evidence_hash || entry.hash)}</p>
                        </div>
                      ))}
                      {!passport.evidence_summary.latest_entries?.length ? <p className="text-sm text-slate-500">No evidence ledger entries available yet.</p> : null}
                    </div>
                  </div>

                  <div className="glass-tile p-5">
                    <h3 className="text-2xl font-black text-white">Share card</h3>
                    <textarea className="textarea mt-4 min-h-[220px]" readOnly value={shareText} />
                    <p className="mt-3 text-xs leading-5 text-slate-500">Use this as readiness wording only. Do not call it an audit certificate.</p>
                  </div>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-3">
                <div className="glass-tile p-5">
                  <h3 className="text-xl font-black text-white">Monitoring + Sentinel</h3>
                  <p className="mt-3 text-sm text-slate-400">Monitoring alerts: {passport.monitoring_status.alerts_count}</p>
                  <p className="mt-1 text-sm text-slate-400">Sentinel alerts: {passport.sentinel_status.alerts_count}</p>
                </div>
                <div className="glass-tile p-5">
                  <h3 className="text-xl font-black text-white">Community review</h3>
                  <p className="mt-3 text-sm text-slate-400">Requests: {passport.community_review_status.requests_count}</p>
                  <p className="mt-1 text-sm text-slate-400">Feedback: {passport.community_review_status.feedback_count}</p>
                  <p className="mt-1 text-sm text-slate-400">Triage items: {passport.community_review_status.triage_count}</p>
                </div>
                <form onSubmit={addLink} className="glass-tile p-5">
                  <h3 className="text-xl font-black text-white">External links</h3>
                  <p className="mt-2 text-sm text-slate-400">Add real audit/bounty/docs links only if they exist.</p>
                  <div className="mt-4 grid gap-3">
                    <input className="input" value={linkTitle} onChange={(event) => setLinkTitle(event.target.value)} placeholder="Link title" />
                    <input className="input" value={linkUrl} onChange={(event) => setLinkUrl(event.target.value)} placeholder="https://..." />
                    <select className="select" value={linkType} onChange={(event) => setLinkType(event.target.value)}>
                      <option value="audit">External audit</option>
                      <option value="bounty">Bounty / disclosure</option>
                      <option value="docs">Docs</option>
                      <option value="monitoring">Monitoring</option>
                      <option value="disclosure">Disclosure</option>
                      <option value="other">Other</option>
                    </select>
                    <button className="btn-secondary" disabled={loading}>Add link</button>
                  </div>
                </form>
              </div>

              <div className="glass-tile p-5">
                <h3 className="text-2xl font-black text-white">External proof links</h3>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  {passport.external_links.map((link) => (
                    <a key={link.id} href={link.url} target="_blank" rel="noreferrer" className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-cyan/30">
                      <p className="font-black text-white">{link.title}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.18em] text-cyan">{link.link_type}</p>
                      <p className="mt-2 break-all text-sm text-slate-500">{link.url}</p>
                    </a>
                  ))}
                  {!passport.external_links.length ? <p className="text-sm text-slate-500">No external proof links added yet.</p> : null}
                </div>
              </div>
            </>
          ) : null}
        </section>
      ) : null}

      {mode === "admin" ? (
        <section className="mt-6 grid gap-6">
          <div className="grid gap-4 md:grid-cols-4">
            <Stat label="External links" value={adminOverview?.external_links_count ?? "—"} tone="cyan" />
            <Stat label="Monitoring configs" value={adminOverview?.monitoring_overview?.configs_count ?? adminOverview?.monitoring_overview?.counts?.configs ?? "—"} tone="green" />
            <Stat label="Community requests" value={adminOverview?.community_overview?.requests_count ?? adminOverview?.community_overview?.counts?.requests ?? "—"} tone="amber" />
            <Stat label="Passport type" value="Readiness" tone="cyan" />
          </div>
          <div className="glass-tile p-5">
            <h2 className="text-2xl font-black text-white">Admin trust network overview</h2>
            <pre className="mt-4 max-h-[520px] overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs leading-6 text-slate-300">
              {JSON.stringify(adminOverview || status || {}, null, 2)}
            </pre>
          </div>
        </section>
      ) : null}
    </main>
  );
}
