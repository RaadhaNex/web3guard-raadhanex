"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";
import { getSessionToken, getSupabaseClient, isSupabaseConfigured } from "@/lib/supabase";

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function redirectTarget() {
    if (typeof window === "undefined") return "/dashboard";
    const params = new URLSearchParams(window.location.search);
    return params.get("redirect") || "/dashboard";
  }

  async function syncProfile(userId: string) {
    const token = await getSessionToken();
    if (!token) return;
    await apiPost("/profile", {
      id: userId,
      email,
      full_name: fullName || email.split("@")[0],
      preferred_language: "English",
      plan: "free",
    }, { headers: { Authorization: `Bearer ${token}` } });
  }

  async function submit() {
    setLoading(true);
    setError(null);
    setStatus(null);
    try {
      const client = getSupabaseClient();
      if (!client) {
        setStatus("Provider Not Configured: add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY. No fake account/session was created.");
        return;
      }
      if (mode === "signup") {
        const { data, error: signUpError } = await client.auth.signUp({
          email,
          password,
          options: { data: { full_name: fullName || email.split("@")[0] } },
        });
        if (signUpError) throw signUpError;
        if (data.user?.id && data.session) await syncProfile(data.user.id);
        setStatus(data.session ? "Signup successful. Redirecting to protected dashboard." : "Signup requested. Check email confirmation if Supabase email confirmation is enabled.");
        if (data.session) {
          router.push(redirectTarget());
          router.refresh();
        }
      } else {
        const { data, error: loginError } = await client.auth.signInWithPassword({ email, password });
        if (loginError) throw loginError;
        if (data.user?.id) await syncProfile(data.user.id);
        setStatus("Login successful. Redirecting to protected dashboard.");
        router.push(redirectTarget());
        router.refresh();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auth failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card p-6">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Patch H real Supabase auth</p>
          <h1 className="mt-2 text-3xl font-black">{mode === "signup" ? "Create account" : "Login"}</h1>
          <p className="mt-2 text-sm text-slate-400">Signup, login, logout and session persistence use Supabase Auth only when real env keys are configured.</p>
        </div>
        <span className={`rounded-full border px-3 py-1 text-xs font-bold ${isSupabaseConfigured ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-200" : "border-amber-400/40 bg-amber-400/10 text-amber-200"}`}>
          {isSupabaseConfigured ? "Supabase configured" : "Provider Not Configured"}
        </span>
      </div>

      <div className="grid gap-4">
        {mode === "signup" && (
          <label className="grid gap-2 text-sm font-semibold text-slate-300">
            Full name
            <input className="input" value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Neeraj Kumar" />
          </label>
        )}
        <label className="grid gap-2 text-sm font-semibold text-slate-300">
          Email
          <input className="input" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="founder@example.com" />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-slate-300">
          Password
          <input className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Minimum 6 characters" />
        </label>
        <button className="btn-primary" disabled={loading || !email || password.length < 6} onClick={submit}>
          {loading ? "Working..." : mode === "signup" ? "Create real account" : "Login with Supabase"}
        </button>
      </div>

      {status && <div className="mt-4 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-100">{status}</div>}
      {error && <div className="mt-4 rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-100">{error}</div>}

      <p className="mt-5 text-sm text-slate-400">
        {mode === "signup" ? "Already have an account? " : "Need an account? "}
        <Link className="text-cyan hover:text-white" href={mode === "signup" ? "/auth/login" : "/auth/signup"}>
          {mode === "signup" ? "Login" : "Sign up"}
        </Link>
      </p>
    </div>
  );
}
