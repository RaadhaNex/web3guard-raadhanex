"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type Method = "well_known" | "dns_txt";

type ScanPolicy = {
  mode: string;
  allowed_methods: string[];
  blocked_actions: string[];
  ownership_required_for: string[];
  consent_text: string;
  private_network_blocking: boolean;
  deep_scan_available: boolean;
  note: string;
};

type Challenge = {
  id: string;
  website_url: string;
  normalized_host: string;
  method: Method;
  token: string;
  expires_at: string;
  dns_txt_name?: string;
  dns_txt_value?: string;
  well_known_url?: string;
  well_known_path: string;
  instructions: string[];
  safety_note: string;
};

type VerifyResult = {
  challenge_id: string;
  status: string;
  verified: boolean;
  checked_at: string;
  evidence: Record<string, unknown>;
  next_steps: string[];
  note: string;
};

export default function OwnershipVerificationPage() {
  const [policy, setPolicy] = useState<ScanPolicy | null>(null);
  const [projectName, setProjectName] = useState("Demo Web3 Launch");
  const [websiteUrl, setWebsiteUrl] = useState("https://example.com");
  const [method, setMethod] = useState<Method>("well_known");
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [verifyResult, setVerifyResult] = useState<VerifyResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<ScanPolicy>("/ownership/policy").then(setPolicy).catch(() => setPolicy(null));
  }, []);

  async function createChallenge() {
    setLoading(true);
    setError(null);
    setVerifyResult(null);
    try {
      const data = await apiPost<Challenge>("/ownership/challenge", {
        project_name: projectName,
        website_url: websiteUrl,
        method,
      });
      setChallenge(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Challenge creation failed");
    } finally {
      setLoading(false);
    }
  }

  async function verifyChallenge() {
    if (!challenge) return;
    setVerifying(true);
    setError(null);
    try {
      const data = await apiPost<VerifyResult>("/ownership/verify", {
        challenge_id: challenge.id,
        website_url: challenge.website_url,
        method: challenge.method,
        token: challenge.token,
      });
      setVerifyResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setVerifying(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">ownership + abuse prevention</p>
      <h1 className="mt-3 text-4xl font-black sm:text-5xl">Prove project ownership before future deep scans.</h1>
      <p className="mt-4 max-w-3xl text-slate-400">
        Web3Guard AI remains passive/checklist/code-submitted by default. This page creates DNS TXT or well-known file verification challenges for future owner-approved workflows.
      </p>

      {policy && (
        <div className="mt-8 grid gap-5 lg:grid-cols-3">
          <div className="card p-5 lg:col-span-1">
            <h2 className="text-xl font-black">Allowed mode</h2>
            <p className="mt-2 text-sm text-slate-300">{policy.mode}</p>
            <p className="mt-4 rounded-2xl border border-cyan/20 bg-cyan/10 p-3 text-xs text-cyan-100">{policy.note}</p>
          </div>
          <div className="card p-5">
            <h2 className="text-xl font-black">Allowed</h2>
            <ul className="mt-3 space-y-2 text-sm text-slate-300">{policy.allowed_methods.map((item) => <li key={item}>✓ {item}</li>)}</ul>
          </div>
          <div className="card p-5">
            <h2 className="text-xl font-black">Blocked</h2>
            <ul className="mt-3 space-y-2 text-sm text-slate-300">{policy.blocked_actions.slice(0, 6).map((item) => <li key={item}>✕ {item}</li>)}</ul>
          </div>
        </div>
      )}

      <div className="mt-10 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card p-6">
          <h2 className="text-2xl font-black">Create verification challenge</h2>
          <div className="mt-5 space-y-4">
            <div>
              <label className="text-sm font-bold text-slate-200">Project name</label>
              <input className="input mt-2" value={projectName} onChange={(event) => setProjectName(event.target.value)} />
            </div>
            <div>
              <label className="text-sm font-bold text-slate-200">Website URL</label>
              <input className="input mt-2" value={websiteUrl} onChange={(event) => setWebsiteUrl(event.target.value)} />
              <p className="mt-2 text-xs text-slate-500">Private/internal IPs, localhost, and unsafe redirects are blocked by backend validation.</p>
            </div>
            <div>
              <label className="text-sm font-bold text-slate-200">Verification method</label>
              <select className="select mt-2" value={method} onChange={(event) => setMethod(event.target.value as Method)}>
                <option value="well_known">Well-known file</option>
                <option value="dns_txt">DNS TXT</option>
              </select>
            </div>
            <button className="btn-primary w-full" disabled={loading} onClick={createChallenge}>{loading ? "Creating..." : "Generate Challenge"}</button>
          </div>
          {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-100">{error}</p>}
        </div>

        <div className="card p-6">
          <h2 className="text-2xl font-black">Challenge instructions</h2>
          {!challenge ? (
            <p className="mt-4 text-sm text-slate-400">Generate a challenge to see DNS/file instructions, token, expiry, and verification steps.</p>
          ) : (
            <div className="mt-5 space-y-5">
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Challenge ID</p>
                <p className="mt-1 font-mono text-sm text-cyan">{challenge.id}</p>
                <p className="mt-3 text-xs uppercase tracking-[0.2em] text-slate-500">Token</p>
                <p className="mt-1 break-all rounded-xl bg-black/30 p-3 font-mono text-xs text-white">{challenge.token}</p>
              </div>
              <ol className="space-y-3 text-sm text-slate-300">
                {challenge.instructions.map((item) => <li key={item} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">{item}</li>)}
              </ol>
              {challenge.method === "well_known" && <p className="text-sm text-slate-300">Fetch URL: <span className="font-mono text-cyan">{challenge.well_known_url}</span></p>}
              {challenge.method === "dns_txt" && <p className="text-sm text-slate-300">TXT name: <span className="font-mono text-cyan">{challenge.dns_txt_name}</span></p>}
              <button className="btn-primary" disabled={verifying} onClick={verifyChallenge}>{verifying ? "Verifying..." : "Verify Now"}</button>
              <p className="text-xs leading-5 text-amber-100">{challenge.safety_note}</p>
            </div>
          )}
        </div>
      </div>

      {verifyResult && (
        <div className={`mt-8 rounded-3xl border p-6 ${verifyResult.verified ? "border-green-400/30 bg-green-500/10" : "border-amber-400/30 bg-amber-400/10"}`}>
          <h2 className="text-2xl font-black">Verification result: {verifyResult.status}</h2>
          <p className="mt-2 text-sm text-slate-300">{verifyResult.note}</p>
          <ul className="mt-4 space-y-2 text-sm text-slate-300">{verifyResult.next_steps.map((step) => <li key={step}>→ {step}</li>)}</ul>
          <pre className="mt-4 overflow-auto rounded-2xl bg-black/40 p-4 text-xs text-slate-200">{JSON.stringify(verifyResult.evidence, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
