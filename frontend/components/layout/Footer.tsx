import Link from "next/link";
import { brand } from "@/lib/constants";

const columns = [
  {
    title: "Core flow",
    links: [
      { label: "Scanner", href: "/scanner/unified-url" },
      { label: "Results", href: "/results" },
      { label: "Fix Plan", href: "/fix-plan" },
      { label: "Report", href: "/report" },
    ],
  },
  {
    title: "Validation",
    links: [
      { label: "Pricing", href: "/pricing" },
      { label: "Billing", href: "/billing" },
      { label: "Launch Validation", href: "/launch-validation" },
      { label: "Dashboard", href: "/dashboard" },
    ],
  },
  {
    title: "Trust docs",
    links: [
      { label: "Docs", href: "/docs" },
      { label: "Methodology", href: "/methodology" },
      { label: "Limitations", href: "/limitations" },
      { label: "Responsible Use", href: "/responsible-use" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-white/[0.07] bg-black/20">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-10 md:grid-cols-[1.45fr_1fr_1fr_1fr]">
          <div>
            <Link href="/" className="flex items-center gap-2.5" aria-label="Web3Guard AI home">
              <span className="brand-mark grid h-9 w-9 place-items-center rounded-[10px] text-[13px] font-black">W3</span>
              <span>
                <span className="block text-sm font-black tracking-tight text-white">{brand.product}</span>
                <span className="block text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">by {brand.company}</span>
              </span>
            </Link>

            <p className="mt-4 max-w-xs text-xs leading-6 text-slate-400">
              Evidence-first Web3 launch readiness scanner for founders preparing before formal audits.
            </p>

            <div className="mt-4 flex flex-wrap gap-2">
              {[
                { tone: "bg-emerald-400", text: "7-path journey" },
                { tone: "bg-amber-300", text: "Payments verified only" },
                { tone: "bg-slate-400", text: "Pre-audit only" },
              ].map(({ tone, text }) => (
                <span key={text} className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.07] bg-white/[0.03] px-2.5 py-1 text-[11px] font-semibold text-slate-400">
                  <span className={`h-1.5 w-1.5 rounded-full ${tone}`} />
                  {text}
                </span>
              ))}
            </div>

            <div className="mt-5 rounded-2xl border border-amber-300/15 bg-amber-300/[0.06] p-4 text-xs leading-6 text-amber-100/80">
              <strong className="text-amber-100">Important:</strong> {brand.disclaimer} It is not a certified audit and does not guarantee 100% security.
            </div>
          </div>

          {columns.map(({ title, links }) => (
            <div key={title}>
              <p className="mb-3 text-[11px] font-black uppercase tracking-[0.22em] text-slate-500">{title}</p>
              <ul className="space-y-2.5">
                {links.map(({ label, href }) => (
                  <li key={href}>
                    <Link href={href} className="text-xs font-medium text-slate-400 transition hover:text-white">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.06] pt-6">
          <p className="text-xs text-slate-600">© {new Date().getFullYear()} {brand.product} by {brand.company}.</p>
          <p className="text-xs text-slate-600">Preliminary review only. Not a certified audit.</p>
        </div>
      </div>
    </footer>
  );
}
