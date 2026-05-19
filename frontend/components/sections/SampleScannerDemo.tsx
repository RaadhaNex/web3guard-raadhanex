import Link from "next/link";

const findings = [
  { sev: "critical", rule: "WG-SOL-REENT-001", surface: "Contract", title: "Reentrancy in withdraw()", fix: "Move balance update before the external call and add a reentrancy guard." },
  { sev: "critical", rule: "WG-SOL-TRANSFER-002", surface: "Contract", title: "Unrestricted transferFrom-like flow", fix: "Check allowance and role boundaries before token movement." },
  { sev: "high", rule: "WG-ADMIN-001", surface: "Admin", title: "Single owner controls launch-critical functions", fix: "Move ownership to a multisig and publish signer policy." },
  { sev: "high", rule: "WG-WALLET-004", surface: "Wallet UX", title: "Approval intent not explained to user", fix: "Display spender, chain, amount, and revocation link before signature." },
  { sev: "medium", rule: "WG-WEB-CSP-001", surface: "Website", title: "Content-Security-Policy evidence missing", fix: "Add a strict CSP and test it before launch." },
];

const sevCls: Record<string, string> = {
  critical: "sev-critical",
  high: "sev-high",
  medium: "sev-medium",
  low: "sev-low",
};

export function SampleScannerDemo() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mb-8 text-center">
        <p className="section-label justify-center">Sample scanner demo</p>
        <h2 className="mt-3 text-3xl font-black sm:text-4xl">VS Code-style review. Serious audit-style output.</h2>
        <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-400">
          Demo content is static for the landing page. Real scan results are generated only from evidence you submit.
        </p>
      </div>

      <div className="card-glow overflow-hidden rounded-2xl">
        <div className="grid gap-0 lg:grid-cols-[1fr_440px]">
          <div className="border-b border-white/[0.07] p-5 lg:border-b-0 lg:border-r lg:p-7">
            <div className="overflow-hidden rounded-xl border border-white/[0.07] bg-[#050811]">
              <div className="flex items-center justify-between border-b border-white/[0.07] px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-red-400" />
                  <span className="h-3 w-3 rounded-full bg-yellow-300" />
                  <span className="h-3 w-3 rounded-full bg-emerald-400" />
                </div>
                <span className="mono text-xs text-slate-500">VulnToken.sol</span>
              </div>
              <pre className="mono overflow-auto p-4 text-[12px] leading-6 text-slate-300 sm:p-5">
<span className="text-slate-600">01</span> <span className="text-purple-300">contract</span> <span className="text-cyan-200">VulnToken</span> {'{'}{"\n"}
<span className="text-slate-600">02</span>   <span className="text-purple-300">mapping</span>(address =&gt; uint256) <span className="text-cyan-200">balances</span>;{"\n"}
<span className="text-slate-600">03</span>   address <span className="text-cyan-200">owner</span>;{"\n\n"}
<span className="text-slate-600">04</span>   <span className="text-purple-300">function</span> <span className="text-cyan-200">withdraw</span>() public {'{'}{"\n"}
<span className="text-slate-600">05</span>     (bool ok,) = msg.sender.call{'{'}value: balances[msg.sender]{'}'}(<span className="text-emerald-300">""</span>);{"\n"}
<span className="text-slate-600">06</span>     <span className="text-orange-300">require</span>(ok);{"\n"}
<span className="text-slate-600">07</span>     balances[msg.sender] = 0; <span className="text-red-300">// too late</span>{"\n"}
<span className="text-slate-600">08</span>   {'}'}{"\n\n"}
<span className="text-slate-600">09</span>   <span className="text-purple-300">function</span> <span className="text-cyan-200">setOwner</span>(address a) public {'{'}{"\n"}
<span className="text-slate-600">10</span>     <span className="text-orange-300">require</span>(tx.origin == owner);{"\n"}
<span className="text-slate-600">11</span>     owner = a;{"\n"}
<span className="text-slate-600">12</span>   {'}'}{"\n"}
<span className="text-slate-600">13</span> {'}'}
              </pre>
            </div>

            <div className="mt-5 flex flex-wrap gap-3">
              <Link href="/scanner/contract" className="btn-primary">Run Contract Scan →</Link>
              <Link href="/scanner/unified-url" className="btn-secondary">Full Launch Scan</Link>
            </div>
          </div>

          <div className="p-5 lg:p-7">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.22em] text-slate-500">Sample result</p>
                <p className="mt-1 text-4xl font-black text-white">34<span className="text-base text-slate-500">/100</span></p>
                <p className="mt-1 text-xs font-bold text-red-200">Critical Launch Risk</p>
              </div>
              <svg width="96" height="96" viewBox="0 0 96 96" className="shrink-0 -rotate-90">
                <circle cx="48" cy="48" r="40" stroke="rgba(255,255,255,.08)" strokeWidth="10" fill="none" />
                <circle className="score-ring" cx="48" cy="48" r="40" stroke="url(#scoreGradient)" strokeWidth="10" fill="none" strokeLinecap="round" strokeDasharray="251" />
                <defs>
                  <linearGradient id="scoreGradient" x1="0" x2="1" y1="0" y2="0">
                    <stop stopColor="#ef4444" />
                    <stop offset="1" stopColor="#facc15" />
                  </linearGradient>
                </defs>
              </svg>
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              <span className="sev-critical">2 Critical</span>
              <span className="sev-high">2 High</span>
              <span className="sev-medium">1 Medium</span>
            </div>

            <div className="mt-5 space-y-2.5">
              {findings.map(({ sev, rule, surface, title, fix }) => (
                <details key={rule} className="group rounded-xl border border-white/[0.07] bg-white/[0.025] p-3 open:border-cyan/20 open:bg-cyan/[0.035]">
                  <summary className="flex cursor-pointer list-none items-start gap-2">
                    <span className={sevCls[sev] ?? "sev-info"}>{sev}</span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-xs font-bold text-white">{title}</span>
                      <span className="mono mt-1 block text-[11px] text-slate-600">{surface} · {rule}</span>
                    </span>
                    <span className="text-slate-600 transition group-open:rotate-45 group-open:text-cyan">＋</span>
                  </summary>
                  <div className="mt-3 rounded-lg border border-white/[0.06] bg-black/25 p-3">
                    <p className="text-xs font-bold text-emerald-300">Fix hint</p>
                    <code className="mono mt-1 block text-xs leading-5 text-slate-300">{fix}</code>
                  </div>
                </details>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
