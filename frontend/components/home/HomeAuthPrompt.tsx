"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { createBrowserClient } from "@supabase/ssr";

type AuthStatus = "loading" | "signed-in" | "signed-out" | "not-configured";

export function HomeAuthPrompt() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

  const supabase = useMemo(() => {
    if (!supabaseUrl || !supabaseAnonKey) return null;

    try {
      return createBrowserClient(supabaseUrl, supabaseAnonKey);
    } catch {
      return null;
    }
  }, [supabaseUrl, supabaseAnonKey]);

  const [status, setStatus] = useState<AuthStatus>("loading");

  useEffect(() => {
    if (!supabase) {
      setStatus("not-configured");
      return;
    }

    const client = supabase;
    let mounted = true;

    client.auth
      .getSession()
      .then(({ data }) => {
        if (!mounted) return;
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

  if (status === "loading" || status === "signed-in") return null;

  return (
    <Link href="/auth/login" className="btn-secondary">
      Login to save reports
    </Link>
  );
}

export default HomeAuthPrompt;
