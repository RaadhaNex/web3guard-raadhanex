"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "@/lib/api";

type Qa = {
  launch_readiness: string;
  security_readiness: string;
  security_score: number;
  manual_blockers: string[];
  checklist: Array<{ area: string; items: string[] }>;
  real_only_note: string;
};

type MapData = {
  real_live_now: string[];
  manual_setup_required: Array<{ service: string; needed_for: string; env_keys: string }>;
  manual_admin_actions: string[];
  never_collect: string[];
  real_only_rule: string;
};

type RemainingWork = {
  area: string;
  status: string;
  priority: string;
  owner: string;
  what_is_done: string;
  remaining_work: string;
  how_to_complete: string;
  verify: string;
};

type ProviderStatus = {
  provider: string;
  status: string;
  required_env: string[];
  verify: string;
};

type CompletionSummary = {
  ok: boolean;
  product: string;
  environment: string;
  code_side_status: string;
  external_provider_pending_count: number;
  high_priority_remaining_count: number;
  blocked_claims: string[];
  next_safe_tests: string[];
};

type ProviderResponse = {
  ok: boolean;
  real_only_rule: string;
  providers: ProviderStatus[];
};

type HandoffResponse = {
  ok: boolean;
  handoff: string;
};

function statusTone(status: string) {
  const value = status.toLowerCase();
  if (value === "done" || value.includes("configured")) return "border-emerald-300 bg-emerald-50 text-emerald-700";
  if (value.includes("manual") || value.includes("external") || value.includes("not assessed")) return "border-amber-300 bg-amber-50 text-amber-800";
  if (value.includes("pending") || value.includes("needs api key") || value.includes("provider not configured") || value.includes("tool not installed")) return "border-rose-200 bg-rose-50 text-rose-700";
  return "border-slate-200 bg-slate-50 text-slate-700";
}

function priorityTone(priority: string) {
  if (priority === "high") return "bg-rose-100 text-rose-700 border-rose-200";
  if (priority === "medium") return "bg-amber-100 text-amber-700 border-amber-200";
  return "bg-slate-100 text-slate-700 border-slate-200";
}

export function FinalQaClient() {
  const [qa, setQa] = useState<Qa | null>(null);
  const [map, setMap] = useState<MapData | null>(null);
  const [remaining, setRemaining] = useState<RemainingWork[]>([]);
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [completion, setCompletion] = useState<CompletionSummary | null>(null);
  const [handoff, setHandoff] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiGet<Qa>("/final-qa/status"),
      apiGet<MapData>("/final-qa/implementation-map"),
      apiGet<{ ok: boolean; remaining_work: RemainingWork[] }>("/final-qa/remaining-work"),
      apiGet<ProviderResponse>("/final-qa/external-providers"),
      apiGet<CompletionSummary>("/final-qa/completion-summary"),
      apiGet<HandoffResponse>("/final-qa/next-chat-handoff"),
    ])
      .then(([q, m, r, p, c, h]) => {
        setQa(q);
        setMap(m);
        setRemaining(r.remaining_work || []);
        setProviders(p.providers || []);
        setCompletion(c);
        setHandoff(h.handoff || "");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load final QA"));
  }, []);

  const highPriorityRemaining = useMemo(
    () => remaining.filter((item) => item.priority === "high" && item.status !== "done"),
    [remaining]
  );

  async function copyHandoff() {
    if (!handoff) return;
    try {
      await navigator.clipboard.writeText(handoff);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  if (error) {
    return (
      <main className="min-h-screen bg-slate-950 px-4 py-12 text-white">
        <div className="mx-auto max-w-5xl rounded-3xl border border-red-400/30 bg-red-500/10 p-6 text-red-100">
          {error}
        </div>
      </main>
    );
  }

  if (!qa || !map || !completion) {
    return (
      <main className="min-h-screen bg-slate-950 px-4 py-12 text-white">
        <div className="mx-auto max-w-5xl rounded-3xl border border-white/10 bg-white/[0.04] p-6">
          Loading final QA map...
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-10 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <section className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-8">
          <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Final Production Launch QA</p>
          <h1 className="mt-3 max-w-5xl text-4xl font-black text-white md:text-5xl">
            Completion map, provider setup, and next-chat handoff
          </h1>
          <p className="mt-4 max-w-4xl text-slate-300">
            Code-side launch hardening is in place. The remaining work is mostly external provider configuration, manual two-user security QA, and final payment/provider verification. No fake success or certified audit claims are allowed.
          </p>

          <div className="mt-6 grid gap-4 md:grid-cols-4">
            <div className="rounded-3xl border border-white/10 bg-black/20 p-5">
              <p className="text-sm text-slate-400">Launch readiness</p>
              <p className="mt-2 text-xl font-black text-white">{qa.launch_readiness}</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-black/20 p-5">
              <p className="text-sm text-slate-400">Security readiness</p>
              <p className="mt-2 text-xl font-black text-white">{qa.security_readiness}</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-black/20 p-5">
              <p className="text-sm text-slate-400">Security score</p>
              <p className="mt-2 text-xl font-black text-cyan">{qa.security_score}/100</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-black/20 p-5">
              <p className="text-sm text-slate-400">High priority left</p>
              <p className="mt-2 text-xl font-black text-amber-200">{highPriorityRemaining.length}</p>
            </div>
          </div>

          <div className="mt-5 rounded-3xl border border-cyan/20 bg-cyan/10 p-4 text-sm text-cyan-50">
            {completion.code_side_status}
          </div>
        </section>

        {qa.manual_blockers.length > 0 ? (
          <section className="rounded-[2rem] border border-amber-400/30 bg-amber-500/10 p-6">
            <h2 className="text-2xl font-black text-white">Manual blockers before public launch</h2>
            <ul className="mt-4 space-y-2 text-sm text-amber-100">
              {qa.manual_blockers.map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
          </section>
        ) : null}

        <section className="grid gap-4 lg:grid-cols-2">
          {remaining.map((item) => (
            <article key={item.area} className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full border px-3 py-1 text-xs font-black ${priorityTone(item.priority)}`}>
                  {item.priority}
                </span>
                <span className={`rounded-full border px-3 py-1 text-xs font-black ${statusTone(item.status)}`}>
                  {item.status.replaceAll("_", " ")}
                </span>
              </div>
              <h3 className="mt-4 text-2xl font-black text-white">{item.area}</h3>
              <p className="mt-3 text-sm text-slate-400"><strong className="text-slate-200">Done:</strong> {item.what_is_done}</p>
              <p className="mt-3 text-sm text-amber-100"><strong>Remaining:</strong> {item.remaining_work}</p>
              <p className="mt-3 text-sm text-slate-300"><strong>How:</strong> {item.how_to_complete}</p>
              <p className="mt-3 text-sm text-cyan-100"><strong>Verify:</strong> {item.verify}</p>
            </article>
          ))}
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6">
          <h2 className="text-2xl font-black text-white">External provider readiness</h2>
          <p className="mt-2 text-sm text-slate-400">Providers are live only when keys, webhooks and verification flows are configured. Missing providers must show Not configured / Needs API Key / Manual / Not assessed.</p>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[1000px] text-left text-sm">
              <thead className="text-slate-400">
                <tr>
                  <th className="py-3 pr-4">Provider</th>
                  <th className="py-3 pr-4">Status</th>
                  <th className="py-3 pr-4">Required env/config</th>
                  <th className="py-3 pr-4">Verify</th>
                </tr>
              </thead>
              <tbody>
                {providers.map((provider) => (
                  <tr key={provider.provider} className="border-t border-white/10 align-top">
                    <td className="py-4 pr-4 font-black text-white">{provider.provider}</td>
                    <td className="py-4 pr-4"><span className={`rounded-full border px-3 py-1 text-xs font-black ${statusTone(provider.status)}`}>{provider.status.replaceAll("_", " ")}</span></td>
                    <td className="py-4 pr-4 font-mono text-xs text-cyan-100">{provider.required_env.join(", ")}</td>
                    <td className="py-4 pr-4 text-slate-300">{provider.verify}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6">
            <h2 className="text-2xl font-black text-white">Safe tests to run</h2>
            <ul className="mt-4 space-y-2 text-sm text-slate-300">
              {completion.next_safe_tests.map((item) => <li key={item}>• {item}</li>)}
            </ul>
          </article>
          <article className="rounded-[2rem] border border-red-400/20 bg-red-500/10 p-6">
            <h2 className="text-2xl font-black text-white">Blocked claims/actions</h2>
            <ul className="mt-4 space-y-2 text-sm text-red-100">
              {completion.blocked_claims.map((item) => <li key={item}>• {item}</li>)}
            </ul>
          </article>
        </section>

        <section className="rounded-[2rem] border border-cyan/20 bg-cyan/10 p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-black text-white">Next chat handoff</h2>
              <p className="mt-2 text-sm text-cyan-50/80">Copy this into a new ChatGPT/Claude chat with your latest clean source ZIP or latest error logs.</p>
            </div>
            <button onClick={copyHandoff} className="rounded-2xl bg-cyan px-5 py-3 text-sm font-black text-slate-950">
              {copied ? "Copied" : "Copy handoff"}
            </button>
          </div>
          <pre className="mt-5 max-h-[420px] overflow-auto whitespace-pre-wrap rounded-3xl border border-white/10 bg-black/30 p-4 text-xs leading-5 text-cyan-50">
            {handoff}
          </pre>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6">
          <h2 className="text-2xl font-black text-white">Original implementation map</h2>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <div>
              <h3 className="font-black text-cyan">Real live now</h3>
              <ul className="mt-3 space-y-2 text-sm text-slate-300">{map.real_live_now.map((item) => <li key={item}>• {item}</li>)}</ul>
            </div>
            <div>
              <h3 className="font-black text-red-200">Never collect</h3>
              <ul className="mt-3 space-y-2 text-sm text-red-100">{map.never_collect.map((item) => <li key={item}>• {item}</li>)}</ul>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
