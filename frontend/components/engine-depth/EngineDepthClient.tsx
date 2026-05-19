"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { CommandEmptyState, CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";

type EngineItem = {
  name: string;
  category: string;
  status: string;
  installed?: boolean;
  enabled_by_env?: boolean;
  will_run?: boolean;
  configured?: boolean;
  path?: string | null;
  safe_note?: string;
  details?: Record<string, unknown>;
};

type EngineDepthStatus = {
  ok: boolean;
  version: string;
  ready_count: number;
  total_count: number;
  readiness_label: string;
  static_tools: EngineItem[];
  deep_tools: EngineItem[];
  provider_integrations: EngineItem[];
  recommended_next_env: string[];
  safety_boundaries: Record<string, boolean>;
};

function statusClass(status: string) {
  const value = status.toLowerCase();
  if (value.includes("ready")) return "badge-green";
  if (value.includes("needs") || value.includes("not installed") || value.includes("not configured") || value.includes("manual")) return "badge-amber";
  return "badge-cyan";
}

function EngineCard({ item }: { item: EngineItem }) {
  return (
    <article className="glass-tile p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">{item.category.replaceAll("_", " ")}</p>
          <h3 className="mt-2 text-xl font-black text-white">{item.name}</h3>
        </div>
        <span className={`badge ${statusClass(item.status)}`}>{item.status}</span>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-400">{item.safe_note || "Real-only status item."}</p>
      <div className="mt-4 grid gap-2 text-xs text-slate-400 sm:grid-cols-2">
        {typeof item.installed === "boolean" ? <p><strong className="text-white">Installed:</strong> {item.installed ? "yes" : "no"}</p> : null}
        {typeof item.enabled_by_env === "boolean" ? <p><strong className="text-white">Env enabled:</strong> {item.enabled_by_env ? "yes" : "no"}</p> : null}
        {typeof item.will_run === "boolean" ? <p><strong className="text-white">Will run:</strong> {item.will_run ? "yes" : "no"}</p> : null}
        {typeof item.configured === "boolean" ? <p><strong className="text-white">Configured:</strong> {item.configured ? "yes" : "no"}</p> : null}
        {item.path ? <p className="sm:col-span-2"><strong className="text-white">Path:</strong> <span className="break-all">{item.path}</span></p> : null}
      </div>
    </article>
  );
}

export function EngineDepthClient() {
  const [status, setStatus] = useState<EngineDepthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<EngineDepthStatus>("/engine-depth/status");
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load engine status.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const allItems = useMemo(() => {
    if (!status) return [];
    return [...status.static_tools, ...status.deep_tools, ...status.provider_integrations];
  }, [status]);

  if (loading) return <CommandLoadingState label="Loading real engine status..." />;

  if (error) {
    return (
      <div className="grid gap-4">
        <CommandNotice
          tone="warning"
          title="Engine status could not be loaded"
          text={error}
        />
        <button type="button" className="btn-secondary w-fit" onClick={() => void load()}>Retry</button>
      </div>
    );
  }

  if (!status) return <CommandEmptyState title="No engine status available" text="The backend did not return a status payload." />;

  return (
    <section className="mt-8 space-y-8">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Ready engines</p>
          <p className="mt-2 text-3xl font-black text-white">{status.ready_count}/{status.total_count}</p>
          <p className="mt-2 text-sm text-slate-400">{status.readiness_label}</p>
        </div>
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Policy</p>
          <p className="mt-2 text-2xl font-black text-white">Real-only</p>
          <p className="mt-2 text-sm text-slate-400">No fake tool output, no exploit automation, no wallet signing.</p>
        </div>
        <div className="stat-slab p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Next action</p>
          <p className="mt-2 text-2xl font-black text-white">Configure workers</p>
          <p className="mt-2 text-sm text-slate-400">Enable tools only on isolated workers after install/testing.</p>
        </div>
      </div>

      <div>
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="section-label">Tool matrix</p>
            <h2 className="mt-2 text-3xl font-black">Static, deep, and provider readiness</h2>
          </div>
          <Link href="/scanner/static-analysis" className="btn-secondary">Open static scanner</Link>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          {allItems.map((item) => <EngineCard key={`${item.category}-${item.name}`} item={item} />)}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
        <div className="glass-tile p-6">
          <p className="section-label">Recommended backend env</p>
          <div className="mt-4 grid gap-3">
            {status.recommended_next_env.map((line) => (
              <p key={line} className="command-line text-sm text-slate-300"><span className="kbd-chip">ENV</span>{line}</p>
            ))}
          </div>
        </div>
        <div className="glass-tile p-6">
          <p className="section-label">Safety boundaries</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {Object.entries(status.safety_boundaries).map(([key, value]) => (
              <span key={key} className={`badge ${value ? "badge-green" : "badge-red"}`}>{key.replaceAll("_", " ")}: {value ? "yes" : "no"}</span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
