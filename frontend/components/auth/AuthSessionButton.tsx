"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { createBrowserClient } from "@supabase/ssr";

type AuthStatus = "loading" | "signed-in" | "signed-out" | "not-configured";

function SettingsIcon() {
  return (
    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 15.4a3.4 3.4 0 1 0 0-6.8 3.4 3.4 0 0 0 0 6.8Z"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M19.4 13.5c.08-.48.1-.99.1-1.5s-.02-1.02-.1-1.5l2.03-1.56-1.92-3.32-2.4.97a7.65 7.65 0 0 0-2.6-1.5L14.16 2h-3.84l-.35 3.09a7.65 7.65 0 0 0-2.6 1.5l-2.4-.97-1.92 3.32L5.08 10.5c-.08.48-.1.99-.1 1.5s.02 1.02.1 1.5l-2.03 1.56 1.92 3.32 2.4-.97a7.65 7.65 0 0 0 2.6 1.5l.35 3.09h3.84l.35-3.09a7.65 7.65 0 0 0 2.6-1.5l2.4.97 1.92-3.32-2.03-1.56Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

const accountLinks = [
  { href: "/dashboard", label: "Profile / Account" },
  { href: "/settings/language", label: "Language & Preferences" },
  { href: "/dashboard/reports", label: "Saved Reports" },
  { href: "/billing", label: "Billing / Payment Pending" },
  { href: "/feature-status", label: "Feature Status" },
  { href: "/launch-readiness", label: "Launch Readiness" },
] as const;

export function AuthSessionButton() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

  const supabase = useMemo(() => {
    if (!supabaseUrl || !supabaseAnonKey) {
      return null;
    }

    try {
      return createBrowserClient(supabaseUrl, supabaseAnonKey);
    } catch {
      return null;
    }
  }, [supabaseUrl, supabaseAnonKey]);

  const [status, setStatus] = useState<AuthStatus>("loading");
  const [loadingLogout, setLoadingLogout] = useState(false);

  useEffect(() => {
    if (!supabase) {
      setStatus("not-configured");
      return;
    }

    const client = supabase;
    let mounted = true;

    client.auth
      .getSession()
      .then(({ data, error }) => {
        if (!mounted) return;

        if (error) {
          setStatus("signed-out");
          return;
        }

        setStatus(data.session ? "signed-in" : "signed-out");
      })
      .catch(() => {
        if (!mounted) return;
        setStatus("signed-out");
      });

    const {
      data: { subscription },
    } = client.auth.onAuthStateChange((_event, session) => {
      if (!mounted) return;
      setStatus(session ? "signed-in" : "signed-out");
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [supabase]);

  async function handleLogout() {
    if (!supabase) {
      setStatus("not-configured");
      return;
    }

    const client = supabase;

    setLoadingLogout(true);

    try {
      await client.auth.signOut();
      setStatus("signed-out");
      window.location.assign("/auth/login");
    } finally {
      setLoadingLogout(false);
    }
  }

  if (status === "loading") {
    return (
      <span className="settings-orb settings-orb-loading" aria-label="Checking account session">
        <SettingsIcon />
      </span>
    );
  }

  if (status === "signed-in") {
    return (
      <details className="settings-menu group relative">
        <summary className="settings-orb settings-orb-menu-trigger list-none" aria-label="Open account and settings menu" title="Settings">
          <SettingsIcon />
          <span className="sr-only">Settings</span>
        </summary>

        <div className="settings-dropdown-panel absolute right-0 top-12 z-50 w-72 overflow-hidden rounded-3xl border border-white/[0.09] bg-[#050a14]/95 p-2 shadow-[0_24px_80px_rgba(0,0,0,.55)] backdrop-blur-xl">
          <div className="px-3 py-3">
            <p className="text-xs font-black uppercase tracking-[0.20em] text-cyan/80">Account controls</p>
            <p className="mt-1 text-xs leading-5 text-slate-400">Settings, reports, billing, and launch readiness.</p>
          </div>
          {accountLinks.map((item) => (
            <Link key={item.href} href={item.href} className="settings-dropdown-link">
              {item.label}
            </Link>
          ))}
          <button
            type="button"
            onClick={handleLogout}
            disabled={loadingLogout}
            className="settings-dropdown-logout"
          >
            {loadingLogout ? "Logging out..." : "Logout"}
          </button>
        </div>
      </details>
    );
  }

  return (
    <Link
      href="/auth/login"
      className="rounded-full border border-cyan/20 bg-white/[0.055] px-5 py-3 text-sm font-black text-white shadow-[0_14px_50px_rgba(6,182,212,0.08)] transition hover:border-cyan/35 hover:bg-cyan/10"
    >
      Login
    </Link>
  );
}

export default AuthSessionButton;
