"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type AgencyStatus = {
  ok: boolean;
  phase: string;
  mode: string;
  counts: Record<string, number>;
  capabilities: string[];
  blocked_claims: string[];
  real_only_note: string;
  safe_boundary: string;
};

type ClientProfile = {
  id: string;
  client_name: string;
  project_name?: string | null;
  website_url?: string | null;
  status: string;
  tags?: string[];
  safe_wording?: string;
};

type IntakeRequest = {
  id: string;
  client_name: string;
  scope_summary: string;
  requested_services?: string[];
  priority?: string;
  status: string;
  created_at: string;
};

type WhiteLabelSettings = {
  id: string;
  brand_name: string;
  report_footer?: string;
  custom_disclaimer?: string;
  show_powered_by_raadhanex?: boolean;
  safe_wording?: string;
};

type HandoffPack = {
  id: string;
  client_id?: string | null;
  client_name: string;
  project_name?: string | null;
  status: string;
  executive_summary: string;
  services_included: string[];
  open_items: string[];
  evidence_links: string[];
  handoff_checklist: string[];
  client_email_template: { subject: string; body: string };
  safe_wording: string;
  created_at: string;
};

type Portfolio = {
  ok: boolean;
  portfolio: Array<{
    client_id: string;
    client_name: string;
    project_name?: string | null;
    website_url?: string | null;
    status: string;
    tags?: string[];
    handoff_count: number;
    latest_handoff_status: string;
    safe_wording: string;
  }>;
  intake_queue: IntakeRequest[];
  latest_white_label_settings?: WhiteLabelSettings | null;
  totals: Record<string, number>;
  team_role_playbook: Array<{ role: string; scope: string }>;
  blocked_claims: string[];
  real_only_note: string;
  safe_boundary: string;
};

const defaultServices = [
  "pre_audit_readiness_review",
  "launch_trust_readiness",
  "public_trust_page_setup",
  "security_passport_setup",
  "community_review_coordination",
  "monitoring_lite_setup",
];

function joinList(raw: string) {
  return raw
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 12);
}

function Stat({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="stat-slab p-4">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 truncate text-2xl font-black text-cyan">{value ?? "—"}</p>
    </div>
  );
}

function Notice({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-3xl border border-amber-300/20 bg-amber-300/10 p-5 text-amber-50">
      <p className="font-black">{title}</p>
      <p className="mt-2 text-sm leading-6 text-amber-100/80">{text}</p>
    </div>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return <span className="badge badge-cyan">{children}</span>;
}

export function AgencyLaunchClient() {
  const [ownerUserId, setOwnerUserId] = useState("local-demo-user");
  const [organizationId, setOrganizationId] = useState("");
  const [status, setStatus] = useState<AgencyStatus | null>(null);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [clients, setClients] = useState<ClientProfile[]>([]);
  const [handoffs, setHandoffs] = useState<HandoffPack[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const [clientName, setClientName] = useState("");
  const [projectName, setProjectName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [projectSummary, setProjectSummary] = useState("");
  const [tags, setTags] = useState("defi\nlaunch-readiness");

  const [intakeClient, setIntakeClient] = useState("");
  const [intakeScope, setIntakeScope] = useState("");
  const [requestedServices, setRequestedServices] = useState(defaultServices.slice(0, 4).join("\n"));

  const [brandName, setBrandName] = useState("My Agency Security Desk");
  const [reportFooter, setReportFooter] = useState("Prepared as a pre-audit readiness handoff. Not a certified audit.");

  const [handoffClientId, setHandoffClientId] = useState("");
  const [handoffClientName, setHandoffClientName] = useState("");
  const [handoffSummary, setHandoffSummary] = useState("Pre-audit readiness handoff prepared from available evidence and open actions.");
  const [openItems, setOpenItems] = useState("Schedule external certified audit for production-critical contracts.\nKeep Not Assessed modules visible until evidence is uploaded.");
  const [evidenceLinks, setEvidenceLinks] = useState("/security-passport\n/trust-pages\n/report/verify");

  const query = useMemo(() => {
    const params = new URLSearchParams({ owner_user_id: ownerUserId || "local-demo-user" });
    if (organizationId.trim()) params.set("organization_id", organizationId.trim());
    return params.toString();
  }, [ownerUserId, organizationId]);

  async function loadAll() {
    setLoading(true);
    setMessage("");
    try {
      const [statusData, portfolioData, clientsData, handoffData] = await Promise.all([
        apiGet<AgencyStatus>("/agency-launch/status"),
        apiGet<Portfolio>(`/agency-launch/portfolio?${query}`),
        apiGet<{ clients: ClientProfile[] }>(`/agency-launch/clients?${query}`),
        apiGet<{ handoff_packs: HandoffPack[] }>(`/agency-launch/handoff-packs?${query}`),
      ]);
      setStatus(statusData);
      setPortfolio(portfolioData);
      setClients(clientsData.clients || []);
      setHandoffs(handoffData.handoff_packs || []);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load agency launch layer.");
    } finally {
      setLoading(false);
    }
  }

  async function createClient(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      await apiPost("/agency-launch/clients", {
        owner_user_id: ownerUserId,
        organization_id: organizationId || null,
        client_name: clientName,
        project_name: projectName || null,
        website_url: websiteUrl || null,
        project_summary: projectSummary,
        tags: joinList(tags),
        status: "active",
        authorization_confirmed: true,
      });
      setClientName("");
      setProjectName("");
      setWebsiteUrl("");
      setProjectSummary("");
      setMessage("Client profile saved. It stays private owner-created data, not a public customer claim.");
      await loadAll();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save client profile.");
    } finally {
      setLoading(false);
    }
  }

  async function createIntake(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      await apiPost("/agency-launch/intake", {
        owner_user_id: ownerUserId,
        organization_id: organizationId || null,
        client_name: intakeClient,
        scope_summary: intakeScope,
        requested_services: joinList(requestedServices),
        authorization_confirmed: true,
        safe_use_acknowledged: true,
      });
      setIntakeClient("");
      setIntakeScope("");
      setMessage("Intake request saved with safe-scope acknowledgement.");
      await loadAll();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save intake request.");
    } finally {
      setLoading(false);
    }
  }

  async function saveWhiteLabel(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      await apiPost("/agency-launch/white-label", {
        owner_user_id: ownerUserId,
        organization_id: organizationId || null,
        brand_name: brandName,
        report_footer: reportFooter,
        custom_disclaimer: "Prepared as a pre-audit readiness handoff. Not a certified audit or guarantee of security.",
        show_powered_by_raadhanex: true,
        client_safe_wording: "White-label presentation only. No certified-audit claim is created.",
      });
      setMessage("White-label settings saved. Unsafe audit/certification wording is blocked.");
      await loadAll();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save white-label settings.");
    } finally {
      setLoading(false);
    }
  }

  async function createHandoff(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      await apiPost("/agency-launch/handoff-packs", {
        owner_user_id: ownerUserId,
        organization_id: organizationId || null,
        client_id: handoffClientId || null,
        client_name: handoffClientName || null,
        executive_summary: handoffSummary,
        services_included: defaultServices,
        open_items: joinList(openItems),
        evidence_links: joinList(evidenceLinks),
        authorization_confirmed: true,
      });
      setHandoffClientName("");
      setMessage("Client handoff pack generated as a readiness handoff, not a certified audit.");
      await loadAll();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not create handoff pack.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totals = portfolio?.totals || status?.counts || {};

  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8 grid gap-6 lg:grid-cols-[1fr_0.72fr] lg:items-end">
        <div>
          <p className="section-label">Agency Launch Layer</p>
          <h1 className="mt-3 text-4xl font-black tracking-[-0.05em] sm:text-5xl">
            Client portfolio, white-label handoff, and agency workflow without fake enterprise claims.
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-400">
            Manage owner-created client records, intake requests, reviewer roles, white-label report settings, and client handoff packs. The layer preserves the pre-audit boundary and blocks certified-audit/100% secure wording.
          </p>
        </div>
        <div className="glass-tile p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan">Real-only boundary</p>
          <p className="mt-2 text-lg font-black text-white">Agency records are manual and evidence-first</p>
          <p className="mt-2 text-sm leading-6 text-slate-400">{status?.real_only_note || "No fake enterprise customers, fake reviewer badges, or fake audit wording."}</p>
        </div>
      </div>

      {message ? <Notice title="Status" text={message} /> : null}

      <section className="mt-6 grid gap-4 md:grid-cols-[1fr_1fr_auto]">
        <input className="input" value={ownerUserId} onChange={(event) => setOwnerUserId(event.target.value)} placeholder="owner_user_id" />
        <input className="input" value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} placeholder="organization_id optional" />
        <button className="btn-primary" onClick={loadAll} disabled={loading}>{loading ? "Loading..." : "Refresh"}</button>
      </section>

      <section className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Clients" value={totals.clients ?? totals.client_profiles ?? 0} />
        <Stat label="Intake" value={totals.intake_requests ?? 0} />
        <Stat label="Handoffs" value={totals.handoff_packs ?? 0} />
        <Stat label="White-label" value={totals.white_label_profiles ?? totals.white_label_settings ?? 0} />
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-2">
        <form onSubmit={createClient} className="glass-tile grid gap-4 p-5">
          <div>
            <p className="text-xl font-black text-white">Add client profile</p>
            <p className="mt-1 text-sm text-slate-500">Private agency/client record. Not a public customer proof.</p>
          </div>
          <input className="input" value={clientName} onChange={(event) => setClientName(event.target.value)} placeholder="Client name" required />
          <input className="input" value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="Project name optional" />
          <input className="input" value={websiteUrl} onChange={(event) => setWebsiteUrl(event.target.value)} placeholder="Website URL optional" />
          <textarea className="input min-h-[110px]" value={projectSummary} onChange={(event) => setProjectSummary(event.target.value)} placeholder="Project summary and authorized scope notes" />
          <textarea className="input min-h-[80px]" value={tags} onChange={(event) => setTags(event.target.value)} placeholder="Tags, one per line" />
          <button className="btn-primary" disabled={loading}>Save client</button>
        </form>

        <form onSubmit={createIntake} className="glass-tile grid gap-4 p-5">
          <div>
            <p className="text-xl font-black text-white">Create intake request</p>
            <p className="mt-1 text-sm text-slate-500">Scope-first request queue for agency/client work.</p>
          </div>
          <input className="input" value={intakeClient} onChange={(event) => setIntakeClient(event.target.value)} placeholder="Client / lead name" required />
          <textarea className="input min-h-[120px]" value={intakeScope} onChange={(event) => setIntakeScope(event.target.value)} placeholder="Authorized scope summary" required />
          <textarea className="input min-h-[110px]" value={requestedServices} onChange={(event) => setRequestedServices(event.target.value)} placeholder="Requested services, one per line" />
          <div className="rounded-2xl border border-cyan/15 bg-cyan/[0.05] p-4 text-xs leading-6 text-slate-400">
            Safe intake requires ownership/authorization and blocks private key, seed phrase, wallet signing, and exploit requests.
          </div>
          <button className="btn-primary" disabled={loading}>Save intake</button>
        </form>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <form onSubmit={saveWhiteLabel} className="glass-tile grid gap-4 p-5">
          <div>
            <p className="text-xl font-black text-white">White-label report settings</p>
            <p className="mt-1 text-sm text-slate-500">Presentation-only. It cannot create audit/certification claims.</p>
          </div>
          <input className="input" value={brandName} onChange={(event) => setBrandName(event.target.value)} placeholder="Agency brand name" required />
          <textarea className="input min-h-[100px]" value={reportFooter} onChange={(event) => setReportFooter(event.target.value)} placeholder="Report footer safe wording" />
          <button className="btn-primary" disabled={loading}>Save white-label</button>
          {portfolio?.latest_white_label_settings ? (
            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
              <p className="text-sm font-black text-white">Latest: {portfolio.latest_white_label_settings.brand_name}</p>
              <p className="mt-2 text-xs leading-6 text-slate-500">{portfolio.latest_white_label_settings.safe_wording}</p>
            </div>
          ) : null}
        </form>

        <form onSubmit={createHandoff} className="glass-tile grid gap-4 p-5">
          <div>
            <p className="text-xl font-black text-white">Build client handoff pack</p>
            <p className="mt-1 text-sm text-slate-500">Handoff pack includes open items, evidence links, and client-safe email copy.</p>
          </div>
          <select className="input" value={handoffClientId} onChange={(event) => setHandoffClientId(event.target.value)}>
            <option value="">Select saved client or type name below</option>
            {clients.map((client) => (
              <option key={client.id} value={client.id}>{client.client_name}</option>
            ))}
          </select>
          <input className="input" value={handoffClientName} onChange={(event) => setHandoffClientName(event.target.value)} placeholder="Client name if no saved client selected" />
          <textarea className="input min-h-[90px]" value={handoffSummary} onChange={(event) => setHandoffSummary(event.target.value)} />
          <textarea className="input min-h-[90px]" value={openItems} onChange={(event) => setOpenItems(event.target.value)} placeholder="Open items, one per line" />
          <textarea className="input min-h-[90px]" value={evidenceLinks} onChange={(event) => setEvidenceLinks(event.target.value)} placeholder="Evidence links, one per line" />
          <button className="btn-primary" disabled={loading}>Generate handoff</button>
        </form>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="glass-tile p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xl font-black text-white">Client portfolio</p>
              <p className="mt-1 text-sm text-slate-500">Saved records only. No fake customer/social proof.</p>
            </div>
            <Pill>{portfolio?.portfolio?.length || 0} records</Pill>
          </div>
          <div className="mt-5 grid gap-3">
            {portfolio?.portfolio?.length ? portfolio.portfolio.map((client) => (
              <div key={client.client_id} className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="font-black text-white">{client.client_name}</p>
                    <p className="mt-1 text-xs text-slate-500">{client.project_name || "Project not linked"} · {client.website_url || "No URL"}</p>
                  </div>
                  <span className="badge badge-green">{client.status}</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(client.tags || []).map((tag) => <Pill key={tag}>{tag}</Pill>)}
                  <span className="badge badge-purple">{client.handoff_count} handoff</span>
                  <span className="badge badge-cyan">{client.latest_handoff_status}</span>
                </div>
                <p className="mt-3 text-xs leading-6 text-slate-500">{client.safe_wording}</p>
              </div>
            )) : (
              <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-5 text-sm text-slate-400">No client records yet. Add a client profile to start the agency workspace.</div>
            )}
          </div>
        </div>

        <div className="glass-tile p-5">
          <p className="text-xl font-black text-white">Team role playbook</p>
          <div className="mt-5 grid gap-3">
            {(portfolio?.team_role_playbook || []).map((item) => (
              <div key={item.role} className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                <p className="text-sm font-black uppercase tracking-[0.18em] text-cyan">{item.role}</p>
                <p className="mt-2 text-sm leading-6 text-slate-400">{item.scope}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="glass-tile p-5">
          <p className="text-xl font-black text-white">Intake queue</p>
          <div className="mt-5 grid gap-3">
            {portfolio?.intake_queue?.length ? portfolio.intake_queue.map((item) => (
              <div key={item.id} className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                <div className="flex items-start justify-between gap-3">
                  <p className="font-black text-white">{item.client_name}</p>
                  <span className="badge badge-cyan">{item.status}</span>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-400">{item.scope_summary}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(item.requested_services || []).map((service) => <Pill key={service}>{service}</Pill>)}
                </div>
              </div>
            )) : <p className="text-sm text-slate-500">No intake requests yet.</p>}
          </div>
        </div>

        <div className="glass-tile p-5">
          <p className="text-xl font-black text-white">Handoff packs</p>
          <div className="mt-5 grid gap-3">
            {handoffs.length ? handoffs.map((item) => (
              <details key={item.id} className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                <summary className="cursor-pointer font-black text-white">{item.client_name} · {item.status}</summary>
                <p className="mt-3 text-sm leading-6 text-slate-400">{item.executive_summary}</p>
                <p className="mt-4 text-xs font-black uppercase tracking-[0.18em] text-slate-500">Open items</p>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-400">
                  {item.open_items.map((openItem) => <li key={openItem}>{openItem}</li>)}
                </ul>
                <p className="mt-4 text-xs font-black uppercase tracking-[0.18em] text-slate-500">Email subject</p>
                <p className="mt-2 text-sm text-cyan">{item.client_email_template.subject}</p>
                <p className="mt-3 text-xs leading-6 text-slate-500">{item.safe_wording}</p>
              </details>
            )) : <p className="text-sm text-slate-500">No handoff packs yet.</p>}
          </div>
        </div>
      </section>

      <section className="mt-6 rounded-3xl border border-red-400/20 bg-red-400/10 p-5">
        <p className="font-black text-red-100">Blocked wording guardrail</p>
        <p className="mt-2 text-sm leading-6 text-red-100/75">{status?.safe_boundary || "No private keys, no wallet signing, no exploit automation, no certified audit claim."}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {(status?.blocked_claims || portfolio?.blocked_claims || []).slice(0, 8).map((claim) => <span key={claim} className="badge badge-red">{claim}</span>)}
        </div>
      </section>
    </main>
  );
}
