"use client";

import { type FormEvent, useState } from "react";
import { apiPost } from "@/lib/api";

const reviewIntents = [
  ["free-scan-followup", "Free scan follow-up", 0, "one_time"],
  ["builder-scope", "Builder scope conversation", 0, "one_time"],
  ["pre-audit-pack", "Pre-audit pack preparation", 0, "one_time"],
  ["bug-bounty-readiness", "Bug bounty readiness", 0, "one_time"],
  ["launch-readiness", "Launch readiness review", 0, "one_time"],
  ["post-launch-protection", "Post-launch protection planning", 0, "one_time"],
];

export function LeadForm() {
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(reviewIntents[0]);

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const chosen = reviewIntents.find((item) => item[0] === formData.get("package_id")) || selected;
    setLoading(true);
    setStatus(null);
    const payload = Object.fromEntries(formData.entries());
    try {
      const data = await apiPost<{ ok: boolean; lead: { id: string; status: string; payment_status?: string }; message: string }>("/lead", {
        ...payload,
        selected_package: chosen[1],
        package_id: chosen[0],
        package_amount_inr: Number(chosen[2]),
        billing_cycle: chosen[3],
        authorization_confirmed: formData.get("authorization_confirmed") === "on",
        consent_confirmed: formData.get("consent_confirmed") === "on",
      });
      setStatus(`Scope request ${data.lead.id} submitted. Status: ${data.lead.status}.`);
      event.currentTarget.reset();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Scope request submission failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submitForm} className="card grid gap-4 p-6">
      <div className="rounded-2xl border border-cyan/20 bg-cyan/10 p-4 text-sm leading-6 text-cyan-50">
        Submit scope context only. Payments are deferred until the final verified payment phase; this form does not confirm paid access, subscriptions, or audit certification.
      </div>
      <input className="input" name="name" placeholder="Your name" required />
      <input className="input" name="email" type="email" placeholder="Email" required />
      <input className="input" name="contact" placeholder="WhatsApp / Telegram" required />
      <input className="input" name="project_name" placeholder="Project name" required />
      <input className="input" name="website_url" placeholder="Website URL optional" />
      <select
        className="select"
        name="package_id"
        defaultValue="free-scan-followup"
        onChange={(event) => setSelected(reviewIntents.find((item) => item[0] === event.target.value) || reviewIntents[0])}
      >
        {reviewIntents.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
      </select>
      <input className="input" name="budget" placeholder="Budget optional for future scoped work" />
      <select className="select" name="preferred_language" defaultValue="Hinglish">
        <option>Hinglish</option><option>English</option><option>Hindi</option>
      </select>
      <select className="select" name="urgency" defaultValue="Normal">
        <option value="Normal">Normal</option><option value="Urgent">Urgent</option>
      </select>
      <textarea className="textarea" name="message" placeholder="Tell us what you want reviewed. Do not paste secrets." />
      <label className="flex gap-3 text-sm text-slate-300"><input name="authorization_confirmed" type="checkbox" required /> I own this project or have authorization.</label>
      <label className="flex gap-3 text-sm text-slate-300"><input name="consent_confirmed" type="checkbox" required /> I understand this is a preliminary review and not a certified audit.</label>
      <button className="btn-primary" disabled={loading}>{loading ? "Submitting..." : "Submit scope request"}</button>
      {status ? <p className="rounded-2xl border border-white/10 bg-white/[0.04] p-3 text-sm text-slate-200">{status}</p> : null}
    </form>
  );
}
