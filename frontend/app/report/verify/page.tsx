import { Suspense } from "react";
import Link from "next/link";
import { ReportVerificationClient } from "@/components/report/ReportVerificationClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function ReportVerifyPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="section-label">Report verification</p>
          <h1 className="mt-3 max-w-4xl text-4xl font-black tracking-[-0.06em] sm:text-6xl">
            Verify report metadata without making unsafe audit claims.
          </h1>
          <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
            report verification adds public report hash verification, evidence snapshots, and finding status workflow bootstrapping. It proves record consistency only—not project safety.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/report/professional" className="btn-secondary">Report builder</Link>
          <Link href="/report/public" className="btn-secondary">Public registry</Link>
        </div>
      </div>

      <Suspense fallback={<div className="glass-tile p-6 text-slate-300">Loading verification console...</div>}>
        <ReportVerificationClient />
      </Suspense>
    </main>
  );
}
