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
      <div className="flex items-center gap-2">
        <Link
          href="/dashboard"
          className="rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
        >
          Dashboard
        </Link>

        <button
          type="button"
          onClick={handleLogout}
          disabled={loadingLogout}
          className="rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loadingLogout ? "Logging out..." : "Logout"}
        </button>
      </div>
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