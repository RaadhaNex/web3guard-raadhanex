import Link from "next/link";

export default async function WorkspaceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const paramsValue = await params;
  const workspaceId = paramsValue.id;

  return (
    <main className="min-h-screen bg-white px-6 py-10 text-slate-950">
      <div className="mx-auto max-w-5xl">
        <Link
          href="/dashboard"
          className="text-sm font-semibold text-slate-600 hover:text-slate-950"
        >
          ← Back to dashboard
        </Link>

        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-slate-500">
            Workspace
          </p>

          <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950">
            Workspace details
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
            This workspace page is connected to the protected dashboard route.
            Full workspace collaboration controls can be expanded here after the
            production launch.
          </p>

          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Workspace ID
            </p>
            <p className="mt-2 break-all font-mono text-sm text-slate-900">
              {workspaceId}
            </p>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/dashboard/scans"
              className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-bold text-white hover:bg-slate-800"
            >
              View scans
            </Link>

            <Link
              href="/dashboard/reports"
              className="rounded-2xl border border-slate-300 px-5 py-3 text-sm font-bold text-slate-900 hover:bg-slate-50"
            >
              View reports
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}