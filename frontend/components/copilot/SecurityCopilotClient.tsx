"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";

type CopilotWorkspace = {
  ok: boolean;
  user_id: string;
  project_id?: string | null;
  language: string;
  generated_at: string;
  mode: {
    mode: string;
    provider?: string;
    provider_configured: boolean;
    status_label: string;
    note: string;
  };
  summary: Record<string, number | string | null | undefined>;
  next_steps: Array<{
    id: string;
    title: string;
    priority: string;
    severity: string;
    why_it_matters: string;
    safe_next_step: string;
    verify_command: string;
    source: string;
  }>;
  safe_commands: Array<{ id: string; title: string; command: string; purpose: string; risk_level: string }>;
  report_assistant: {
    templates: Record<string, string>;
    suggested_summary: string;
    safe_public_phrase: string;
    blocked_phrases: string[];
    review_note: string;
  };
  evidence_digest: Array<Record<string, unknown>>;
  india_pack_summary: { mode?: string; sections?: string[]; note: string };
  real_only_note: string;
  safe_boundary: string;
};

type AskResponse = {
  ok: boolean;
  mode: CopilotWorkspace["mode"];
  question: string;
  answer: string;
  recommended_steps: CopilotWorkspace["next_steps"];
  safe_commands: CopilotWorkspace["safe_commands"];
  blocked: string[];
  review_note: string;
};

const severityClass: Record<string, string> = {
  critical: "sev-critical",
  high: "sev-high",
  medium: "sev-medium",
  low: "sev-low",
  info: "sev-info",
};

function copyToClipboard(text: string) {
  void navigator.clipboard?.writeText(text);
}

export function SecurityCopilotClient() {
  const [userId, setUserId] = useState("local-demo-user");
  const [projectId, setProjectId] = useState("");
  const [language, setLanguage] = useState("English");
  const [question, setQuestion] = useState("What should I fix next before launch?");
  const [workspace, setWorkspace] = useState<CopilotWorkspace | null>(null);
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useMemo(() => {
    const params = new URLSearchParams({ user_id: userId || "local-demo-user", language: language || "English" });
    if (projectId.trim()) params.set("project_id", projectId.trim());
    return params.toString();
  }, [userId, projectId, language]);

  async function loadWorkspace() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<CopilotWorkspace>(`/security-copilot/workspace?${query}`);
      setWorkspace(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load Security Copilot workspace.");
    } finally {
      setLoading(false);
    }
  }

  async function askCopilot() {
    setAsking(true);
    setError(null);
    try {
      const data = await apiPost<AskResponse>("/security-copilot/ask", {
        user_id: userId || "local-demo-user",
        project_id: projectId.trim() || null,
        language,
        question,
        include_commands: true,
      });
      setAnswer(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not build Copilot guidance.");
    } finally {
      setAsking(false);
    }
  }

  useEffect(() => {
    void loadWorkspace();
  }, []);

  return (
    <main className="relative overflow-hidden px-4 py-10 text-white sm:px-6 lg:px-8">
      <div className="pointer-events-none absolute inset-0 w3g-cyber-grid opacity-50" />
      <div className="relative mx-auto max-w-7xl">
        <section className="quantum-stage p-6 sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="section-label">Security Copilot Workspace</p>
              <h1 className="mt-4 max-w-5xl text-4xl font-black tracking-[-0.06em] sm:text-6xl">
                AI-style security coaching without fake audit claims.
              </h1>
              <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
                Ask what to fix next, get safe local commands, improve report wording, and use stored EON/Sentinel/readiness evidence. Provider OFF still works through deterministic checklist guidance.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link href="/eon" className="btn-secondary">EON Risk Graph</Link>
              <Link href="/security-tests" className="btn-secondary">Test Generator</Link>
              <Link href="/trust-readiness" className="btn-secondary">Trust Readiness</Link>
            </div>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-4">
            <input className="input" value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="user_id" />
            <input className="input" value={projectId} onChange={(event) => setProjectId(event.target.value)} placeholder="optional project_id" />
            <select className="select" value={language} onChange={(event) => setLanguage(event.target.value)}>
              <option>English</option>
              <option>Hinglish</option>
              <option>Hindi</option>
            </select>
            <button className="btn-primary" type="button" onClick={loadWorkspace} disabled={loading}>Refresh workspace</button>
          </div>
        </section>

        {error ? <div className="mt-6 rounded-3xl border border-red-400/30 bg-red-500/10 p-5 text-red-100">{error}</div> : null}
        {loading ? <div className="mt-6 command-loading">Loading Copilot workspace...</div> : null}

        {workspace ? (
          <>
            <section className="mt-6 grid gap-4 lg:grid-cols-5">
              <Metric label="Mode" value={workspace.mode.status_label} />
              <Metric label="Risk nodes" value={workspace.summary.risk_nodes ?? 0} />
              <Metric label="Launch blockers" value={workspace.summary.launch_blockers ?? 0} />
              <Metric label="Next steps" value={workspace.summary.next_steps ?? 0} />
              <Metric label="Evidence entries" value={workspace.summary.evidence_entries ?? 0} />
            </section>

            <section className="mt-6 grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
              <div className="glass-tile p-6">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="section-label">Ask Copilot</p>
                    <h2 className="mt-2 text-2xl font-black">Next-step assistant</h2>
                    <p className="mt-2 text-sm leading-6 text-slate-400">Output is guidance only. It never unlocks a certified audit badge or auto-applies fixes.</p>
                  </div>
                  <span className={`badge ${workspace.mode.provider_configured ? "badge-green" : "badge-amber"}`}>{workspace.mode.mode}</span>
                </div>
                <textarea className="textarea mt-5 min-h-[150px]" value={question} onChange={(event) => setQuestion(event.target.value)} />
                <button className="btn-primary mt-4" type="button" onClick={askCopilot} disabled={asking}>{asking ? "Building guidance..." : "Ask Security Copilot"}</button>
                {answer ? (
                  <div className="mt-5 rounded-3xl border border-cyan/20 bg-cyan/10 p-5">
                    <p className="mono text-xs font-black uppercase tracking-[0.18em] text-cyan">Copilot guidance</p>
                    <pre className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-100">{answer.answer}</pre>
                    <p className="mt-4 text-xs text-slate-400">{answer.review_note}</p>
                  </div>
                ) : null}
              </div>

              <div className="glass-tile p-6">
                <p className="section-label">Priority queue</p>
                <h2 className="mt-2 text-2xl font-black">Evidence-backed next actions</h2>
                <div className="mt-5 grid gap-3">
                  {workspace.next_steps.length ? workspace.next_steps.map((step) => (
                    <div key={step.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="font-black text-white">{step.title}</p>
                          <p className="mt-1 text-xs text-slate-500">{step.priority} · {step.source}</p>
                        </div>
                        <span className={severityClass[step.severity] || "sev-info"}>{step.severity}</span>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-slate-300">{step.why_it_matters}</p>
                      <p className="mt-3 text-sm leading-6 text-cyan-100">Next: {step.safe_next_step}</p>
                      <p className="mt-2 text-xs text-slate-500">Verify: {step.verify_command}</p>
                    </div>
                  )) : <p className="text-sm text-slate-500">No stored evidence yet. Save a project, run scans, and generate reports first.</p>}
                </div>
              </div>
            </section>

            <section className="mt-6 grid gap-6 xl:grid-cols-3">
              <div className="glass-tile p-6 xl:col-span-2">
                <p className="section-label">Safe commands</p>
                <h2 className="mt-2 text-2xl font-black">Local defensive verification pack</h2>
                <div className="mt-5 grid gap-3">
                  {workspace.safe_commands.map((cmd) => (
                    <div key={cmd.id} className="rounded-2xl border border-white/10 bg-black/25 p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="font-black text-white">{cmd.title}</p>
                          <p className="mt-1 text-sm text-slate-400">{cmd.purpose}</p>
                        </div>
                        <button className="btn-ghost" type="button" onClick={() => copyToClipboard(cmd.command)}>Copy</button>
                      </div>
                      <code className="mt-3 block overflow-x-auto rounded-xl border border-white/10 bg-black/40 p-3 mono text-xs text-cyan-100">{cmd.command}</code>
                      <p className="mt-2 text-xs text-slate-500">{cmd.risk_level}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-tile p-6">
                <p className="section-label">Report wording</p>
                <h2 className="mt-2 text-2xl font-black">Safe share copy</h2>
                <p className="mt-4 rounded-2xl border border-emerald-400/20 bg-emerald-500/10 p-4 text-sm leading-6 text-emerald-100">{workspace.report_assistant.safe_public_phrase}</p>
                <p className="mt-4 text-sm leading-6 text-slate-300">{workspace.report_assistant.suggested_summary}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {workspace.report_assistant.blocked_phrases.map((phrase) => <span key={phrase} className="badge badge-red">{phrase}</span>)}
                </div>
              </div>
            </section>

            <section className="mt-6 grid gap-6 lg:grid-cols-2">
              <div className="glass-tile p-6">
                <p className="section-label">Evidence digest</p>
                <h2 className="mt-2 text-2xl font-black">Latest evidence entries</h2>
                <div className="mt-5 grid gap-3">
                  {workspace.evidence_digest.length ? workspace.evidence_digest.map((entry, index) => (
                    <div key={`${entry.id || index}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                      <p className="font-black text-white">{String(entry.title || entry.kind || "Evidence entry")}</p>
                      <p className="mt-1 break-all mono text-xs text-slate-500">{String(entry.evidence_hash || entry.id || "hash unavailable")}</p>
                    </div>
                  )) : <p className="text-sm text-slate-500">No evidence entries yet.</p>}
                </div>
              </div>

              <div className="glass-tile p-6">
                <p className="section-label">Boundary</p>
                <h2 className="mt-2 text-2xl font-black">What Copilot will not do</h2>
                <div className="mt-5 grid gap-3 text-sm leading-6 text-slate-300">
                  <p className="rounded-2xl border border-amber-400/20 bg-amber-500/10 p-4">{workspace.real_only_note}</p>
                  <p className="rounded-2xl border border-white/10 bg-black/20 p-4">{workspace.safe_boundary}</p>
                  <p className="rounded-2xl border border-cyan/20 bg-cyan/10 p-4">India Launch Pack mode: {workspace.india_pack_summary.mode || "not loaded"}. {workspace.india_pack_summary.note}</p>
                </div>
              </div>
            </section>
          </>
        ) : null}
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="stat-slab p-4">
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 truncate text-lg font-black text-white">{value ?? "—"}</p>
    </div>
  );
}
