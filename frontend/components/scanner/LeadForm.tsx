"use client";

import { type FormEvent, useState } from "react";
import { apiPost } from "@/lib/api";

const packages = [
  ["quick-risk-report", "₹999 Quick Risk Scan Report", 999, "one_time"],
  ["detailed-launch-readiness", "₹2,999 Detailed Launch Readiness", 2999, "one_time"],
  ["fix-suggestion-pack", "₹7,999 Fix Suggestion Pack", 7999, "one_time"],
  ["manual-pre-audit", "₹14,999+ Manual Pre-Audit Review", 14999, "one_time"],
  ["full-launch-readiness", "₹29,999+ Full Launch Readiness Review", 29999, "one_time"],
  ["builder-monthly", "₹2,999/month Builder Subscription", 2999, "monthly"],
  ["shield-monthly", "₹9,999/month Shield Subscription", 9999, "monthly"],
];

export function LeadForm() {
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(packages[0]);

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const chosen = packages.find((item) => item[0] === formData.get("package_id")) || selected;
    setLoading(true);
    setStatus(null);
    const payload = Object.fromEntries(formData.entries());
    try {
      const data = await apiPost<{ ok: boolean; lead: { id: string; status: string; payment_status: string }; message: string }>("/lead", {
        ...payload,
        selected_package: chosen[1],
        package_id: chosen[0],
        package_amount_inr: Number(chosen[2]),
        billing_cycle: chosen[3],
        authorization_confirmed: formData.get("authorization_confirmed") === "on",
        consent_confirmed: formData.get("consent_confirmed") === "on",
      });
      setStatus(`Lead ${data.lead.id} submitted. Status: ${data.lead.status}. Save UPI reference for manual verification.`);
      event.currentTarget.reset();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Lead submission failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submitForm} className="card grid gap-4 p-6">
      <div className="rounded-2xl border border-cyan/20 bg-cyan/10 p-4 text-sm text-cyan-50">
        Phase 8 supports Razorpay verified payments and manual UPI fallback. If you used UPI manual fallback, paste the transaction/reference ID here. If Razorpay verified, paste the payment intent/order ID for admin matching.
      </div>
      <input className="input" name="name" placeholder="Your name" required />
      <input className="input" name="email" type="email" placeholder="Email" required />
      <input className="input" name="contact" placeholder="WhatsApp / Telegram" required />
      <input className="input" name="project_name" placeholder="Project name" required />
      <input className="input" name="website_url" placeholder="Website URL optional" />
      <select
        className="select"
        name="package_id"
        defaultValue="quick-risk-report"
        onChange={(e) => setSelected(packages.find((item) => item[0] === e.target.value) || packages[0])}
      >
        {packages.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
      </select>
      <input className="input" name="budget" placeholder="Budget optional" />
      <input className="input" name="payment_intent_id" placeholder="Payment intent ID optional, e.g. pay_xxxxx" />
      <input className="input" name="payment_reference" placeholder="UPI transaction/reference ID optional" />
      <select className="select" name="preferred_language" defaultValue="Hinglish">
        <option>Hinglish</option><option>English</option><option>Hindi</option>
      </select>
      <select className="select" name="urgency" defaultValue="Normal">
        <option value="Normal">Normal</option><option value="Urgent">Urgent</option>
      </select>
      <textarea className="textarea" name="message" placeholder="Tell us what you want reviewed" />
      <label className="flex gap-3 text-sm text-slate-300"><input name="authorization_confirmed" type="checkbox" required /> I own this project or have authorization.</label>
      <label className="flex gap-3 text-sm text-slate-300"><input name="consent_confirmed" type="checkbox" required /> I understand this is a preliminary review and not a certified audit.</label>
      <button className="btn-primary" disabled={loading}>{loading ? "Submitting..." : "Submit Review Request"}</button>
      {status && <p className="rounded-2xl border border-white/10 bg-white/[0.04] p-3 text-sm text-slate-200">{status}</p>}
    </form>
  );
}
