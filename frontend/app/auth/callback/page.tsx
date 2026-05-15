"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getSupabaseClient, isSupabaseConfigured } from "@/lib/supabase";

export default function AuthCallbackPage() {
  const router = useRouter();
  const [message, setMessage] = useState("Checking Supabase session...");

  useEffect(() => {
    async function run() {
      const client = getSupabaseClient();
      if (!isSupabaseConfigured || !client) {
        setMessage("Supabase env is not configured. No fake callback session was created.");
        return;
      }
      const { data, error } = await client.auth.getSession();
      if (error) {
        setMessage(error.message);
        return;
      }
      if (data.session) {
        setMessage("Session found. Redirecting to dashboard...");
        setTimeout(() => router.push("/dashboard"), 500);
      } else {
        setMessage("No active session found. Login again.");
      }
    }
    void run();
  }, [router]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="card p-6">
        <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Supabase auth callback</p>
        <h1 className="mt-2 text-3xl font-black">Authentication status</h1>
        <p className="mt-4 text-slate-300">{message}</p>
        <div className="mt-6 flex gap-3">
          <Link className="btn-primary" href="/dashboard">Dashboard</Link>
          <Link className="btn-secondary" href="/auth/login">Login</Link>
        </div>
      </div>
    </main>
  );
}
