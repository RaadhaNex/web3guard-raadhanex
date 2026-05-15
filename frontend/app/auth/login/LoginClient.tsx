"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import { createBrowserClient } from "@supabase/ssr";

export default function LoginClient() {
  const router = useRouter();

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

  const [clientError, setClientError] = useState("");

  const supabase = useMemo(() => {
    if (!supabaseUrl || !supabaseAnonKey) {
      return null;
    }

    try {
      return createBrowserClient(supabaseUrl, supabaseAnonKey);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to initialize Supabase client.";

      setClientError(message);
      return null;
    }
  }, [supabaseUrl, supabaseAnonKey]);

  const isConfigured = Boolean(supabaseUrl && supabaseAnonKey && supabase);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [status, setStatus] = useState<{
    type: "idle" | "error" | "success";
    message: string;
  }>({
    type: "idle",
    message: "",
  });
  const [loading, setLoading] = useState(false);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!isConfigured || !supabase) {
      setStatus({
        type: "error",
        message:
          clientError ||
          "Supabase frontend keys are missing or invalid. Check Vercel Environment Variables and redeploy.",
      });
      return;
    }

    if (!email.trim() || !password.trim()) {
      setStatus({
        type: "error",
        message: "Please enter your email and password.",
      });
      return;
    }

    setLoading(true);
    setStatus({ type: "idle", message: "" });

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      if (error) {
        setStatus({
          type: "error",
          message: error.message || "Login failed. Please try again.",
        });
        return;
      }

      setStatus({
        type: "success",
        message: "Login successful. Opening dashboard...",
      });

      router.replace("/dashboard");
      router.refresh();
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Login failed because of a network or browser issue.";

      setStatus({
        type: "error",
        message,
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10 text-slate-950">
      <section className="mx-auto max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-xs font-bold uppercase tracking-[0.24em] text-sky-500">
          Secure account access
        </p>

        <h1 className="mt-3 text-3xl font-black tracking-tight">
          Login to Web3Guard
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-600">
          Access your dashboard, reports, scan history, and billing securely.
        </p>

        {!isConfigured ? (
          <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-900">
            Supabase frontend keys are missing or invalid. Add
            NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in
            Vercel, then redeploy.
            {clientError ? (
              <p className="mt-2 text-xs font-medium">{clientError}</p>
            ) : null}
          </div>
        ) : null}

        <form onSubmit={handleLogin} className="mt-6 space-y-5">
          <label className="block">
            <span className="text-sm font-bold text-slate-800">Email</span>
            <input
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
            />
          </label>

          <label className="block">
            <span className="text-sm font-bold text-slate-800">Password</span>
            <div className="mt-2 flex rounded-2xl border border-slate-300 bg-white focus-within:border-sky-400 focus-within:ring-4 focus-within:ring-sky-100">
              <input
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Enter your password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-2xl bg-transparent px-4 py-3 text-slate-950 outline-none"
              />
              <button
                type="button"
                onClick={() => setShowPassword((value) => !value)}
                className="px-4 text-sm font-bold text-slate-600 hover:text-slate-950"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </label>

          {status.message ? (
            <div
              className={`rounded-2xl border p-4 text-sm font-semibold ${
                status.type === "success"
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                  : "border-rose-200 bg-rose-50 text-rose-800"
              }`}
            >
              {status.message}
            </div>
          ) : null}

          <button
            type="submit"
            disabled={loading || !isConfigured}
            className="w-full rounded-2xl bg-sky-400 px-5 py-4 text-base font-black text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>

        <p className="mt-6 text-sm text-slate-600">
          New to Web3Guard?{" "}
          <Link href="/auth/signup" className="font-bold text-sky-600">
            Create account
          </Link>
        </p>
      </section>
    </main>
  );
}