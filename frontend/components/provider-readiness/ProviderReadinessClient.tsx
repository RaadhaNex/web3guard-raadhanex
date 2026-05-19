"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";

type ProviderItem = {
  key: string;
  name: string;
  status: string;
  configured: boolean;
  masked_credential?: string | null;
  api_base?: string;
  live_endpoint?: string;
  what_it_enables?: string[];
  not_claimed?: string[];
  details?: Record<string, unknown>;
};

type ProviderReadiness = {
  ok: boolean;
  version: string;
  ready_count: number;
  total_count: number;
  readiness_label: string;
  providers: ProviderItem[];
  safe_env_to_add: string[];
  safety_boundaries: Record<string, boolean>;
  chain_matrix?: Record<string, unknown>;
};

function statusClass(status: string) {
  const s = status.toLowerCase();
  if (s.includes("ready")) return "badge badge-green";
  if (s.includes("needs")) return "badge badge-amber";
  if (s.includes("not configured")) return "badge badge-purple";
  return "badge badge-cyan";
}

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="mono max-h-80 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs leading-5 text-slate-300">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

export function ProviderReadinessClient() {
  const [data, setData] = useState<ProviderReadiness | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setData(await apiGet<ProviderReadiness>("/provider-readiness/status"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load provider readiness status.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
        <aside className="space-y-5">
          <section className="glass-tile p-6">
            <p className="section-label">Provider readiness</p>
            <h2 className="mt-3 text-2xl font-black text-white">Real external data only.</h2>
            <p className="mt-3 text-sm leading-7 text-slate-400">
              This board tells you if Etherscan, GoPlus, and GitHub provider layers are actually available. Missing keys stay visible instead of producing fake scores.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <button className="btn-secondary" onClick={() => void load()} disabled={loading}>Refresh status</button>
              <Link href="/engine-depth" className="btn-secondary">Engine depth</Link>
            </div>
          </section>

          <section className="glass-tile p-6">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan">Safe env checklist</p>
            <div className="mt-4 space-y-3">
              {(data?.safe_env_to_add || ["Load backend status first."]).map((item) => (
                <div key={item} className="command-line text-sm text-slate-300">
                  <span className="kbd-chip">ENV</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="glass-tile p-6">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan">Never changed by providers</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {Object.entries(data?.safety_boundaries || {
                no_fake_provider_data: true,
                no_wallet_signing: true,
                no_private_key_collection: true,
                not_certified_audit: true,
              }).map(([key, value]) => (
                <span key={key} className={value ? "badge badge-green" : "badge badge-red"}>{key.replaceAll("_", " ")}</span>
              ))}
            </div>
          </section>
        </aside>

        <section className="space-y-5">
          {loading ? <div className="glass-tile p-6 text-slate-400">Loading provider status...</div> : null}
          {error ? <div className="glass-tile border-red-400/30 bg-red-500/10 p-6 text-red-100">{error}</div> : null}

          {data ? (
            <>
              <div className="quantum-stage p-6 sm:p-8">
                <p className="text-xs font-black uppercase tracking-[0.22em] text-cyan">{data.version}</p>
                <h2 className="mt-3 text-3xl font-black text-white">{data.readiness_label}</h2>
                <p className="mt-3 text-sm leading-7 text-slate-400">
                  {data.ready_count} of {data.total_count} provider layers are ready on this backend.
                </p>
                <div className="mt-5 h-3 overflow-hidden rounded-full border border-cyan/20 bg-white/[0.05]">
                  <div className="h-full rounded-full bg-gradient-to-r from-cyan to-blue-500" style={{ width: `${Math.max(8, Math.round((data.ready_count / Math.max(1, data.total_count)) * 100))}%` }} />
                </div>
              </div>

              <div className="grid gap-5">
                {data.providers.map((provider) => (
                  <article key={provider.key} className="glass-tile p-6">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <p className="mono text-xs font-black uppercase tracking-[0.18em] text-slate-500">{provider.key}</p>
                        <h3 className="mt-2 text-2xl font-black text-white">{provider.name}</h3>
                        <p className="mt-2 text-sm text-slate-500">Endpoint: <span className="text-slate-300">{provider.live_endpoint}</span></p>
                        <p className="mt-1 text-sm text-slate-500">Base: <span className="text-slate-300">{provider.api_base || "internal"}</span></p>
                      </div>
                      <span className={statusClass(provider.status)}>{provider.status}</span>
                    </div>

                    <div className="mt-5 grid gap-4 lg:grid-cols-2">
                      <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                        <p className="text-sm font-black text-white">What it enables</p>
                        <ul className="mt-3 space-y-2 text-sm text-slate-400">
                          {(provider.what_it_enables || []).map((item) => <li key={item}>• {item}</li>)}
                        </ul>
                      </div>
                      <div className="rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4">
                        <p className="text-sm font-black text-amber-100">Not claimed</p>
                        <ul className="mt-3 space-y-2 text-sm text-amber-50/80">
                          {(provider.not_claimed || []).map((item) => <li key={item}>• {item}</li>)}
                        </ul>
                      </div>
                    </div>

                    <details className="mt-5 rounded-2xl border border-white/10 bg-black/20 p-4">
                      <summary className="cursor-pointer text-sm font-black text-cyan">Provider details JSON</summary>
                      <div className="mt-4"><JsonBlock value={provider.details || {}} /></div>
                    </details>
                  </article>
                ))}
              </div>
            </>
          ) : null}
        </section>
      </div>
    </div>
  );
}
