"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="mt-4 max-h-[520px] overflow-auto rounded-2xl border border-white/10 bg-black/35 p-4 text-xs leading-5 text-slate-200">{JSON.stringify(value, null, 2)}</pre>;
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-[1.6rem] border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/20">
      <h2 className="text-xl font-black text-white">{title}</h2>
      {children}
    </section>
  );
}

export function AccuracyUpgradeClient() {
  const [status, setStatus] = useState<unknown>(null);
  const [packageJson, setPackageJson] = useState("");
  const [solidityCode, setSolidityCode] = useState("");
  const [apiEvidence, setApiEvidence] = useState('[{"endpoint":"/admin","status_code":200,"role":"anonymous","expected_access":"admin only","response_hash":"sha256-demo"}]');
  const [walletEvidence, setWalletEvidence] = useState('{"expected_chain_id":"1","copy":"Connect wallet only. Never enter seed phrase."}');
  const [output, setOutput] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet("/accuracy-upgrade/status").then(setStatus).catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  async function run(path: string, body: unknown) {
    setError(null);
    setOutput(null);
    try {
      setOutput(await apiPost(path, body));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="rounded-[2rem] border border-cyan-300/15 bg-slate-950/75 p-6 shadow-2xl shadow-cyan-950/20 sm:p-8">
        <p className="text-xs font-black uppercase tracking-[0.28em] text-cyan-200/80">Phases 52–58</p>
        <h1 className="mt-4 max-w-5xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">Accuracy upgrade engines</h1>
        <p className="mt-4 max-w-4xl text-sm leading-7 text-slate-300 sm:text-base">
          This hub connects real dependency advisory lookup, backend static tool execution, authorized API evidence, wallet-flow evidence, business-logic review, DeFi simulation artifacts, and reviewed-report confirmation. Missing evidence stays Not Assessed; no certified-audit or all-bugs claim is made.
        </p>
      </section>

      {error ? <div className="mt-6 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</div> : null}

      <section className="mt-8 grid gap-5 lg:grid-cols-2">
        <Card title="52 — GitHub + OSV dependency evidence">
          <p className="mt-2 text-sm text-slate-400">Paste package.json. Vulnerabilities are returned only from OSV provider output.</p>
          <textarea className="textarea mt-4 min-h-[160px]" value={packageJson} onChange={(e) => setPackageJson(e.target.value)} placeholder='{ "dependencies": { "lodash": "4.17.20" } }' />
          <button className="btn-primary mt-4" onClick={() => void run("/accuracy-upgrade/dependency-osv", { package_json: packageJson })}>Run OSV evidence check</button>
        </Card>

        <Card title="53 — Backend Slither/Semgrep worker">
          <p className="mt-2 text-sm text-slate-400">Runs only when backend tools are installed/enabled. Otherwise it reports Tool/Provider state.</p>
          <textarea className="textarea mt-4 min-h-[160px]" value={solidityCode} onChange={(e) => setSolidityCode(e.target.value)} placeholder="Paste Solidity source" />
          <button className="btn-primary mt-4" onClick={() => void run("/accuracy-upgrade/static-worker", { solidity_code: solidityCode, project_name: "Accuracy check" })}>Run static worker bridge</button>
        </Card>

        <Card title="54 — Authorized API evidence">
          <p className="mt-2 text-sm text-slate-400">Only supplied/authorized observations become proof. No brute force or bypass automation.</p>
          <textarea className="textarea mt-4 min-h-[150px]" value={apiEvidence} onChange={(e) => setApiEvidence(e.target.value)} />
          <button className="btn-primary mt-4" onClick={() => void run("/accuracy-upgrade/api-evidence", { observations: JSON.parse(apiEvidence || "[]"), authorization_confirmed: true })}>Evaluate API evidence</button>
        </Card>

        <Card title="55 — Wallet UX evidence">
          <p className="mt-2 text-sm text-slate-400">No wallet signing. Paste copied wallet-flow evidence or sample transactions/signatures.</p>
          <textarea className="textarea mt-4 min-h-[150px]" value={walletEvidence} onChange={(e) => setWalletEvidence(e.target.value)} />
          <button className="btn-primary mt-4" onClick={() => void run("/accuracy-upgrade/wallet-evidence", { wallet_evidence: JSON.parse(walletEvidence || "{}"), authorization_confirmed: true })}>Evaluate wallet evidence</button>
        </Card>

        <Card title="56 — Business logic review builder">
          <p className="mt-2 text-sm text-slate-400">Creates manual proof test cases for roles, paid unlocks, rewards, and object ownership.</p>
          <button className="btn-primary mt-4" onClick={() => void run("/accuracy-upgrade/business-logic", { business_context: { roles: ["owner", "user"], critical_actions: ["report unlock", "delete project"], asset_flows: ["₹999 payment unlock"] }, authorization_confirmed: true })}>Build test plan</button>
        </Card>

        <Card title="57–58 — Simulation + reviewed confirmation">
          <p className="mt-2 text-sm text-slate-400">Local/testnet simulation artifacts can confirm economic failures. Reviewed report requires triage/payment/reviewer gates.</p>
          <div className="mt-4 flex flex-wrap gap-3">
            <button className="btn-secondary" onClick={() => void run("/accuracy-upgrade/defi-simulation", { simulation_result: { invariants: [{ name: "total assets conserved", passed: false, severity: "high", evidence: "local fork invariant failed" }] }, authorization_confirmed: true })}>Check simulation artifact</button>
            <button className="btn-secondary" onClick={() => void run("/accuracy-upgrade/reviewed-confirmation", { review_context: { reviewer: "Manual reviewer", triaged_findings_count: 8, unresolved_critical_high_count: 0, payment_verified: true } })}>Check reviewed confirmation</button>
          </div>
        </Card>
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-2">
        <Card title="Status">
          <JsonBlock value={status} />
        </Card>
        <Card title="Output">
          <JsonBlock value={output || { note: "Run one engine to see real evidence output." }} />
        </Card>
      </section>
    </main>
  );
}
