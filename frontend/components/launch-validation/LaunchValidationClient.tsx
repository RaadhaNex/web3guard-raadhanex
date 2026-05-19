"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";

type Gate = { key: string; passed: boolean; status: string };
type PhaseStatus = {
  ok: boolean;
  version: string;
  phase: string;
  summary: string;
  gates: Gate[];
  passed_gates: number;
  total_gates: number;
  visible_journey: Array<{ label: string; href: string; purpose: string }>;
  safe_missing_labels: string[];
  next_30_days: string[];
};

type SlitherReadiness = {
  status: string;
  detected_path?: string | null;
  render_build_command: string;
  render_env_to_set: string[];
  real_only_note: string;
};

type RazorpayReadiness = {
  status: string;
  razorpay_enabled: boolean;
  payment_mode: string;
  detected_mode: string;
  missing_env: string[];
  test_mode_ready: boolean;
  test_checklist: string[];
};

type DependencyIntel = {
  status: string;
  package_count: number;
  packages: Array<{ name: string; version?: string | null; ecosystem?: string | null }>;
  live_lookup_requested: boolean;
  network_enabled: boolean;
  osv_results: Array<{
    package: { name: string; version?: string | null; ecosystem?: string | null };
    vulnerability_count: number;
    vulnerabilities: Array<{ id?: string; summary?: string; aliases?: string[] }>;
  }>;
  osv_vulnerability_count?: number;
  cisa_kev_matches: Array<{ cve: string; vendorProject?: string; product?: string; dateAdded?: string; requiredAction?: string }>;
  next_step?: string;
  error?: string;
  real_only_note: string;
};

const defaultPackageJson = `{
  "dependencies": {
    "ethers": "^6.13.4",
    "next": "16.2.6"
  }
}`;

function statusClass(status: string) {
  const lower = status.toLowerCase();
  if (lower.includes("ready") || lower.includes("assessed")) return "badge badge-green";
  if (lower.includes("key") || lower.includes("configured") || lower.includes("installed")) return "badge badge-amber";
  return "badge";
}

export function LaunchValidationClient() {
  const [status, setStatus] = useState<PhaseStatus | null>(null);
  const [slither, setSlither] = useState<SlitherReadiness | null>(null);
  const [razorpay, setRazorpay] = useState<RazorpayReadiness | null>(null);
  const [packageJson, setPackageJson] = useState(defaultPackageJson);
  const [liveLookup, setLiveLookup] = useState(false);
  const [intel, setIntel] = useState<DependencyIntel | null>(null);
  const [loadingIntel, setLoadingIntel] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiGet<PhaseStatus>("/launch-validation/status"),
      apiGet<SlitherReadiness>("/launch-validation/slither-readiness"),
      apiGet<RazorpayReadiness>("/launch-validation/razorpay-readiness"),
    ])
      .then(([phase, slitherStatus, razorpayStatus]) => {
        setStatus(phase);
        setSlither(slitherStatus);
        setRazorpay(razorpayStatus);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load launch validation status"));
  }, []);

  const failedGates = useMemo(() => status?.gates.filter((gate) => !gate.passed) ?? [], [status]);

  async function runDependencyIntel() {
    setLoadingIntel(true);
    setError(null);
    try {
      const data = await apiPost<DependencyIntel>("/launch-validation/dependency-intel", {
        package_json: packageJson,
        live_lookup: liveLookup,
        real_only_acknowledged: true,
        limit: 40,
      });
      setIntel(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dependency intelligence check failed");
    } finally {
      setLoadingIntel(false);
    }
  }

  return (
    <main className="relative overflow-hidden">
      <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
          <div className="quantum-stage p-6 sm:p-8">
            <p className="section-label">Phase 31</p>
            <h1 className="mt-3 text-4xl font-black tracking-[-0.05em] sm:text-5xl">
              Real launch compression + revenue validation sprint.
            </h1>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-base">
              This sprint reduces the visible journey to seven user paths and focuses on real validation: Slither readiness, Razorpay test-mode readiness, and OSV/CISA dependency intelligence. No fake scanner/provider output is generated.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              {status?.safe_missing_labels.map((label) => (
                <span key={label} className={statusClass(label)}>{label}</span>
              ))}
            </div>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/scanner/unified-url" className="btn-primary">Start scanner →</Link>
              <Link href="/pricing" className="btn-secondary">Validate payment path</Link>
              <Link href="/docs" className="btn-secondary">Open docs</Link>
            </div>
          </div>

          <div className="grid gap-4">
            <div className="glass-tile p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-black text-white">Launch validation gates</p>
                  <p className="mt-1 text-xs text-slate-500">Passed gates are environment-dependent; failed gates are not hidden.</p>
                </div>
                <span className="badge badge-cyan">{status ? `${status.passed_gates}/${status.total_gates}` : "loading"}</span>
              </div>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {status?.gates.map((gate) => (
                  <div key={gate.key} className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-3">
                    <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">{gate.key.replaceAll("_", " ")}</p>
                    <p className="mt-2 text-sm font-bold text-white">{gate.status}</p>
                  </div>
                ))}
              </div>
              {failedGates.length ? (
                <p className="mt-4 text-xs leading-6 text-amber-100/80">
                  Failed/pending gates are expected until Render Slither, Razorpay keys, and live OSV/CISA flags are configured.
                </p>
              ) : null}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="glass-tile p-5">
                <p className="text-sm font-black text-white">Slither on Render</p>
                <span className={statusClass(slither?.status ?? "loading")}>{slither?.status ?? "loading"}</span>
                <p className="mt-3 text-xs leading-6 text-slate-400">{slither?.real_only_note}</p>
                <pre className="mt-3 overflow-x-auto rounded-2xl border border-white/[0.07] bg-black/30 p-3 text-[11px] text-slate-300">{slither?.render_build_command}</pre>
              </div>
              <div className="glass-tile p-5">
                <p className="text-sm font-black text-white">Razorpay test readiness</p>
                <span className={statusClass(razorpay?.status ?? "loading")}>{razorpay?.status ?? "loading"}</span>
                <p className="mt-3 text-xs text-slate-400">Mode: {razorpay?.detected_mode ?? "unknown"} · Payment mode: {razorpay?.payment_mode ?? "unknown"}</p>
                {razorpay?.missing_env.length ? (
                  <p className="mt-3 text-xs leading-6 text-amber-100/80">Missing: {razorpay.missing_env.join(", ")}</p>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-cyan/10 bg-cyan/[0.025]">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="section-label">7 visible paths</p>
              <h2 className="mt-3 text-3xl font-black">Keep public navigation simple. Preserve advanced modules in docs/search.</h2>
            </div>
            <Link href="/docs" className="btn-secondary">Advanced docs</Link>
          </div>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {status?.visible_journey.map((item) => (
              <Link key={item.href} href={item.href} className="glass-tile p-5 transition hover:-translate-y-1">
                <p className="text-base font-black text-white">{item.label}</p>
                <p className="mt-2 text-sm leading-6 text-slate-400">{item.purpose}</p>
                <p className="mt-4 text-xs font-bold text-cyan">{item.href}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="section-label">OSV + CISA KEV starter</p>
            <h2 className="mt-3 text-3xl font-black">Check dependency intelligence without fake vulnerabilities.</h2>
            <p className="mt-4 text-sm leading-7 text-slate-400">
              Paste package.json. By default Web3Guard only parses packages and returns Not assessed yet. Turn on live lookup only after backend env enables network calls.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button type="button" className="btn-primary" onClick={runDependencyIntel} disabled={loadingIntel}>
                {loadingIntel ? "Checking..." : "Run dependency intel"}
              </button>
              <label className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.04] px-4 py-2 text-xs font-bold text-slate-300">
                <input type="checkbox" checked={liveLookup} onChange={(event) => setLiveLookup(event.target.checked)} />
                Live lookup
              </label>
            </div>
            {error ? <p className="mt-4 rounded-2xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</p> : null}
          </div>
          <div className="grid gap-4">
            <textarea
              value={packageJson}
              onChange={(event) => setPackageJson(event.target.value)}
              className="min-h-[220px] rounded-[24px] border border-white/[0.08] bg-black/35 p-4 font-mono text-xs leading-6 text-slate-200 outline-none transition focus:border-cyan/40"
              spellCheck={false}
            />
            {intel ? (
              <div className="glass-tile p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-sm font-black text-white">Dependency intelligence result</p>
                  <span className={statusClass(intel.status)}>{intel.status}</span>
                </div>
                <p className="mt-3 text-xs leading-6 text-slate-400">{intel.real_only_note}</p>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-3">
                    <p className="text-xs text-slate-500">Packages</p>
                    <p className="text-xl font-black text-white">{intel.package_count}</p>
                  </div>
                  <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-3">
                    <p className="text-xs text-slate-500">OSV vulns</p>
                    <p className="text-xl font-black text-white">{intel.osv_vulnerability_count ?? 0}</p>
                  </div>
                  <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-3">
                    <p className="text-xs text-slate-500">CISA KEV</p>
                    <p className="text-xl font-black text-white">{intel.cisa_kev_matches.length}</p>
                  </div>
                </div>
                {intel.next_step ? <p className="mt-4 text-xs leading-6 text-amber-100/80">{intel.next_step}</p> : null}
                {intel.error ? <p className="mt-4 text-xs leading-6 text-red-100">{intel.error}</p> : null}
              </div>
            ) : null}
          </div>
        </div>
      </section>
    </main>
  );
}
