"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser, isSupabaseConfigured, signOutSupabase } from "@/lib/supabase";

export function AuthSessionButton() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function load() {
      const user = await getCurrentUser();
      if (!mounted) return;
      setEmail(user?.email ?? null);
      setLoading(false);
    }

    void load();
    return () => {
      mounted = false;
    };
  }, []);

  async function logout() {
    await signOutSupabase();
    setEmail(null);
    router.push("/auth/login");
    router.refresh();
  }

  if (!isSupabaseConfigured) {
    return <Link href="/auth/login" className="btn-secondary whitespace-nowrap">Provider Not Configured</Link>;
  }

  if (loading) {
    return <span className="auth-status-pill">Session...</span>;
  }

  if (!email) {
    return <Link href="/auth/login" className="btn-secondary whitespace-nowrap">Login</Link>;
  }

  return (
    <button className="btn-secondary max-w-[10rem] truncate whitespace-nowrap" onClick={logout} title={email}>
      Logout
    </button>
  );
}
