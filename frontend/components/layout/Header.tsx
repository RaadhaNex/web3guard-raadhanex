"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AuthSessionButton } from "@/components/auth/AuthSessionButton";
import KavachWingNavLogo from "@/components/brand/KavachWingNavLogo";
import { brand } from "@/lib/constants";

const primaryLinks = [
  { href: "/scanner/unified-url", label: "Scanner" },
  { href: "/results", label: "Results" },
  { href: "/report", label: "Report" },
  { href: "/pricing", label: "Pricing" },
  { href: "/docs", label: "Docs" },
];

const secondaryLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/scans", label: "Saved scans" },
  { href: "/launch-pack", label: "First 10 users" },
  { href: "/risk-intelligence", label: "Risk intelligence" },
  { href: "/payment-validation", label: "Payment validation" },
  { href: "/feature-status", label: "Feature status" },
  { href: "/advanced", label: "Advanced tools" },
];

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavLink({ href, label, onClick }: { href: string; label: string; onClick?: () => void }) {
  const pathname = usePathname();
  return (
    <Link href={href} onClick={onClick} className={`nav-link ${isActive(pathname, href) ? "nav-link-active" : ""}`}>
      {label}
    </Link>
  );
}

export function Header() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="site-header">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-3" aria-label="Web3Guard AI home" onClick={() => setOpen(false)}>
          <KavachWingNavLogo showText={false} />
          <span className="hidden min-w-0 sm:block">
            <span className="brand-product block truncate text-sm font-black tracking-[-0.02em]">{brand.product}</span>
            <span className="brand-company block truncate text-[10px] font-semibold uppercase tracking-[0.18em]">by {brand.company}</span>
          </span>
        </Link>

        <nav className="hidden min-w-0 flex-1 items-center justify-center gap-1 lg:flex" aria-label="Main navigation">
          {primaryLinks.map((item) => (
            <NavLink key={item.href} href={item.href} label={item.label} />
          ))}
          <details className="clean-more-menu relative">
            <summary className={`nav-link cursor-pointer list-none ${secondaryLinks.some((item) => isActive(pathname, item.href)) ? "nav-link-active" : ""}`}>
              More
            </summary>
            <div className="absolute right-0 top-12 z-50 w-64 rounded-2xl border border-white/[0.08] bg-[#050a14]/95 p-2 shadow-[0_24px_80px_rgba(0,0,0,.55)] backdrop-blur-xl">
              {secondaryLinks.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="block rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-300 transition hover:bg-white/[0.05] hover:text-white"
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </details>
        </nav>

        <div className="hidden shrink-0 items-center gap-2 sm:flex">
          <Link href="/scanner/unified-url" className="btn-primary !px-4 !py-2 text-xs">
            Start readiness scan
          </Link>
          <AuthSessionButton />
        </div>

        <button
          type="button"
          aria-label="Open navigation menu"
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
          className="grid h-10 w-10 place-items-center rounded-[10px] border border-white/[0.08] bg-white/[0.04] text-white lg:hidden"
        >
          <span className="relative h-4 w-5">
            <span className={`absolute left-0 top-0 h-0.5 w-5 rounded-full bg-current transition ${open ? "translate-y-[7px] rotate-45" : ""}`} />
            <span className={`absolute left-0 top-[7px] h-0.5 w-5 rounded-full bg-current transition ${open ? "opacity-0" : ""}`} />
            <span className={`absolute left-0 top-[14px] h-0.5 w-5 rounded-full bg-current transition ${open ? "-translate-y-[7px] -rotate-45" : ""}`} />
          </span>
        </button>
      </div>

      {open ? (
        <div className="mobile-panel lg:hidden">
          <div className="mx-auto max-w-7xl px-4 pt-4 sm:px-6">
            <div className="mb-3 rounded-2xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-slate-300">
              Clean beta flow: scan → results → report → pricing. Advanced setup stays under More.
            </div>
          </div>
          <nav className="mx-auto grid max-w-7xl gap-2 px-4 pb-4 sm:grid-cols-2 sm:px-6" aria-label="Mobile navigation">
            {[...primaryLinks, ...secondaryLinks].map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={`rounded-xl border px-4 py-3 text-sm font-bold transition ${
                  isActive(pathname, item.href)
                    ? "border-cyan/30 bg-cyan/10 text-cyan"
                    : "border-white/[0.07] bg-white/[0.03] text-slate-300 hover:border-cyan/25 hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            ))}
            <Link href="/scanner/unified-url" onClick={() => setOpen(false)} className="btn-primary mt-2 sm:col-span-2">
              Start readiness scan →
            </Link>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
