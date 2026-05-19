import Link from "next/link";

const endpoints = [
  ["POST /report/publication", "Create a public or private report record from a real report payload."],
  ["GET /report/public", "List public report records that were intentionally published."],
  ["GET /report/public/:id", "Fetch a specific public record."],
  ["GET /report/public/:id/verify", "Verify a report hash against the published record."],
  ["GET /report/public/:id/html", "Open the public HTML delivery view."],
  ["GET /report/public/:id/pdf", "Download the public PDF delivery artifact."],
];

const rules = [
  "No fake verified badges.",
  "No certified-audit wording.",
  "Public report findings may expose sensitive details, so review before publishing.",
  "Private records should remain private unless deliberately shared.",
];

export default function PublicReportRegistryPage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <p className="section-label">Public report registry</p>
      <h1 className="mt-3 text-4xl font-black sm:text-6xl">Share report evidence without overstating security.</h1>
      <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
        Public report records are for transparent pre-audit readiness sharing. They must use safe wording and should be reviewed before being shared with users, investors, partners, or communities.
      </p>

      <section className="mt-8 grid gap-4 md:grid-cols-2">
        <div className="glass-tile p-6">
          <h2 className="text-2xl font-black text-white">Available report routes</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-300">
            {endpoints.map(([endpoint, text]) => (
              <li key={endpoint} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <code className="text-cyan">{endpoint}</code>
                <p className="mt-1 text-slate-400">{text}</p>
              </li>
            ))}
          </ul>
        </div>
        <div className="glass-tile p-6">
          <h2 className="text-2xl font-black text-white">Real-only rules</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-300">
            {rules.map((rule) => <li key={rule}>• {rule}</li>)}
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
