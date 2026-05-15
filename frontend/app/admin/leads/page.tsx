"use client";

import { useMemo, useState } from "react";
import { API_BASE, apiPatch, apiPost } from "@/lib/api";

type Lead = {
  id: string;
  created_at: string;
  name: string;
  email: string;
  contact: string;
  project_name: string;
  selected_package: string;
  package_id?: string | null;
  package_amount_inr?: number | null;
  billing_cycle?: string;
  status: string;
  payment_status?: string;
  payment_reference?: string | null;
  payment_intent_id?: string | null;
  assigned_reviewer?: string | null;
  urgency?: string;
  internal_notes?: string[];
};

type Summary = {
  total: number;
  new: number;
  payment_pending: number;
  paid: number;
  in_review: number;
  delivered: number;
  revenue_pipeline_inr: number;
  verified_revenue_inr: number;
};

const statuses = ["New", "Contacted", "Payment Pending", "Paid", "In Review", "Delivered", "Closed", "Refunded", "Rejected / Out of Scope"];
const paymentStatuses = ["created", "reference_submitted", "manual_verification_pending", "verified", "failed", "cancelled"];

export default function AdminLeadsPage() {
  const [token, setToken] = useState("");
  const [leads, setLeads] = useState<Lead[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const authHeaders = useMemo(() => ({ "x-admin-token": token }), [token]);

  async function load() {
    setError(null);
    const search = query ? `?q=${encodeURIComponent(query)}` : "";
    const response = await fetch(`${API_BASE}/admin/leads${search}`, { headers: authHeaders });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) { setError(data.detail || "Failed to load leads"); return; }
    setLeads(data.leads || []);
    setSummary(data.summary || null);
  }

  async function downloadCsv() {
    setError(null);
    const response = await fetch(`${API_BASE}/admin/leads.csv`, { headers: authHeaders });
    if (!response.ok) { setError("CSV export failed"); return; }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "raadhanex-web3guard-leads.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function updateLead(path: string, payload: unknown, id: string) {
    setBusy(id);
    setError(null);
    try {
      await apiPatch(path, payload, { headers: authHeaders });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setBusy(null);
    }
  }

  async function addNote(leadId: string) {
    const note = window.prompt("Internal note");
    if (!note) return;
    setBusy(leadId);
    try {
      await apiPost(`/admin/leads/${leadId}/note`, { note, reviewer: "RAADHANEX admin" }, { headers: authHeaders });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Note failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">Admin</p>
      <h1 className="mt-3 text-4xl font-black">RAADHANEX income funnel dashboard</h1>
      <p className="mt-3 max-w-3xl text-slate-400">Track leads, UPI references, manual payment verification, review status, reviewer assignment, and CSV export.</p>
      <div className="card mt-8 grid gap-3 p-5 md:grid-cols-[1fr_1fr_auto_auto]">
        <input className="input" value={token} onChange={(e) => setToken(e.target.value)} placeholder="Admin token from backend .env" />
        <input className="input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search project/name/email/package" />
        <button className="btn-primary" onClick={load}>Load Leads</button>
        {token && <button className="btn-secondary" onClick={downloadCsv}>Download CSV</button>}
      </div>
      {summary && (
        <div className="mt-6 grid gap-4 md:grid-cols-4">
          <div className="card p-4"><p className="text-sm text-slate-400">Total leads</p><p className="text-3xl font-black">{summary.total}</p></div>
          <div className="card p-4"><p className="text-sm text-slate-400">Payment pending</p><p className="text-3xl font-black">{summary.payment_pending}</p></div>
          <div className="card p-4"><p className="text-sm text-slate-400">Verified revenue</p><p className="text-3xl font-black">₹{summary.verified_revenue_inr.toLocaleString("en-IN")}</p></div>
          <div className="card p-4"><p className="text-sm text-slate-400">Pipeline value</p><p className="text-3xl font-black">₹{summary.revenue_pipeline_inr.toLocaleString("en-IN")}</p></div>
        </div>
      )}
      {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4 text-red-100">{error}</p>}
      <div className="card mt-6 overflow-x-auto">
        <table className="w-full min-w-[1250px] text-left text-sm">
          <thead className="bg-white/[0.04] text-slate-200">
            <tr>
              <th className="p-4">Project</th><th className="p-4">Client</th><th className="p-4">Package</th><th className="p-4">Amount</th><th className="p-4">Lead Status</th><th className="p-4">Payment</th><th className="p-4">Reference</th><th className="p-4">Reviewer</th><th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>{leads.map((lead) => (
            <tr key={lead.id} className="border-t border-white/10 align-top">
              <td className="p-4"><p className="font-bold">{lead.project_name}</p><p className="text-xs text-slate-500">{lead.id}</p></td>
              <td className="p-4"><p>{lead.name}</p><p className="text-xs text-slate-500">{lead.email}</p><p className="text-xs text-slate-500">{lead.contact}</p></td>
              <td className="p-4"><p>{lead.selected_package}</p><p className="text-xs text-slate-500">{lead.billing_cycle || "one_time"}</p></td>
              <td className="p-4">₹{(lead.package_amount_inr || 0).toLocaleString("en-IN")}</td>
              <td className="p-4"><select className="select min-w-[150px]" value={lead.status} disabled={busy === lead.id} onChange={(e) => updateLead(`/admin/leads/${lead.id}/status`, { status: e.target.value }, lead.id)}>{statuses.map((status) => <option key={status}>{status}</option>)}</select></td>
              <td className="p-4"><select className="select min-w-[190px]" value={lead.payment_status || "created"} disabled={busy === lead.id} onChange={(e) => updateLead(`/admin/leads/${lead.id}/payment`, { payment_status: e.target.value, payment_reference: lead.payment_reference || null, payment_intent_id: lead.payment_intent_id || null }, lead.id)}>{paymentStatuses.map((status) => <option key={status}>{status}</option>)}</select></td>
              <td className="p-4"><p>{lead.payment_reference || "—"}</p><p className="text-xs text-slate-500">{lead.payment_intent_id || "no intent"}</p></td>
              <td className="p-4"><input className="input min-w-[170px]" defaultValue={lead.assigned_reviewer || ""} onBlur={(e) => updateLead(`/admin/leads/${lead.id}/assign`, { assigned_reviewer: e.target.value || null }, lead.id)} placeholder="Reviewer" /></td>
              <td className="p-4"><button className="btn-secondary whitespace-nowrap" onClick={() => addNote(lead.id)} disabled={busy === lead.id}>Add Note</button><p className="mt-2 text-xs text-slate-500">Notes: {lead.internal_notes?.length || 0}</p></td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  );
}
