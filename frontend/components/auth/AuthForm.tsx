"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiPost } from "@/lib/api";
import { getSessionToken, getSupabaseClient } from "@/lib/supabase";

type AuthMode = "login" | "signup";

type PasswordChecks = {
  length: boolean;
  uppercase: boolean;
  lowercase: boolean;
  number: boolean;
  special: boolean;
};

function getPasswordChecks(password: string): PasswordChecks {
  return {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };
}

function isStrongPassword(password: string): boolean {
  return Object.values(getPasswordChecks(password)).every(Boolean);
}

function PasswordRule({ passed, label }: { passed: boolean; label: string }) {
  return (
    <li className="flex items-center gap-2">
      <span
        className={
          passed
            ? "flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-xs font-black text-emerald-300"
            : "flex h-5 w-5 items-center justify-center rounded-full border border-white/10 text-xs font-black text-slate-500"
        }
        aria-hidden="true"
      >
        {passed ? "✓" : "•"}
      </span>
      <span className={passed ? "text-emerald-200" : "text-slate-400"}>{label}</span>
    </li>
  );
}

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const passwordChecks = useMemo(() => getPasswordChecks(password), [password]);
  const passwordStrong = useMemo(() => isStrongPassword(password), [password]);
  const isSignup = mode === "signup";

  function redirectTarget() {
    const target = searchParams.get("redirect") || "/dashboard";
    if (!target.startsWith("/") || target.startsWith("//")) return "/dashboard";
    return target;
  }

  async function syncProfile(userId: string) {
    const token = await getSessionToken();
    if (!token) return;

    await apiPost(
      "/profile",
      {
        id: userId,
        email: email.trim(),
        full_name: fullName.trim() || email.trim().split("@")[0],
        preferred_language: "English",
        plan: "free",
      },
      { headers: { Authorization: `Bearer ${token}` } }
    );
  }

  async function submit() {
    setError(null);
    setStatus(null);

    const cleanEmail = email.trim().toLowerCase();
    const cleanName = fullName.trim();

    if (!cleanEmail) {
      setError("Please enter your email address.");
      return;
    }

    if (isSignup && !cleanName) {
      setError("Please enter your full name.");
      return;
    }

    if (isSignup && !passwordStrong) {
      setError("Use a stronger password with uppercase, lowercase, number, special character, and minimum 8 characters.");
      return;
    }

    if (!isSignup && !password) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);

    try {
      const client = getSupabaseClient();
      if (!client) {
        setError("Supabase is not configured. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY, then redeploy.");
        return;
      }

      if (isSignup) {
        const emailRedirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(redirectTarget())}`;

        const { data, error: signUpError } = await client.auth.signUp({
          email: cleanEmail,
          password,
          options: {
            emailRedirectTo,
            data: {
              full_name: cleanName,
            },
          },
        });

        if (signUpError) throw signUpError;

        if (data.user?.id && data.session) {
          await syncProfile(data.user.id);
          setStatus("Account created. Opening your dashboard...");
          router.push(redirectTarget());
          router.refresh();
          return;
        }

        setStatus("Account created. Please verify your email before login.");
        return;
      }

      const { data, error: loginError } = await client.auth.signInWithPassword({
        email: cleanEmail,
        password,
      });

      if (loginError) throw loginError;
      if (data.user?.id) await syncProfile(data.user.id);

      setStatus("Login successful. Opening dashboard...");
      router.push(redirectTarget());
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setLoading(false);
    }
  }

  const disabled =
    loading ||
    !email.trim() ||
    (isSignup ? !fullName.trim() || !passwordStrong : !password);

  return (
    <div className="auth-shell p-6 sm:p-8">
      <div className="relative z-[1]">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">Secure account access</p>
            <h1 className="mt-2 text-3xl font-black">{isSignup ? "Create your Web3Guard account" : "Login to Web3Guard"}</h1>
            <p className="mt-2 max-w-xl text-sm leading-6 text-slate-400">
              {isSignup
                ? "Create a real account to save scan history, reports, and future billing records."
                : "Access your protected dashboard, saved reports, and scan history from the command center."}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-xs leading-6 text-slate-400">
            <p className="font-black uppercase tracking-[0.18em] text-cyan">Security posture</p>
            <p>No seed phrases · No fake sessions · Real Supabase auth only</p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="grid gap-4">
            {isSignup && (
              <label className="grid gap-2 text-sm font-semibold text-slate-300">
                Full name
                <input
                  className="input"
                  name="web3guard_full_name"
                  autoComplete="off"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="Full name"
                />
              </label>
            )}

            <label className="grid gap-2 text-sm font-semibold text-slate-300">
              Email
              <input
                className="input"
                name="web3guard_email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
              />
            </label>

            <label className="grid gap-2 text-sm font-semibold text-slate-300">
              Password
              <div className="flex rounded-[14px] border border-white/10 bg-[rgba(6,15,30,0.7)] focus-within:border-cyan/30 focus-within:shadow-[0_0_0_3px_rgba(6,182,212,.10)]">
                <input
                  className="w-full bg-transparent px-4 py-3 text-sm text-white outline-none"
                  type={showPassword ? "text" : "password"}
                  name="web3guard_password"
                  autoComplete={isSignup ? "new-password" : "current-password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder={isSignup ? "Create password" : "Enter password"}
                />
                <button
                  type="button"
                  className="px-4 text-xs font-bold uppercase tracking-[0.15em] text-slate-400 hover:text-white"
                  onClick={() => setShowPassword((value) => !value)}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </label>

            {error ? <div className="rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">{error}</div> : null}
            {status ? <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">{status}</div> : null}

            <button className="btn-primary w-full" disabled={disabled} onClick={submit} type="button">
              {loading ? "Please wait..." : isSignup ? "Create account" : "Login"}
            </button>

            <p className="text-sm text-slate-400">
              {isSignup ? "Already have an account?" : "New to Web3Guard?"}{" "}
              <Link href={isSignup ? "/auth/login" : "/auth/signup"} className="font-bold text-cyan hover:text-cyan-200">
                {isSignup ? "Login" : "Create account"}
              </Link>
            </p>
          </div>

          <div className="glass-tile p-5">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan">Access preview</p>
            <div className="mt-4 space-y-3 text-sm text-slate-300">
              <div className="command-line">
                <span className="kbd-chip">01</span>
                <span>Dashboard + project workspace</span>
              </div>
              <div className="command-line">
                <span className="kbd-chip">02</span>
                <span>Saved reports + scan history</span>
              </div>
              <div className="command-line">
                <span className="kbd-chip">03</span>
                <span>Future subscriptions and billing records</span>
              </div>
            </div>

            {isSignup ? (
              <div className="mt-5 rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-sm font-bold text-white">Password strength</p>
                <ul className="mt-3 grid gap-2 text-sm">
                  <PasswordRule passed={passwordChecks.length} label="At least 8 characters" />
                  <PasswordRule passed={passwordChecks.uppercase} label="One uppercase letter" />
                  <PasswordRule passed={passwordChecks.lowercase} label="One lowercase letter" />
                  <PasswordRule passed={passwordChecks.number} label="One number" />
                  <PasswordRule passed={passwordChecks.special} label="One special character" />
                </ul>
              </div>
            ) : (
              <div className="mt-5 rounded-2xl border border-white/10 bg-black/20 p-4 text-sm leading-6 text-slate-400">
                Use the same email you used during signup. If email confirmation is enabled in Supabase, verify first and then login.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
