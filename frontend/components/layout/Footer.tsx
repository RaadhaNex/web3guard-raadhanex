import Link from "next/link";
import { brand } from "@/lib/constants";

const columns = [
  {
    title: "Core flow",
    links: [
      { label: "Home", href: "/" },
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
    title: "More",
    links: [
      { label: "First 10 users", href: "/launch-pack" },
      { label: "Payment validation", href: "/payment-validation" },
      { label: "Risk intelligence", href: "/risk-intelligence" },
      { label: "More hub", href: "/more" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="cinematic-footer border-t border-white/[0.07]">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid gap-8 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div>
            <Link href="/" className="flex items-center gap-2.5" aria-label="Web3Guard AI home">
              <span className="brand-mark grid h-9 w-9 place-items-center rounded-[10px] text-[13px] font-black">W3</span>
              <span>
                <span className="block text-sm font-black tracking-tight text-white">{brand.product}</span>
                <span className="block text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan/80">by {brand.company}</span>
              </span>
            </Link>

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
