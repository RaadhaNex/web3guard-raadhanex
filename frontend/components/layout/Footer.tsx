import Link from "next/link";
import { brand } from "@/lib/constants";

const columns = [
  {
    title: "Core flow",
    links: [
      { label: "Scanner", href: "/scanner/unified-url" },
      { label: "Results", href: "/results" },
      { label: "Report", href: "/report" },
      { label: "Pricing", href: "/pricing" },
    ],
  },
  {
    title: "Trust",
    links: [
      { label: "Docs", href: "/docs" },
      { label: "Methodology", href: "/methodology" },
      { label: "Limitations", href: "/limitations" },
      { label: "Responsible use", href: "/responsible-use" },
    ],
  },
  {
    title: "Beta ops",
    links: [
      { label: "First 10 users", href: "/launch-pack" },
      { label: "Payment validation", href: "/payment-validation" },
      { label: "Feature status", href: "/feature-status" },
      { label: "Advanced tools", href: "/advanced" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-white/[0.07] bg-black/20">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid gap-8 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div>
            <Link href="/" className="flex items-center gap-2.5" aria-label="Web3Guard AI home">
              <span className="brand-mark grid h-9 w-9 place-items-center rounded-[10px] text-[13px] font-black">W3</span>
              <span>
                <span className="block text-sm font-black tracking-tight text-white">{brand.product}</span>
                <span className="block text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">by {brand.company}</span>
              </span>
            </Link>

            <p className="mt-4 max-w-sm text-xs leading-6 text-slate-400">
              India-first founder security OS for pre-audit launch readiness. Real evidence only; unavailable tools stay visible instead of being guessed.
            </p>

            <div className="mt-5 rounded-2xl border border-amber-300/15 bg-amber-300/[0.055] p-4 text-xs leading-6 text-amber-100/80">
              <strong className="text-amber-100">Important:</strong> {brand.disclaimer} Does not replace professional security review.
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

        <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.06] pt-6">
          <p className="text-xs text-slate-600">© {new Date().getFullYear()} {brand.product} by {brand.company}.</p>
          <p className="text-xs text-slate-600">Pre-audit readiness only. No security guarantee.</p>
        </div>
      </div>
    </footer>
  );
}
