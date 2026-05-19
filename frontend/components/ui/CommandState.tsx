import Link from "next/link";

export function CommandEmptyState({
  title,
  text,
  actionHref,
  actionLabel,
}: {
  title: string;
  text: string;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <div className="empty-state">
      <div>
        <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl border border-cyan/20 bg-cyan/10 mono text-cyan shadow-soft">
          W3
        </div>
        <h3 className="mt-4 text-lg font-black text-white">{title}</h3>
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-400">{text}</p>
        {actionHref && actionLabel ? (
          <Link href={actionHref} className="btn-secondary mt-5">
            {actionLabel}
          </Link>
        ) : null}
      </div>
    </div>
  );
}

export function CommandLoadingState({ label = "Loading command data..." }: { label?: string }) {
  return (
    <div className="command-card p-5">
      <p className="text-sm font-bold text-slate-300">{label}</p>
      <div className="mt-4 grid gap-3">
        <div className="loading-line h-4 w-full" />
        <div className="loading-line h-4 w-4/5" />
        <div className="loading-line h-4 w-2/3" />
      </div>
    </div>
  );
}

export function CommandNotice({ tone = "info", title, text }: { tone?: "info" | "warning" | "success" | "danger"; title: string; text: string }) {
  const toneClass = {
    info: "border-cyan/20 bg-cyan/10 text-cyan-50",
    warning: "border-amber-400/25 bg-amber-400/10 text-amber-100",
    success: "border-emerald-400/25 bg-emerald-400/10 text-emerald-100",
    danger: "border-red-400/25 bg-red-500/10 text-red-100",
  }[tone];

  return (
    <div className={`rounded-2xl border p-4 text-sm leading-6 ${toneClass}`}>
      <p className="font-black">{title}</p>
      <p className="mt-1 opacity-90">{text}</p>
    </div>
  );
}
