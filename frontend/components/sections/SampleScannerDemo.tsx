import Link from "next/link";

const findings = [
  { sev: "critical", rule: "WG-SOL-REENT-001", surface: "Contract", title: "Reentrancy in withdraw()", fix: "Move bal[msg.sender]=0 before the external call." },
  { sev: "high",     rule: "WG-SOL-AUTH-001",  surface: "Contract", title: "tx.origin authorization", fix: "Replace tx.origin with msg.sender in all require checks." },
  { sev: "high",     rule: "WG-SOL-LOCK-001",  surface: "Contract", title: "Locked ether — no withdrawal", fix: "Add onlyOwner rescueETH() function." },
  { sev: "medium",   rule: "WG-SOL-WEBSITE",   surface: "Website",  title: "CSP header missing", fix: "Add Content-Security-Policy in next.config.mjs headers." },
  { sev: "high",     rule: "WG-SOL-ADMIN-001", surface: "Admin",    title: "Single owner — no multisig", fix: "Deploy Gnosis Safe and transfer ownership before launch." },
];

const sevCls: Record<string, string> = {
  critical: "sev-critical", high: "sev-high", medium: "sev-medium", low: "sev-low",
};

export function SampleScannerDemo() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="card overflow-hidden">
        <div className="grid gap-0 lg:grid-cols-[1fr_420px]">

          {/* Left — Code editor look */}
          <div className="border-b border-white/[0.07] p-6 lg:border-b-0 lg:border-r lg:p-8">
            <p className="section-label">Try the scanner</p>
            <h2 className="mt-3 text-2xl font-black sm:text-3xl">
              Paste any Solidity contract. Get real findings instantly.
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              This sample contract has 3 known vulnerabilities. Copy it into the scanner to see how findings are generated — then replace with your own code.
            </p>

            {/* Code block */}
            <div className="mt-5 overflow-hidden rounded-xl border border-white/[0.07]" style={{ background: "#07090f" }}>
              <div className="flex items-center gap-2 border-b border-white/[0.07] px-4 py-2.5">
                <div className="flex gap-1.5">
                  <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ff5f57", display: "block" }} />
                  <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#febc2e", display: "block" }} />
                  <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#28c840", display: "block" }} />
                </div>
                <span className="mono text-xs text-slate-500">VulnVault.sol</span>
              </div>
              <pre className="overflow-auto p-4 text-xs leading-relaxed text-slate-300" style={{ fontFamily: "'JetBrains Mono',monospace", maxHeight: 200 }}>
{`contract VulnVault {
  mapping(address=>uint) public bal;
  address public owner;

  // ⚠ Reentrancy: state update after call
  function withdraw() public {
    (bool ok,) = msg.sender.call{
      value: bal[msg.sender]}("");
    require(ok);
    bal[msg.sender] = 0; // too late!
  }

  // ⚠ tx.origin auth risk
  function setOwner(address a) public {
    require(tx.origin == owner);
    owner = a;
  }
}`}
              </pre>
            </div>

            <div className="mt-5 flex flex-wrap gap-3">
              <Link href="/scanner/contract" className="btn-primary">
                Scan This Contract
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}><path d="M1.5 6.5h10M7.5 2.5l4 4-4 4"/></svg>
              </Link>
              <Link href="/scanner/unified-url" className="btn-secondary">Full Launch Scan</Link>
            </div>
          </div>

          {/* Right — Results */}
          <div className="p-6 lg:p-8">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">Sample result</p>
                <p className="mt-1 text-4xl font-black" style={{ lineHeight: 1 }}>34<span className="text-base text-slate-500">/100</span></p>
                <p className="mt-1 text-xs font-semibold" style={{ color: "#fca5a5" }}>Critical Launch Risk</p>
              </div>
              <div className="flex flex-col items-end gap-1">
                <span className="sev-critical">2 Critical</span>
                <span className="sev-high">2 High</span>
                <span className="sev-medium">1 Medium</span>
              </div>
            </div>

            <div className="space-y-2.5">
              {findings.map(({ sev, rule, surface, title, fix }) => (
                <div key={rule} className="rounded-xl border border-white/[0.07] bg-white/[0.025] p-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className={sevCls[sev] ?? "sev-info"}>{sev}</span>
                    <span className="text-xs text-slate-500">{surface}</span>
                    <span className="mono text-xs text-slate-600 ml-auto">{rule}</span>
                  </div>
                  <p className="text-xs font-bold text-white">{title}</p>
                  <p className="mt-0.5 text-xs text-slate-400 leading-5">
                    <span className="text-green-400">Fix:</span> {fix}
                  </p>
                </div>
              ))}
            </div>

            <p className="mt-4 text-xs text-slate-600">
              Sample only — real scans use your contract code.{" "}
              <Link href="/sample-reports" className="text-cyan hover:underline">View full sample reports →</Link>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
