type RouteLoadingShellProps = {
  label?: string;
  title: string;
  description?: string;
  cards?: number;
};

export function RouteLoadingShell({
  label = "Loading workspace",
  title,
  description = "Preparing a lightweight view while this route loads.",
  cards = 6,
}: RouteLoadingShellProps) {
  return (
    <section className="command-page px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="rounded-[2rem] border border-cyan/15 bg-white/[0.025] p-6 shadow-[0_20px_80px_rgba(0,0,0,.24)] sm:p-8">
          <p className="section-label">{label}</p>
          <div className="mt-4 grid gap-6 lg:grid-cols-[1.1fr_.9fr] lg:items-end">
            <div>
              <h1 className="max-w-3xl text-3xl font-black text-white sm:text-5xl">{title}</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-400 sm:text-base">{description}</p>
            </div>
            <div className="grid gap-3 rounded-2xl border border-white/[0.07] bg-black/20 p-4">
              <div className="phase25-skeleton h-3 w-2/3 rounded-full" />
              <div className="phase25-skeleton h-3 w-full rounded-full" />
              <div className="phase25-skeleton h-3 w-5/6 rounded-full" />
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: cards }).map((_, index) => (
            <div key={index} className="rounded-3xl border border-white/[0.07] bg-white/[0.025] p-5">
              <div className="phase25-skeleton h-10 w-10 rounded-2xl" />
              <div className="phase25-skeleton mt-5 h-3 w-3/4 rounded-full" />
              <div className="phase25-skeleton mt-3 h-3 w-full rounded-full" />
              <div className="phase25-skeleton mt-3 h-3 w-2/3 rounded-full" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
