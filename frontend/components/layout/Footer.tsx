import Link from "next/link";
import { brand } from "@/lib/constants";

const cols = [
  {
    title: "Product",
    links: [
      { label: "Quick Scan",      href: "/scanner/unified-url" },
      { label: "All Scanners",    href: "/scanner" },
      { label: "Pricing",         href: "/pricing" },
      { label: "Feature Status",  href: "/feature-status" },
      { label: "Learning",        href: "/learning" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Methodology",    href: "/methodology" },
      { label: "Sample Reports", href: "/sample-reports" },
      { label: "Launch Pack",    href: "/launch-pack" },
      { label: "Developer API",  href: "/developer-api" },
      { label: "Threat Intel",   href: "/threat-intel" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "Trust Policy",   href: "/trust" },
      { label: "Responsible Use",href: "/responsible-use" },
      { label: "Scope & Refund", href: "/scope-refund" },
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Terms",          href: "/terms" },
    ],
  },
];

export function Footer() {
  return (
    <footer style={{ borderTop: "1px solid rgba(255,255,255,0.07)", background: "rgba(0,0,0,0.2)" }}>
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">

        {/* Top grid */}
        <div className="grid gap-10 md:grid-cols-[1.6fr_1fr_1fr_1fr]">

          {/* Brand */}
          <div>
            <div className="flex items-center gap-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-xl border border-cyan/25 bg-cyan/10 text-xs font-black text-cyan">W3</span>
              <span className="text-sm font-black tracking-tight text-white">{brand.product}</span>
            </div>

            <p className="mt-3 max-w-xs text-xs leading-6 text-slate-400">{brand.tagline}</p>

            <div className="mt-4 flex flex-wrap gap-2">
              {[
                { dot: "#22d3ee", text: "Scanners live" },
                { dot: "#f59e0b", text: "Manual payments" },
                { dot: "#64748b", text: "Pre-audit only" },
              ].map(({ dot, text }) => (
                <span key={text} className="flex items-center gap-1.5 rounded-full border border-white/[0.07] px-2.5 py-1 text-xs font-medium text-slate-400">
                  <span style={{ width: 5, height: 5, borderRadius: "50%", background: dot, flexShrink: 0, display: "inline-block" }} />
                  {text}
                </span>
              ))}
            </div>

            <p className="mt-4 rounded-xl border border-amber-400/15 bg-amber-400/[0.06] p-3 text-xs leading-5 text-amber-200/80">
              {brand.disclaimer}
            </p>
          </div>

          {/* Link columns */}
          {cols.map(({ title, links }) => (
            <div key={title}>
              <p className="mb-3 text-xs font-bold uppercase tracking-widest text-slate-500">{title}</p>
              <ul className="space-y-2.5">
                {links.map(({ label, href }) => (
                  <li key={href}>
                    <Link href={href} className="text-xs text-slate-400 transition hover:text-white">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom */}
        <div className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.06] pt-6">
          <p className="text-xs text-slate-600">
            © {new Date().getFullYear()} {brand.product} by {brand.company}. All rights reserved.
          </p>
          <p className="text-xs text-slate-600">
            Not a licensed security firm. Preliminary AI-assisted review only.
          </p>
        </div>
      </div>
    </footer>
  );
}
