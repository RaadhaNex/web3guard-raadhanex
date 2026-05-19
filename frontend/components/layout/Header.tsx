"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AuthSessionButton } from "@/components/auth/AuthSessionButton";
import { brand } from "@/lib/constants";

const navLinks = [
  { href: "/scanner/unified-url", label: "Scanner" },
  { href: "/methodology", label: "Methodology" },
  { href: "/limitations", label: "Limitations" },
  { href: "/sample-reports", label: "Sample Reports" },
  { href: "/pricing", label: "Pricing" },
  { href: "/free-tools", label: "Free Tools" },
  { href: "/dashboard", label: "Dashboard" },
];

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Header() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="site-header">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-3" aria-label="Web3Guard AI home" onClick={() => setOpen(false)}>
          <span className="brand-mark grid h-9 w-9 shrink-0 place-items-center rounded-[10px] text-[13px] font-black tracking-tight">
            W3
          </span>
          <span className="hidden min-w-0 sm:block">
            <span className="brand-product block truncate text-sm font-black tracking-[-0.02em]">{brand.product}</span>
            <span className="brand-company block truncate text-[10px] font-semibold uppercase tracking-[0.18em]">by {brand.company}</span>
          </span>
        </Link>

        <nav className="hidden min-w-0 flex-1 items-center justify-center gap-1 lg:flex" aria-label="Main navigation">
          {navLinks.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-link ${isActive(pathname, item.href) ? "nav-link-active" : ""}`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden shrink-0 items-center gap-2 sm:flex">
          <Link href="/scanner/unified-url" className="btn-primary !px-4 !py-2 text-xs">
            Free Scan
          </Link>
          <AuthSessionButton />
        </div>

        <button
          type="button"
          aria-label="Open navigation menu"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
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
          <nav className="mx-auto grid max-w-7xl gap-2 px-4 py-4 sm:grid-cols-2 sm:px-6" aria-label="Mobile navigation">
            {navLinks.map((item) => (
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
              Start Free Scan →
            </Link>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
