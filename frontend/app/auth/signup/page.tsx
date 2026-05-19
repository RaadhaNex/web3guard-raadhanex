import { Suspense } from "react";
import { AuthForm } from "@/components/auth/AuthForm";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function SignupPage() {
  return (
    <main className="min-h-screen bg-ink px-4 py-10 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-5xl">
        <Suspense
          fallback={
            <div className="auth-shell p-8">
              <p className="text-sm font-semibold text-slate-300">Loading secure signup...</p>
            </div>
          }
        >
          <AuthForm mode="signup" />
        </Suspense>
      </section>
    </main>
  );
}
