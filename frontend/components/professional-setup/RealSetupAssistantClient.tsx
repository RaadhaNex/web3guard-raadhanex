"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "@/lib/api";

type JsonMap = Record<string, unknown>;

function isRecord(value: unknown): value is JsonMap {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asText(value: unknown, fallback = "—") {
  if (value === undefined || value === null || value === "") return fallback;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return fallback;
  }
}

function asRecord(value: unknown): JsonMap {
  return isRecord(value) ? value : {};
}

function asArray(value: unknown): JsonMap[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function jsonText(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function statusTone(value: unknown) {
  const text = asText(value, "").toLowerCase();
  if (text.includes("ready") || text.includes("true") || text.includes("configured")) return "badge-green";
  if (text.includes("missing") || text.includes("false") || text.includes("blocked")) return "badge-red";
  if (text.includes("optional") || text.includes("warning")) return "badge-amber";
  return "badge-cyan";
}

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mt-4 max-h-[460px] overflow-auto rounded-2xl border border-white/10 bg-black/40 p-4 text-xs leading-5 text-slate-300">{jsonText(value)}</pre>;
}

function MetricCard({ label, value, tone = "cyan" }: { label: string; value: unknown; tone?: "cyan" | "green" | "amber" | "red" }) {
  const toneClass = {
    cyan: "border-cyan/15 bg-cyan/5 text-cyan",
    green: "border-emerald-400/20 bg-emerald-500/10 text-emerald-100",
    amber: "border-amber-400/20 bg-amber-500/10 text-amber-100",
    red: "border-red-400/20 bg-red-500/10 text-red-100",
  }[tone];
  return (
    <div className={`rounded-2xl border p-4 ${toneClass}`}>
      <p className="text-xs font-black uppercase tracking-[0.18em] opacity-80">{label}</p>
      <p className="mt-2 text-2xl font-black text-white">{asText(value, "0")}</p>
    </div>
  );
}

function CheckList({ checks }: { checks: JsonMap[] }) {
  return (
    <div className="mt-4 overflow-x-auto rounded-2xl border border-white/10">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="bg-white/[0.04] text-xs uppercase tracking-[0.16em] text-slate-500">
          <tr>
            <th className="px-4 py-3">Key</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Required</th>
            <th className="px-4 py-3">Fix</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/10">
          {checks.map((check, index) => (
            <tr key={`${asText(check.key, "check")}-${index}`}>
              <td className="px-4 py-3 font-mono text-xs text-white">{asText(check.key)}</td>
              <td className="px-4 py-3"><span className={`badge ${statusTone(check.state)}`}>{asText(check.state)}</span></td>
              <td className="px-4 py-3 text-slate-300">{asText(check.required)}</td>
              <td className="max-w-[360px] px-4 py-3 text-slate-400">{asText(check.fix)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EnvSnippet({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <h4 className="text-sm font-black uppercase tracking-[0.18em] text-slate-300">{title}</h4>
      <pre className="mt-3 overflow-auto rounded-xl bg-black/40 p-4 text-xs leading-6 text-slate-300">{asText(value)}</pre>
    </div>
  );
}

export function RealSetupAssistantClient() {
  const [status, setStatus] = useState<JsonMap | null>(null);
  const [env, setEnv] = useState<JsonMap | null>(null);
  const [webhooks, setWebhooks] = useState<JsonMap | null>(null);
  const [worker, setWorker] = useState<JsonMap | null>(null);
  const [readiness, setReadiness] = useState<JsonMap | null>(null);
  const [actions, setActions] = useState<JsonMap | null>(null);
  const [activeJson, setActiveJson] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadAll() {
    setLoading(true);
    setError(null);
    try {
      const [nextStatus, nextEnv, nextWebhooks, nextWorker, nextReadiness, nextActions] = await Promise.all([
        apiGet<JsonMap>("/professional-setup/status"),
        apiGet<JsonMap>("/professional-setup/env-checklist"),
        apiGet<JsonMap>("/professional-setup/webhooks"),
        apiGet<JsonMap>("/professional-setup/worker-gate"),
        apiGet<JsonMap>("/professional-setup/production-readiness"),
        apiGet<JsonMap>("/professional-setup/manual-actions"),
      ]);
      setStatus(nextStatus);
      setEnv(nextEnv);
      setWebhooks(nextWebhooks);
      setWorker(nextWorker);
      setReadiness(nextReadiness);
      setActions(nextActions);
      setActiveJson(nextReadiness);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAll();
  }, []);

  const snippets = useMemo(() => asRecord(env?.snippets), [env]);
  const workerEnabled = asRecord(worker?.currently_enabled);
  const workerTools = asRecord(worker?.tool_status);
  const github = asRecord(webhooks?.github);
  const onchain = asRecord(webhooks?.onchain);
  const manualActions = asArray(actions?.actions);
  const checks = asArray(env?.checks);

  return (
    <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <section className="glass-tile p-6 sm:p-8">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="section-label">Phase T</p>
            <h1 className="mt-3 text-4xl font-black tracking-[-0.06em] sm:text-6xl">Real setup assistant.</h1>
            <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400">
              Production readiness, env checklist, webhook setup, safe worker gate, and manual action plan for Web3Guard AI. This page does not enable unsafe tooling by itself.
            </p>
          </div>
          <button onClick={loadAll} disabled={loading} className="rounded-2xl border border-cyan/30 bg-cyan/10 px-5 py-3 text-sm font-black text-cyan transition hover:bg-cyan/15 disabled:opacity-60">
            {loading ? "Checking..." : "Refresh readiness"}
          </button>
        </div>
        <div className="mt-6 flex flex-wrap gap-2">
          <span className="badge badge-green">Real setup only</span>
          <span className="badge badge-amber">Worker off until isolated</span>
          <span className="badge badge-cyan">No certified audit claim</span>
          <span className="badge badge-purple">No private key / seed collection</span>
        </div>
        {error && <div className="mt-5 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</div>}
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Readiness score" value={readiness?.readiness_score} tone={Number(readiness?.readiness_score || 0) >= 80 ? "green" : "amber"} />
        <MetricCard label="Required env ready" value={asText(env?.required_ready)} tone={env?.required_ready ? "green" : "red"} />
        <MetricCard label="GitHub webhook" value={asText(github.configured)} tone={github.configured ? "green" : "amber"} />
        <MetricCard label="Worker safe" value={asText(worker?.safe_to_turn_true)} tone={worker?.safe_to_turn_true ? "green" : "red"} />
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="glass-tile p-5">
          <h2 className="text-2xl font-black text-white">Environment checklist</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">Only secret presence is shown. Values are not exposed.</p>
          <CheckList checks={checks} />
        </div>
        <div className="glass-tile p-5">
          <h2 className="text-2xl font-black text-white">Safe worker answer</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Do not set worker flags true on the main API. Turn them on only after a separate isolated worker service is ready and this gate is green.
          </p>
          <div className="mt-4 grid gap-3">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Effective runner enabled</p>
              <p className="mt-1 text-lg font-black text-white">{asText(workerEnabled.effective_professional_runner_enabled)}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Foundry</p>
              <p className="mt-1 text-sm text-slate-300">{asText(asRecord(workerTools.foundry).state)} · {asText(asRecord(workerTools.foundry).binary)}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Echidna</p>
              <p className="mt-1 text-sm text-slate-300">{asText(asRecord(workerTools.echidna).state)} · {asText(asRecord(workerTools.echidna).binary)}</p>
            </div>
          </div>
          <JsonBlock value={{ blockers: worker?.blockers, warnings: worker?.warnings, answer: worker?.answer_to_user_env_question }} />
        </div>
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-2">
        <div className="glass-tile p-5">
          <h2 className="text-2xl font-black text-white">Webhook readiness</h2>
          <div className="mt-4 grid gap-4">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center justify-between gap-3"><h3 className="font-black text-white">GitHub</h3><span className={`badge ${statusTone(github.configured)}`}>{asText(github.configured)}</span></div>
              <p className="mt-2 break-all text-xs text-slate-400">{asText(github.webhook_url)}</p>
              <p className="mt-2 text-sm text-slate-300">Events seen: {asText(github.events_seen, "0")}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center justify-between gap-3"><h3 className="font-black text-white">On-chain provider</h3><span className={`badge ${statusTone(onchain.configured)}`}>{asText(onchain.configured)}</span></div>
              <p className="mt-2 break-all text-xs text-slate-400">{asText(onchain.webhook_url)}</p>
              <p className="mt-2 text-sm text-slate-300">Events seen: {asText(onchain.events_seen, "0")}</p>
            </div>
          </div>
        </div>
        <div className="glass-tile p-5">
          <h2 className="text-2xl font-black text-white">Manual action plan</h2>
          <div className="mt-4 space-y-3">
            {manualActions.map((item) => (
              <div key={asText(item.order)} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs font-black uppercase tracking-[0.18em] text-cyan">Step {asText(item.order)}</p>
                <h3 className="mt-1 font-black text-white">{asText(item.title)}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">{asText(item.done_signal)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-2">
        <EnvSnippet title="Render backend minimum" value={snippets.backend_render_minimum} />
        <EnvSnippet title="Vercel frontend minimum" value={snippets.frontend_vercel_minimum} />
        <EnvSnippet title="Worker default off" value={snippets.safe_worker_default_off} />
        <EnvSnippet title="Worker on only after isolation" value={snippets.safe_worker_on_after_isolated_runtime} />
      </section>

      <section className="mt-8 glass-tile p-5">
        <div className="flex flex-wrap gap-2">
          <button onClick={() => setActiveJson(status)} className="badge badge-cyan">Status JSON</button>
          <button onClick={() => setActiveJson(env)} className="badge badge-cyan">Env JSON</button>
          <button onClick={() => setActiveJson(webhooks)} className="badge badge-cyan">Webhook JSON</button>
          <button onClick={() => setActiveJson(worker)} className="badge badge-cyan">Worker JSON</button>
          <button onClick={() => setActiveJson(readiness)} className="badge badge-cyan">Readiness JSON</button>
        </div>
        <JsonBlock value={activeJson} />
      </section>
    </main>
  );
}
