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
            ? "flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-xs font-black text-emerald-600"
            : "flex h-5 w-5 items-center justify-center rounded-full border border-slate-300 text-xs font-black text-slate-400"
        }
        aria-hidden="true"
      >
        {passed ? "✓" : "•"}
      </span>
      <span className={passed ? "text-emerald-700" : "text-slate-600"}>
        {label}
      </span>
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
      setError(
        "Please create a stronger password with uppercase, lowercase, number, special character, and at least 8 characters."
      );
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
        setError(
          "Supabase is not configured. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in Vercel, then redeploy."
        );
        return;
      }

      if (isSignup) {
        const emailRedirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(
          redirectTarget()
        )}`;

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
          setStatus("Account created. Redirecting to your dashboard...");
          router.push(redirectTarget());
          router.refresh();
          return;
        }

        setStatus(
          "Account created. Please check your email and confirm your account before login."
        );
        return;
      }

      const { data, error: loginError } = await client.auth.signInWithPassword({
        email: cleanEmail,
        password,
      });

      if (loginError) throw loginError;
      if (data.user?.id) await syncProfile(data.user.id);

      setStatus("Login successful. Redirecting to your dashboard...");
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
    <div className="card p-6 sm:p-8">
      <div className="mb-6">
        <p className="text-xs font-bold uppercase tracking-[0.25em] text-cyan">
          Secure account access
        </p>
        <h1 className="mt-2 text-3xl font-black">
          {isSignup ? "Create your account" : "Login to Web3Guard"}
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-500">
          {isSignup
            ? "Use a real email to save scan history, reports, and billing records."
            : "Access your protected dashboard, reports, and saved scan history."}
        </p>
      </div>

      <div className="grid gap-4">
        {isSignup && (
          <label className="grid gap-2 text-sm font-semibold text-slate-700">
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

        <label className="grid gap-2 text-sm font-semibold text-slate-700">
          Email
          <input
            className="input"
            name="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="founder@example.com"
          />
        </label>

        <label className="grid gap-2 text-sm font-semibold text-slate-700">
          Password
          <div className="relative">
            <input
              className="input pr-24"
              name={isSignup ? "new-password" : "current-password"}
              type={showPassword ? "text" : "password"}
              autoComplete={isSignup ? "new-password" : "current-password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder={
                isSignup
                  ? "Minimum 8 chars with A-z, 0-9 and special char"
                  : "Enter your password"
              }
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full border border-slate-200 px-3 py-1 text-xs font-bold text-slate-600 hover:bg-slate-100"
              onClick={() => setShowPassword((value) => !value)}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
        </label>

        {isSignup && (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm">
            <p className="mb-3 font-bold text-slate-900">Password must include:</p>
            <ul className="grid gap-2 sm:grid-cols-2">
              <PasswordRule passed={passwordChecks.length} label="At least 8 characters" />
              <PasswordRule passed={passwordChecks.uppercase} label="One uppercase letter" />
              <PasswordRule passed={passwordChecks.lowercase} label="One lowercase letter" />
              <PasswordRule passed={passwordChecks.number} label="One number" />
              <PasswordRule passed={passwordChecks.special} label="One special character" />
            </ul>
          </div>
        )}

        <button className="btn-primary" disabled={disabled} onClick={submit}>
          {loading
            ? "Please wait..."
            : isSignup
              ? "Create account"
              : "Login"}
        </button>
      </div>

      {status && (
        <div className="mt-4 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-700">
          {status}
        </div>
      )}
      {error && (
        <div className="mt-4 rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <p className="mt-5 text-sm text-slate-500">
        {isSignup ? "Already have an account? " : "Need an account? "}
        <Link
          className="font-bold text-cyan hover:text-slate-900"
          href={isSignup ? "/auth/login" : "/auth/signup"}
        >
          {isSignup ? "Login" : "Create account"}
        </Link>
      </p>
    </div>
  );
}
