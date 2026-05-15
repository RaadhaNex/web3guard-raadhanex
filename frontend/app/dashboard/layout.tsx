import type { ReactNode } from "react";
import { redirect } from "next/navigation";
import { getSupabaseServerClient, isSupabaseServerConfigured } from "@/lib/supabaseServer";

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  if (!isSupabaseServerConfigured) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="card p-6">
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-amber-200">Provider Not Configured</p>
          <h1 className="mt-3 text-3xl font-black">Supabase Auth is required for the protected dashboard.</h1>
          <p className="mt-3 text-slate-300">
            Add real <code>NEXT_PUBLIC_SUPABASE_URL</code> and <code>NEXT_PUBLIC_SUPABASE_ANON_KEY</code> in the frontend, plus backend Supabase env keys before storing private project data.
          </p>
          <p className="mt-4 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm text-amber-50">
            No fake session is created here. Dashboard records should be viewed only after real signup/login.
          </p>
        </div>
      </main>
    );
  }

  const supabase = getSupabaseServerClient();
  const { data } = await supabase!.auth.getSession();
  if (!data.session) redirect("/auth/login?redirect=/dashboard");

  return <>{children}</>;
}
