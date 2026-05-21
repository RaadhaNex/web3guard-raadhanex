import { WebDastClient } from "@/components/web-dast/WebDastClient";

export default function WebDastPage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <section className="clean-panel p-6 sm:p-8">
        <p className="section-label">Verified authorized web DAST</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">
          Authorized web security checks without unsafe hacking automation.
        </h1>
        <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
          Verify ownership or written permission, lock scope, then run passive baseline or light non-destructive authorized checks. Brute force, DoS, RCE exploitation, data extraction, wallet signing, and private-key collection stay blocked.
        </p>
      </section>
      <WebDastClient />
    </main>
  );
}
