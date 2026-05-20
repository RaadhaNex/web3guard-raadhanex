"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

function jsonPreview(value: unknown) {
  try { return JSON.stringify(value, null, 2); } catch { return String(value); }
}

export function StaticArtifactBridgeClient() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [slitherJson, setSlitherJson] = useState("");
  const [semgrepJson, setSemgrepJson] = useState("");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiGet<Record<string, unknown>>("/static-artifact/status").then(setStatus).catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  async function parseArtifacts() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data = await apiPost<Record<string, unknown>>("/static-artifact/parse", {
        project_name: "Manual artifact parse",
        slither_json: slitherJson.trim() || null,
        semgrep_json: semgrepJson.trim() || null,
        real_only_acknowledged: true,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-cyan-300/15 bg-slate-950/70 p-6 shadow-2xl shadow-cyan-950/20 sm:p-8">
        <p className="section-label">Phase 50</p>
        <h1 className="mt-3 text-4xl font-black tracking-[-0.05em] text-white sm:text-5xl">Static Analysis Artifact Bridge</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300">
          Paste real Slither/Semgrep JSON output and Web3Guard will parse it as tool evidence. This does not claim certified audit status or fake backend execution.
        </p>
        {status ? <pre className="mt-5 max-h-52 overflow-auto rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{jsonPreview(status)}</pre> : null}
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-2">
        <label className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <span className="text-sm font-black text-white">Slither JSON</span>
          <textarea className="textarea mt-3 min-h-[260px]" value={slitherJson} onChange={(event) => setSlitherJson(event.target.value)} placeholder='{ "results": { "detectors": [...] } }' />
        </label>
        <label className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          <span className="text-sm font-black text-white">Semgrep JSON</span>
          <textarea className="textarea mt-3 min-h-[260px]" value={semgrepJson} onChange={(event) => setSemgrepJson(event.target.value)} placeholder='{ "results": [...] }' />
        </label>
      </section>

      <div className="mt-5 flex flex-wrap gap-3">
        <button type="button" className="btn-primary" onClick={() => void parseArtifacts()} disabled={loading}>{loading ? "Parsing..." : "Parse real artifacts"}</button>
        <a className="btn-secondary" href="/scanner/unified-url">Use inside unified scan</a>
      </div>
      {error ? <p className="mt-5 rounded-2xl border border-red-400/20 bg-red-500/10 p-4 text-sm text-red-100">{error}</p> : null}
      {result ? (
        <section className="mt-6 rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-2xl font-black text-white">Parsed artifact result</h2>
          <pre className="mt-4 max-h-[520px] overflow-auto whitespace-pre-wrap break-words rounded-2xl border border-white/10 bg-black/30 p-4 text-xs text-slate-300">{jsonPreview(result)}</pre>
        </section>
      ) : null}
    </main>
  );
}
