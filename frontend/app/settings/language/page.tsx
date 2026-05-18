export default function LanguageSettingsPage() {
  return (
    <main className="min-h-screen bg-[#f7fafc] px-4 py-10 text-slate-950 sm:px-6 lg:px-8">
      <section className="mx-auto max-w-3xl rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <p className="text-xs font-black uppercase tracking-[0.28em] text-cyan-600">Settings</p>
        <h1 className="mt-3 text-3xl font-black tracking-tight sm:text-5xl">Language & preferences</h1>
        <p className="mt-4 text-sm leading-6 text-slate-600">
          This page is reserved for account-level language, report tone, and notification preferences. Core scanner outputs remain evidence-based and missing modules remain Not assessed.
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {[
            "English reports",
            "Hindi/Hinglish explanations",
            "Developer fix hints",
            "Founder-friendly summaries",
          ].map((item) => (
            <div key={item} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm font-bold text-slate-700">
              {item}
            </div>
          ))}
        </div>
        <p className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-900">
          Preference persistence can be wired later to Supabase profile/settings. This placeholder avoids broken navigation while keeping production scanner logic unchanged.
        </p>
      </section>
    </main>
  );
}
