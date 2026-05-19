import { Suspense } from "react";
import LoginClient from "./LoginClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-ink px-4 py-10 text-white sm:px-6 lg:px-8">
          <div className="auth-shell mx-auto max-w-5xl p-8">
            <p className="text-sm font-semibold text-slate-300">Loading secure login...</p>
          </div>
        </main>
      }
    >
      <LoginClient />
    </Suspense>
  );
}
