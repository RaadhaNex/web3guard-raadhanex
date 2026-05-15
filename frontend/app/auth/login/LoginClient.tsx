"use client";
import { Suspense } from "react";
import LoginClient from "./LoginClient";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-white px-6 py-10 text-slate-950">
          <div className="mx-auto max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <p className="text-sm font-semibold text-slate-700">
              Loading secure login...
            </p>
          </div>
        </main>
      }
    >
      <LoginClient />
    </Suspense>
  );
}