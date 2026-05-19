"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";

type ReviewRequest = {
  id: string;
  user_id: string;
  project_id?: string | null;
  title: string;
  project_url?: string | null;
  repo_url?: string | null;
  scope_summary?: string;
  focus_areas?: string[];
  review_type: string;
  status: string;
  priority: string;
  public_feedback_enabled: boolean;
  created_at: string;
  note?: string;
};

type FeedbackItem = {
  id: string;
  request_id?: string | null;
  user_id: string;
  project_id?: string | null;
  reviewer_display_name: string;
  summary: string;
  evidence_note: string;
  severity: string;
  status: string;
  visibility: string;
  created_at: string;
};

type TriageItem = {
  id: string;
  request_id?: string | null;
  feedback_id?: string | null;
  status: string;
  severity: string;
  summary: string;
  next_step: string;
  assigned_to?: string | null;
  created_at: string;
};

type Board = {
  ok: boolean;
  user_id: string;
  project_id?: string | null;
  requests: ReviewRequest[];
  feedback: FeedbackItem[];
  triage: TriageItem[];
  summary: Record<string, number>;
  reviewer_rules: string[];
  real_only_note: string;
};

type AdminOverview = {
  ok: boolean;
  summary: Record<string, number>;
  requests_by_status: Record<string, number>;
  feedback_by_status: Record<string, number>;
  latest_requests: ReviewRequest[];
  latest_feedback: FeedbackItem[];
  latest_triage: TriageItem[];
  real_only_note: string;
  safe_boundary: string;
};

type TemplateResponse = {
  ok: boolean;
  template: { subject: string; message: string; safe_boundary: string; blocked_claims: string[] };
};

const severityClass: Record<string, string> = {
  critical: "sev-critical",
  high: "sev-high",
  medium: "sev-medium",
  low: "sev-low",
  info: "sev-info",
};

function copy(text: string) {
  void navigator.clipboard?.writeText(text);
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat-slab p-4">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 truncate text-2xl font-black text-white">{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color = status.includes("closed") || status.includes("completed") || status.includes("accepted") ? "badge-green" : status.includes("moderation") || status.includes("needs") || status.includes("triage") ? "badge-amber" : "badge-cyan";
  return <span className={`badge ${color}`}>{status}</span>;
}

export function CommunityReviewClient({ defaultProjectId = "", adminMode = false }: { defaultProjectId?: string; adminMode?: boolean }) {
  const [userId, setUserId] = useState("local-demo-user");
  const [projectId, setProjectId] = useState(defaultProjectId);
  const [title, setTitle] = useState("Pre-audit community review request");
  const [projectUrl, setProjectUrl] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [scopeSummary, setScopeSummary] = useState("Review public launch readiness evidence, supplied reports, GitHub hygiene, and open fix tasks. No live exploitation is authorized.");
  const [focusAreas, setFocusAreas] = useState("contracts, website, github, admin-opsec, wallet-ux");
  const [authorized, setAuthorized] = useState(false);
  const [board, setBoard] = useState<Board | null>(null);
  const [admin, setAdmin] = useState<AdminOverview | null>(null);
  const [template, setTemplate] = useState<TemplateResponse | null>(null);
  const [feedbackSummary, setFeedbackSummary] = useState("Missing evidence should be kept Not Assessed until project owner supplies proof.");
  const [feedbackEvidence, setFeedbackEvidence] = useState("Reviewed public report summary and visible project metadata only.");
  const [selectedRequestId, setSelectedRequestId] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const query = useMemo(() => {
    const params = new URLSearchParams({ user_id: userId || "local-demo-user" });
    if (projectId.trim()) params.set("project_id", projectId.trim());
    return params.toString();
  }, [userId, projectId]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [boardData, adminData] = await Promise.all([
        apiGet<Board>(`/community-review/project-board?${query}`),
        adminMode ? apiGet<AdminOverview>("/community-review/admin/overview") : Promise.resolve(null),
      ]);
      setBoard(boardData);
      setAdmin(adminData);
      if (!selectedRequestId && boardData.requests[0]?.id) setSelectedRequestId(boardData.requests[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load Community Review workspace.");
    } finally {
      setLoading(false);
    }
  }

  async function createRequest() {
    setBusy("request");
    setError(null);
    setMessage(null);
    try {
      const data = await apiPost<{ ok: boolean; request: ReviewRequest }>("/community-review/requests", {
        user_id: userId || "local-demo-user",
        project_id: projectId.trim() || null,
        title,
        project_url: projectUrl.trim() || null,
        repo_url: repoUrl.trim() || null,
        scope_summary: scopeSummary,
        focus_areas: focusAreas.split(",").map((item) => item.trim()).filter(Boolean),
        review_type: "pre_audit_readiness",
        priority: "medium",
        public_feedback_enabled: true,
        authorized_scope_confirmed: authorized,
      });
      setMessage(`Review request created: ${data.request.id}`);
      setSelectedRequestId(data.request.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create review request.");
    } finally {
      setBusy(null);
    }
  }

  async function submitFeedback() {
    setBusy("feedback");
    setError(null);
    setMessage(null);
    try {
      const data = await apiPost<{ ok: boolean; feedback: FeedbackItem }>("/community-review/feedback", {
        request_id: selectedRequestId || null,
        user_id: userId || "local-demo-user",
        project_id: projectId.trim() || null,
        reviewer_display_name: "Community reviewer",
        summary: feedbackSummary,
        evidence_note: feedbackEvidence,
        severity: "info",
        safe_feedback_acknowledged: true,
      });
      setMessage(`Feedback queued for moderation: ${data.feedback.id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit feedback.");
    } finally {
      setBusy(null);
    }
  }

  async function addTriage(status: string) {
    setBusy(status);
    setError(null);
    setMessage(null);
    try {
      const data = await apiPost<{ ok: boolean; triage_item: TriageItem }>("/community-review/triage", {
        request_id: selectedRequestId || null,
        user_id: userId || "local-demo-user",
        project_id: projectId.trim() || null,
        status,
        severity: status === "ready_for_review" ? "medium" : "info",
        summary: `Manual triage update: ${status}`,
        next_step: status === "ready_for_review" ? "Assign a reviewer and validate non-sensitive evidence." : "Continue scope validation and evidence collection.",
      });
      setMessage(`Triage event added: ${data.triage_item.id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add triage event.");
    } finally {
      setBusy(null);
    }
  }

  async function buildTemplate() {
    setBusy("template");
    setError(null);
    try {
      const data = await apiPost<TemplateResponse>("/community-review/templates/responsible-review", {
        project_name: title || "your Web3 project",
        scope_summary: scopeSummary,
        contact: "project team",
      });
      setTemplate(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not build template.");
    } finally {
      setBusy(null);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const summary = board?.summary || {};

  return (
    <main className="relative overflow-hidden px-4 py-10 text-white sm:px-6 lg:px-8">
      <div className="pointer-events-none absolute inset-0 w3g-cyber-grid opacity-50" />
      <div className="relative mx-auto max-w-7xl">
        <section className="quantum-stage p-6 sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="section-label">Community Review Layer</p>
              <h1 className="mt-4 max-w-5xl text-4xl font-black tracking-[-0.06em] sm:text-6xl">
                Request human review without fake auditor badges.
              </h1>
              <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
                Create a scoped review request, collect moderated feedback, and run manual triage while keeping public wording honest: pre-audit readiness only, not a bounty marketplace or certified audit.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link href="/security-copilot" className="btn-secondary">Security Copilot</Link>
              <Link href="/trust-pages" className="btn-secondary">Trust Pages</Link>
              <Link href="/community-review/admin" className="btn-secondary">Admin board</Link>
            </div>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <input className="input" value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="user_id" />
            <input className="input" value={projectId} onChange={(event) => setProjectId(event.target.value)} placeholder="optional project_id" />
            <button className="btn-primary" type="button" onClick={load} disabled={loading}>Refresh board</button>
          </div>
        </section>

        {error ? <div className="mt-6 rounded-3xl border border-red-400/30 bg-red-500/10 p-5 text-red-100">{error}</div> : null}
        {message ? <div className="mt-6 rounded-3xl border border-emerald-400/30 bg-emerald-500/10 p-5 text-emerald-100">{message}</div> : null}
        {loading ? <div className="mt-6 command-loading">Loading community review board...</div> : null}

        {board ? (
          <>
            <section className="mt-6 grid gap-4 lg:grid-cols-5">
              <Metric label="Requests" value={summary.requests ?? 0} />
              <Metric label="Open" value={summary.open_requests ?? 0} />
              <Metric label="Feedback" value={summary.feedback_items ?? 0} />
              <Metric label="Moderation" value={summary.needs_moderation ?? 0} />
              <Metric label="Triage events" value={summary.triage_events ?? 0} />
            </section>

            <section className="mt-6 grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
              <div className="glass-tile p-6">
                <p className="section-label">Request board</p>
                <h2 className="mt-2 text-2xl font-black">Create a scoped review request</h2>
                <p className="mt-2 text-sm leading-6 text-slate-400">Requests stay manual-first. No request creates an auditor badge, bounty guarantee, or certified audit status.</p>
                <div className="mt-5 grid gap-4">
                  <input className="input" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Review title" />
                  <input className="input" value={projectUrl} onChange={(event) => setProjectUrl(event.target.value)} placeholder="https://project.example" />
                  <input className="input" value={repoUrl} onChange={(event) => setRepoUrl(event.target.value)} placeholder="https://github.com/org/repo" />
                  <input className="input" value={focusAreas} onChange={(event) => setFocusAreas(event.target.value)} placeholder="contracts, website, github" />
                  <textarea className="textarea min-h-[130px]" value={scopeSummary} onChange={(event) => setScopeSummary(event.target.value)} />
                  <label className="flex items-start gap-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm leading-6 text-amber-100">
                    <input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} className="mt-1" />
                    I confirm this project/scope is owned by me or I am authorized to request this review. No live exploitation is authorized.
                  </label>
                  <button className="btn-primary" type="button" onClick={createRequest} disabled={busy !== null}>Create review request</button>
                </div>
              </div>

              <div className="glass-tile p-6">
                <p className="section-label">Active requests</p>
                <h2 className="mt-2 text-2xl font-black">Manual review queue</h2>
                <div className="mt-5 grid gap-3">
                  {board.requests.length ? board.requests.map((request) => (
                    <button key={request.id} type="button" onClick={() => setSelectedRequestId(request.id)} className={`text-left rounded-2xl border p-4 transition ${selectedRequestId === request.id ? "border-cyan/40 bg-cyan/10" : "border-white/10 bg-white/[0.03] hover:border-cyan/25"}`}>
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="font-black text-white">{request.title}</p>
                          <p className="mt-1 text-xs text-slate-500">{request.id} · {request.review_type}</p>
                        </div>
                        <StatusBadge status={request.status} />
                      </div>
                      <p className="mt-3 text-sm leading-6 text-slate-300">{request.scope_summary || "No scope summary supplied."}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {(request.focus_areas || []).map((area) => <span key={area} className="badge badge-cyan">{area}</span>)}
                      </div>
                    </button>
                  )) : <p className="text-sm text-slate-500">No review requests yet. Create one only for authorized scope.</p>}
                </div>
              </div>
            </section>

            <section className="mt-6 grid gap-6 xl:grid-cols-3">
              <div className="glass-tile p-6">
                <p className="section-label">Public feedback</p>
                <h2 className="mt-2 text-2xl font-black">Moderation-first queue</h2>
                <textarea className="textarea mt-5 min-h-[110px]" value={feedbackSummary} onChange={(event) => setFeedbackSummary(event.target.value)} />
                <textarea className="textarea mt-3 min-h-[100px]" value={feedbackEvidence} onChange={(event) => setFeedbackEvidence(event.target.value)} />
                <button className="btn-secondary mt-4" type="button" onClick={submitFeedback} disabled={busy !== null}>Queue safe feedback</button>
              </div>

              <div className="glass-tile p-6">
                <p className="section-label">Manual triage</p>
                <h2 className="mt-2 text-2xl font-black">Scope validation states</h2>
                <div className="mt-5 grid gap-3">
                  {["validating_scope", "needs_more_evidence", "ready_for_review", "assigned", "closed"].map((status) => (
                    <button key={status} className="btn-secondary !justify-start" type="button" onClick={() => addTriage(status)} disabled={busy !== null}>{status}</button>
                  ))}
                </div>
              </div>

              <div className="glass-tile p-6">
                <p className="section-label">Responsible template</p>
                <h2 className="mt-2 text-2xl font-black">Safe review message</h2>
                <button className="btn-secondary mt-5" type="button" onClick={buildTemplate} disabled={busy !== null}>Build template</button>
                {template ? (
                  <div className="mt-5 rounded-2xl border border-white/10 bg-black/25 p-4">
                    <p className="font-black text-white">{template.template.subject}</p>
                    <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap text-xs leading-6 text-slate-300">{template.template.message}</pre>
                    <button className="btn-ghost mt-3" type="button" onClick={() => copy(template.template.message)}>Copy message</button>
                  </div>
                ) : <p className="mt-4 text-sm text-slate-500">Generate a scope-safe template for manual review coordination.</p>}
              </div>
            </section>

            <section className="mt-6 grid gap-6 xl:grid-cols-3">
              <Queue title="Feedback queue" items={board.feedback.map((item) => ({ id: item.id, title: item.summary, meta: `${item.status} · ${item.severity}`, severity: item.severity }))} />
              <Queue title="Triage events" items={board.triage.map((item) => ({ id: item.id, title: item.summary, meta: `${item.status} · ${item.next_step}`, severity: item.severity }))} />
              <div className="glass-tile p-6">
                <p className="section-label">Reviewer rules</p>
                <h2 className="mt-2 text-2xl font-black">Safety boundary</h2>
                <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">
                  {board.reviewer_rules.map((rule) => <li key={rule} className="flex gap-3"><span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-cyan" />{rule}</li>)}
                </ul>
              </div>
            </section>
          </>
        ) : null}

        {adminMode && admin ? (
          <section className="mt-6 quantum-stage p-6">
            <p className="section-label">Admin overview</p>
            <h2 className="mt-2 text-2xl font-black">Community review moderation board</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-5">
              {Object.entries(admin.summary).map(([key, value]) => <Metric key={key} label={key.replaceAll("_", " ")} value={value} />)}
            </div>
            <p className="mt-5 text-sm leading-6 text-slate-400">{admin.safe_boundary}</p>
          </section>
        ) : null}
      </div>
    </main>
  );
}

function Queue({ title, items }: { title: string; items: Array<{ id: string; title: string; meta: string; severity: string }> }) {
  return (
    <div className="glass-tile p-6">
      <p className="section-label">Queue</p>
      <h2 className="mt-2 text-2xl font-black">{title}</h2>
      <div className="mt-5 grid gap-3">
        {items.length ? items.map((item) => (
          <div key={item.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <p className="font-black text-white">{item.title}</p>
              <span className={severityClass[item.severity] || "sev-info"}>{item.severity}</span>
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-500">{item.id} · {item.meta}</p>
          </div>
        )) : <p className="text-sm text-slate-500">No records yet.</p>}
      </div>
    </div>
  );
}
