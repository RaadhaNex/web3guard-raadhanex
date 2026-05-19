export default function LanguageSettingsPage() {
  return (
    <main className="min-h-screen bg-ink px-4 py-10 text-white sm:px-6 lg:px-8">
      <section className="auth-shell mx-auto max-w-4xl p-6 sm:p-8">
        <div className="relative z-[1]">
          <p className="section-label">Settings</p>
          <h1 className="mt-3 text-3xl font-black tracking-tight sm:text-5xl">Language & preferences</h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400">
            This page is reserved for account-level language, report tone, and notification preferences. Scanner outputs stay evidence-based and missing modules remain Not Assessed.
          </p>

          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {[
              "English reports",
              "Hindi/Hinglish explanations",
              "Developer fix hints",
              "Founder-friendly summaries",
            ].map((item, index) => (
              <div key={item} className="command-line">
                <span className="kbd-chip">0{index + 1}</span>
                <span className="text-sm font-bold text-slate-200">{item}</span>
              </div>
            ))}
          </div>

          <p className="mt-6 rounded-2xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm font-semibold text-amber-100">
            Preference persistence can be wired later to Supabase profile/settings. This page avoids broken navigation while keeping production scanner logic unchanged.
          </p>
        </div>
      </section>
    </main>
  );
}
