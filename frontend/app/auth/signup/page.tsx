import { Suspense } from "react";
import { AuthForm } from "@/components/auth/AuthForm";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function SignupPage() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
      <Suspense
        fallback={
          <div className="card p-6 sm:p-8">
            <p className="text-sm font-semibold text-slate-600">
              Loading secure signup...
            </p>
          </div>
        }
      >
        <AuthForm mode="signup" />
      </Suspense>
    </main>
  );
}
