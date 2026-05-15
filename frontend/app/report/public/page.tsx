import Link from "next/link";

export default function PublicReportRegistryPage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <p className="text-sm font-black uppercase tracking-[0.3em] text-cyan">Phase 9 public registry foundation</p>
      <h1 className="mt-3 text-4xl font-black sm:text-6xl">Public Report Registry</h1>
      <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-300">
        Phase 9 adds backend public/private report records and verification endpoints. Use public report links only with pre-audit readiness wording. Never call these reports certified audits.
      </p>
      <section className="mt-8 grid gap-4 md:grid-cols-2">
        <div className="card p-6">
          <h2 className="text-2xl font-black text-white">Endpoints</h2>
          <ul className="mt-4 space-y-2 text-sm text-slate-300">
            <li><code>POST /report/publication</code> — create public/private record</li>
            <li><code>GET /report/public</code> — list public records</li>
            <li><code>GET /report/public/:id</code> — fetch public record</li>
            <li><code>GET /report/public/:id/verify?report_hash=...</code> — verify hash</li>
            <li><code>GET /report/public/:id/html</code> — public HTML view</li>
            <li><code>GET /report/public/:id/pdf</code> — public PDF download</li>
          </ul>
        </div>
        <div className="card p-6">
          <h2 className="text-2xl font-black text-white">Real-only rules</h2>
          <ul className="mt-4 space-y-2 text-sm text-slate-300">
            <li>No fake verified badges.</li>
            <li>No certified-audit wording.</li>
            <li>Public report can expose findings, so sensitive details need manual review.</li>
            <li>Private records require explicit allow-private backend query for local/admin use.</li>
          </ul>
        </div>
      </section>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link className="btn-primary" href="/report/professional">Create professional report</Link>
        <Link className="btn-secondary" href="/trust">Read trust policy</Link>
      </div>
    </main>
  );
}
