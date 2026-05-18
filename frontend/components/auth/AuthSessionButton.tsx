"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { createBrowserClient } from "@supabase/ssr";

type AuthStatus = "loading" | "signed-in" | "signed-out" | "not-configured";

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
      <span className="rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-500">
        Checking...
      </span>
    );
  }

  if (status === "signed-in") {
    return (
      <details className="group relative">
        <summary className="list-none rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-800 shadow-sm transition hover:bg-slate-50">
          Settings
          <span aria-hidden="true" className="ml-1 inline-block transition group-open:rotate-180">⌄</span>
        </summary>

        <div className="absolute right-0 top-12 z-50 w-64 overflow-hidden rounded-3xl border border-slate-200 bg-white p-2 shadow-xl">
          <Link href="/dashboard" className="block rounded-2xl px-4 py-3 text-sm font-bold text-slate-800 hover:bg-slate-50">
            Profile / Account
          </Link>
          <Link href="/settings/language" className="block rounded-2xl px-4 py-3 text-sm font-bold text-slate-800 hover:bg-slate-50">
            Language & Preferences
          </Link>
          <Link href="/dashboard/reports" className="block rounded-2xl px-4 py-3 text-sm font-bold text-slate-800 hover:bg-slate-50">
            Saved Reports
          </Link>
          <Link href="/billing" className="block rounded-2xl px-4 py-3 text-sm font-bold text-slate-800 hover:bg-slate-50">
            Billing
          </Link>
          <Link href="/feature-status" className="block rounded-2xl px-4 py-3 text-sm font-bold text-slate-800 hover:bg-slate-50">
            Feature Status
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            disabled={loadingLogout}
            className="mt-1 w-full rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-left text-sm font-black text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-60"
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
      className="rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
    >
      Login
    </Link>
  );
}

export default AuthSessionButton;
