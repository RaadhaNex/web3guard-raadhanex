"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { CommandLoadingState, CommandNotice } from "@/components/ui/CommandState";
import { StatusPill } from "@/components/ui/StatusPill";

type RiskFamily = {
  key: string;
  label: string;
  bug_examples: string[];
  detectable_by: string[];
  confidence: string;
  limitation: string;
};

type RiskStatus = {
  ok: boolean;
  version: string;
  purpose: string;
  reference_scope: {
    cwe_total_weakness_types: number;
    nvd_documented_cve_records_snapshot: number;
    meaning: string;
  };
  detectable_when_configured: string[];
  safe_status_labels: string[];
  blocked_claims: string[];
  required_disclaimer: string;
};

type TaxonomyMap = {
  ok: boolean;
  version: string;
  reference_scope: {
    cwe_total_weakness_types: number;
    nvd_documented_cve_records_snapshot: number;
    note: string;
  };
  families: RiskFamily[];
  not_fully_automatable: string[];
  safe_product_wording: string;
};

type FindingInput = {
  title: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  module: string;
  source: string;
  rule_id?: string;
  cwe_ids?: string[];
  cve_ids?: string[];
  recommendation?: string;
};

type EnhancedFinding = {
  id: string;
  title: string;
  description: string;
  module: string;
  risk_family: string;
  status: string;
  severity: string;
  confidence: string;
  source: string;
  rule_id?: string | null;
  cwe_ids: string[];
  cve_ids: string[];
  priority: string;
  impact: string;
  future_risk: string;
  exploit_scenario: string;
  fix_plan: {
    summary: string;
    priority: string;
    owner: string;
    verify_steps: string[];
  };
  needs_human_review: boolean;
  limitation: string;
};

type RiskAnalysis = {
  ok: boolean;
  version: string;
  analysis_id: string;
  project_name: string;
  generated_at: string;
  input_findings_count: number;
  enhanced_findings_count: number;
  severity_breakdown: Record<string, number>;
  risk_family_breakdown: Record<string, number>;
  priority_summary: Record<string, number>;
  findings: EnhancedFinding[];
  coverage_gaps: Array<{ module: string; label: string; status: string; why_it_matters: string }>;
  taxonomy_reference: { cwe_total_weakness_types: number; nvd_documented_cve_records_snapshot: number; claim_boundary: string };
  recommended_next_action: string;
  safe_report_wording: string;
};

type ClaimResult = {
  ok: boolean;
  violations: string[];
  allowed_rewrite: string;
  required_disclaimer: string;
};

const demoFindings: FindingInput[] = [
  {
    title: "Reentrancy risk in withdraw",
    description: "External call happens before state update in Vault.withdraw.",
    severity: "critical",
    module: "smart_contract",
    source: "Slither",
    rule_id: "reentrancy-eth",
  },
  {
    title: "Razorpay webhook signature missing",
    description: "Payment webhook appears to accept success without verified server-side signature.",
    severity: "high",
    module: "payment_backend",
    source: "Semgrep",
  },
  {
    title: "OSV CVE dependency advisory",
    description: "A known vulnerable dependency version was supplied by the package evidence.",
    severity: "high",
    module: "dependency_intelligence",
    source: "OSV",
    cve_ids: ["CVE-2020-8203"],
  },
];

const assessedDefaults = {
  slither: true,
  semgrep: true,
  osv: true,
  cisa_kev: true,
  github: true,
  website: true,
  api: true,
  wallet_ux: false,
  admin_opsec: false,
  foundry: false,
  echidna: false,
  mythril: false,
};

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mono max-h-96 overflow-auto rounded-2xl border border-white/10 bg-black/35 p-4 text-xs text-slate-300">{JSON.stringify(value, null, 2)}</pre>;
}

function SeverityBadge({ severity }: { severity: string }) {
  const label = severity.toUpperCase();
  return <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[11px] font-black uppercase tracking-[0.16em] text-white">{label}</span>;
}

export function RiskIntelligenceClient() {
  const [status, setStatus] = useState<RiskStatus | null>(null);
  const [taxonomy, setTaxonomy] = useState<TaxonomyMap | null>(null);
  const [analysis, setAnalysis] = useState<RiskAnalysis | null>(null);
  const [claim, setClaim] = useState("Web3Guard provides CWE/NVD-aware pre-audit risk intelligence, not a certified audit.");
  const [claimResult, setClaimResult] = useState<ClaimResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [statusData, taxonomyData] = await Promise.all([
          apiGet<RiskStatus>("/risk-intelligence/status"),
          apiGet<TaxonomyMap>("/risk-intelligence/taxonomy"),
        ]);
        setStatus(statusData);
        setTaxonomy(taxonomyData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load risk intelligence engine");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function runDemoAnalysis() {
    setError(null);
    try {
      const data = await apiPost<RiskAnalysis>("/risk-intelligence/analyze", {
        project_name: "Pilot Web3 Project",
        findings: demoFindings,
        assessed_modules: assessedDefaults,
        real_only_acknowledged: true,
      });
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Risk analysis failed");
    }
  }

  async function checkClaim() {
    setError(null);
    try {
      const data = await apiPost<ClaimResult>("/risk-intelligence/claim-check", {
        text: claim,
        real_only_acknowledged: true,
      });
      setClaimResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claim check failed");
    }
  }

  const topPriorities = useMemo(() => analysis?.findings.filter((item) => item.priority === "P0" || item.priority === "P1") ?? [], [analysis]);

  if (loading) return <CommandLoadingState label="Loading CWE/NVD-aware risk intelligence..." />;

  return (
    <section className="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      {error ? <div className="lg:col-span-2"><CommandNotice tone="danger" title="Risk intelligence error" text={error} /></div> : null}

      <div className="space-y-6">
        <article className="clean-panel p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="section-label">Reference coverage</p>
              <h2 className="mt-2 text-2xl font-black text-white">CWE/NVD map-aware, not all-bug guaranteed.</h2>
            </div>
            <StatusPill status="Real-only" />
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-4xl font-black tracking-[-0.07em] text-white">{status?.reference_scope.cwe_total_weakness_types}</p>
              <p className="mt-1 text-xs font-bold uppercase tracking-[0.16em] text-slate-500">CWE weakness types reference</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-4xl font-black tracking-[-0.07em] text-white">{status?.reference_scope.nvd_documented_cve_records_snapshot.toLocaleString()}+</p>
              <p className="mt-1 text-xs font-bold uppercase tracking-[0.16em] text-slate-500">NVD CVE records snapshot</p>
            </div>
          </div>
          <p className="mt-4 text-sm leading-7 text-slate-400">{status?.reference_scope.meaning}</p>
        </article>

        <article className="clean-panel p-6">
          <p className="section-label">Run demo risk intelligence</p>
          <h3 className="mt-2 text-xl font-black text-white">Convert findings into impact + future risk + fix plan.</h3>
          <p className="mt-3 text-sm leading-7 text-slate-400">
            This demo uses sample evidence-style findings. Real scans must pass actual Slither/Semgrep/OSV/CISA evidence; empty input never becomes a fake pass.
          </p>
          <button type="button" onClick={runDemoAnalysis} className="btn-primary mt-5 w-full">Analyze sample findings</button>
        </article>

        <article className="clean-panel p-6">
          <p className="section-label">Unsafe claim blocker</p>
          <textarea
            value={claim}
            onChange={(event) => setClaim(event.target.value)}
            className="mt-3 min-h-28 w-full rounded-2xl border border-white/10 bg-black/35 p-4 text-sm text-white outline-none transition focus:border-cyan/40"
          />
          <button type="button" onClick={checkClaim} className="btn-secondary mt-3 w-full">Check wording</button>
          {claimResult ? (
            <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm font-black text-white">{claimResult.ok ? "Safe wording" : "Unsafe wording blocked"}</p>
              {claimResult.violations.length ? <p className="mt-2 text-sm text-rose-200">Blocked: {claimResult.violations.join(", ")}</p> : null}
              <p className="mt-2 text-sm leading-6 text-slate-400">{claimResult.allowed_rewrite}</p>
            </div>
          ) : null}
        </article>
      </div>

      <div className="space-y-6">
        <article className="clean-panel p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-label">Bug families covered when configured</p>
              <h2 className="mt-2 text-2xl font-black text-white">150–250+ practical checks can be explained, not guaranteed.</h2>
            </div>
            <Link href="/scanner-depth" className="btn-secondary">Coverage depth</Link>
          </div>
          <div className="mt-5 grid gap-3">
            {taxonomy?.families.map((family) => (
              <details key={family.key} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <summary className="cursor-pointer text-sm font-black text-white">{family.label}</summary>
                <div className="mt-3 grid gap-3 text-sm leading-6 text-slate-400">
                  <p><span className="font-bold text-slate-200">Examples:</span> {family.bug_examples.join(", ")}</p>
                  <p><span className="font-bold text-slate-200">Detected by:</span> {family.detectable_by.join(", ")}</p>
                  <p><span className="font-bold text-slate-200">Limit:</span> {family.limitation}</p>
                </div>
              </details>
            ))}
          </div>
        </article>

        {analysis ? (
          <article className="clean-panel p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="section-label">Analysis result</p>
                <h2 className="mt-2 text-2xl font-black text-white">{analysis.enhanced_findings_count} findings explained</h2>
              </div>
              <StatusPill status={`P0 ${analysis.priority_summary.p0} · P1 ${analysis.priority_summary.p1}`} />
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-400">{analysis.recommended_next_action}</p>

            <div className="mt-5 grid gap-4">
              {topPriorities.map((finding) => (
                <div key={finding.id} className="rounded-2xl border border-white/10 bg-black/25 p-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <SeverityBadge severity={finding.severity} />
                    <StatusPill status={finding.priority} />
                    {finding.needs_human_review ? <StatusPill status="Manual review" /> : null}
                  </div>
                  <h3 className="mt-3 text-lg font-black text-white">{finding.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{finding.impact}</p>
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                      <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Future risk</p>
                      <p className="mt-2 text-sm leading-6 text-slate-300">{finding.future_risk}</p>
                    </div>
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                      <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">Fix</p>
                      <p className="mt-2 text-sm leading-6 text-slate-300">{finding.fix_plan.summary}</p>
                    </div>
                  </div>
                  <p className="mt-3 text-xs leading-5 text-slate-500">CWE: {finding.cwe_ids.join(", ") || "Mapped by context"}</p>
                </div>
              ))}
            </div>

            <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm font-black text-white">Coverage gaps</p>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {analysis.coverage_gaps.slice(0, 8).map((gap) => (
                  <div key={gap.module} className="rounded-xl bg-black/25 p-3 text-xs leading-5 text-slate-400">
                    <span className="font-bold text-slate-200">{gap.label}:</span> {gap.status}
                  </div>
                ))}
              </div>
            </div>

            <details className="mt-5">
              <summary className="cursor-pointer text-sm font-bold text-slate-300">Raw normalized JSON</summary>
              <div className="mt-3"><JsonBlock value={analysis} /></div>
            </details>
          </article>
        ) : (
          <article className="clean-panel p-6">
            <p className="section-label">No analysis run yet</p>
            <h2 className="mt-2 text-2xl font-black text-white">Run the demo or call the API with real findings.</h2>
            <p className="mt-3 text-sm leading-7 text-slate-400">The API accepts real Slither/Semgrep/OSV/CISA/manual findings and returns detailed bug impact, future risk, and fix guidance.</p>
          </article>
        )}

        <article className="clean-panel p-6">
          <p className="section-label">Never automated completely</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {taxonomy?.not_fully_automatable.map((item) => (
              <span key={item} className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-2 text-xs font-bold text-slate-300">{item}</span>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}
