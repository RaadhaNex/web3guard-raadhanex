import Link from "next/link";
import { brand } from "@/lib/constants";

const links = [
  ["Launch Pack", "/launch-pack"],
  ["Local QA", "/local-qa"],
  ["Reports", "/report/professional"],
  ["Feature Status", "/feature-status"],
  ["Methodology", "/methodology"],
  ["Sample Reports", "/sample-reports"],
  ["Trust", "/trust"],
  ["Scope / Refund", "/scope-refund"],
  ["Responsible Use", "/responsible-use"],
  ["Terms", "/terms"],
  ["Privacy", "/privacy"],
  ["Admin Leads", "/admin/leads"],
];

export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-black/20">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 lg:grid-cols-[1.4fr_1fr] lg:px-8">
        <div>
          <p className="text-lg font-black">{brand.product} by {brand.company}</p>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">{brand.tagline}</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {[
              ["Live", "Real scanners show evidence."],
              ["Manual", "UPI settlement is manually verified."],
              ["Not enabled", "Future integrations are not fake-scored."],
            ].map(([title, text]) => (
              <div key={title} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-xs text-slate-300">
                <strong className="text-white">{title}</strong><br />{text}
              </div>
            ))}
          </div>
          <p className="mt-4 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm text-amber-100">{brand.disclaimer}</p>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm text-slate-300 sm:grid-cols-3 lg:grid-cols-2">
          {links.map(([label, href]) => (
            <Link key={href} href={href} className="hover:text-white">{label}</Link>
          ))}
        </div>
      </div>
    </footer>
  );
}
