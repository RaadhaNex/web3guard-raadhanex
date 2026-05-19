
import Link from "next/link";
import { ProfessionalReportClient } from "@/components/report/ProfessionalReportClient";

const cards = [
  ["Server PDF", "Generated from backend report data for delivery-ready artifacts."],
  ["Branded HTML", "Preview report layout before downloading or publishing records."],
  ["Hash verify", "Keep report_id and report_hash visible for traceability."],
  ["Clean wording", "Pre-audit readiness reviewed; not certified audit wording."],
];

export default function ProfessionalReportPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <section className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
        <div>
          <p className="section-label">Professional delivery</p>
          <h1 className="mt-4 text-4xl font-black tracking-[-0.06em] sm:text-6xl">Export serious reports without overstating security.</h1>
          <p className="mt-5 max-w-4xl text-base leading-8 text-slate-300 sm:text-lg">
            Paste a real combined report JSON or use scanner exports to create PDF, HTML, Markdown, JSON, and public/private report records with the correct pre-audit boundary.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link className="btn-primary" href="/scanner/unified-url">Run unified scan →</Link>
            <Link className="btn-secondary" href="/report">Report overview</Link>
            <Link className="btn-secondary" href="/sample-reports">Sample reports</Link>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {cards.map(([title, text]) => (
            <div key={title} className="card p-5">
              <p className="font-black text-white">{title}</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-5 text-sm leading-7 text-amber-100">
        Public-safe wording: <strong>Pre-audit readiness reviewed by Web3Guard AI by RAADHANEX.</strong> Avoid certified audit, 100% secure, exploit-proof, and insurance-guaranteed language.
      </section>

      <section className="mt-8">
        <ProfessionalReportClient />
      </section>
    </main>
  );
}
