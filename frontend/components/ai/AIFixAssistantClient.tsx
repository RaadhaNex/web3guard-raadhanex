"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import type { AIFixAssistantStatus, AIFixSuggestion, Finding } from "@/lib/types";
import { SeverityBadge } from "@/components/ui/SeverityBadge";

const sampleFinding: Finding = {
  id: "sample-reentrancy-finding",
  module: "contract",
  severity: "high",
  title: "External call before state update can enable reentrancy",
  description: "The withdraw function sends value before updating internal balance state.",
  affected_line: 12,
  affected_function: "withdraw",
  affected_code: "(bool ok, ) = msg.sender.call{value: amount}(\"\");\nbalances[msg.sender] -= amount;",
  confidence: "high",
  source: "Rule Engine",
  category: "reentrancy",
  rule_id: "W3G-REENTRANCY-001",
  business_impact: "A malicious receiver may repeatedly withdraw funds before state changes are finalized.",
  developer_explanation: "External calls should be made after state changes, or guarded with a reentrancy lock.",
  recommendation: "Apply checks-effects-interactions, update balance before the external call, and add a regression test with a malicious receiver contract.",
  references: [],
  paid_review_recommended: true,
};

const sampleCode = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RiskyVault {
    mapping(address => uint256) public balances;

    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "insufficient");
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");
        balances[msg.sender] -= amount;
    }
}`;

export function AIFixAssistantClient() {
  const [status, setStatus] = useState<AIFixAssistantStatus | null>(null);
  const [findingText, setFindingText] = useState(JSON.stringify(sampleFinding, null, 2));
  const [code, setCode] = useState(sampleCode);
  const [language, setLanguage] = useState("Hinglish");
  const [includeCode, setIncludeCode] = useState(false);
  const [privacyAck, setPrivacyAck] = useState(false);
  const [realOnlyAck, setRealOnlyAck] = useState(true);
  const [loading, setLoading] = useState(false);
  const [suggestion, setSuggestion] = useState<AIFixSuggestion | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<AIFixAssistantStatus>("/ai/fix-assistant/status").then(setStatus).catch(() => setStatus(null));
  }, []);

  const parsedFinding = useMemo(() => {
    try {
      return JSON.parse(findingText) as Finding;
    } catch {
      return null;
    }
  }, [findingText]);

  async function runAssistant() {
    setLoading(true);
    setError(null);
    setSuggestion(null);
    try {
      if (!parsedFinding) throw new Error("Finding JSON is invalid");
      const data = await apiPost<AIFixSuggestion>("/ai/fix-assistant/suggest", {
        finding: parsedFinding,
        code_context: code,
        mode: "safe_patch",
        preferred_language: language,
        include_code: includeCode,
        privacy_acknowledged: privacyAck,
        real_only_acknowledged: realOnlyAck,
      });
      setSuggestion(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI Fix Assistant failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="max-w-4xl">
        <p className="text-sm font-bold uppercase tracking-[0.3em] text-cyan">· Real AI Fix Assistant</p>
        <h1 className="mt-3 text-3xl font-black sm:text-5xl">Safe fix suggestions, not auto-fixes</h1>
        <p className="mt-4 text-slate-400">
          This assistant can generate conservative patch direction, diff/snippet ideas, tests, and validation steps. It never auto-applies production code, never asks for private keys, and uses local fallback if provider keys are missing.
        </p>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-5">
          <div className="card p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-black text-white">AI provider status</p>
                <p className="mt-1 text-sm text-slate-400">Provider mode controls whether real API calls are made.</p>
              </div>
              <span className="badge">{status?.mode || "loading"}</span>
            </div>
            {status && (
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <Info label="Provider" value={`${status.provider} · ${status.model}`} />
                <Info label="Configured" value={String(status.provider_configured)} />
                <Info label="Code send" value={String(status.ai_send_code && status.ai_fix_send_code)} />
                <Info label="Auto apply" value={String(status.auto_apply_allowed)} />
              </div>
            )}
            {status?.blocked_claims?.length ? (
              <div className="mt-4 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4">
                <p className="text-sm font-black text-amber-100">Blocked claims</p>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-amber-100/90">
                  {status.blocked_claims.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            ) : null}
          </div>

          <div className="card p-6">
            <label className="text-sm font-bold text-slate-200">Finding JSON</label>
            <textarea className="textarea mono mt-2 min-h-[360px]" value={findingText} onChange={(e) => setFindingText(e.target.value)} />
            {parsedFinding && (
              <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-slate-300">
                <SeverityBadge severity={parsedFinding.severity} />
                <span>{parsedFinding.title}</span>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-5">
          <div className="card p-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="text-sm font-bold text-slate-200">Language</label>
                <select className="select mt-2" value={language} onChange={(e) => setLanguage(e.target.value)}>
                  <option>English</option>
                  <option>Hindi</option>
                  <option>Hinglish</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-bold text-slate-200">Mode</label>
                <input className="input mt-2" value="safe_patch" readOnly />
              </div>
            </div>

            <div className="mt-5">
              <label className="text-sm font-bold text-slate-200">Optional code context</label>
              <textarea className="textarea mono mt-2 min-h-[260px]" value={code} onChange={(e) => setCode(e.target.value)} />
            </div>

            <label className="mt-5 flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-300">
              <input type="checkbox" className="mt-1" checked={includeCode} onChange={(e) => setIncludeCode(e.target.checked)} />
              <span>Include code context in request. If provider mode is not configured, code still stays local and fallback guidance is returned.</span>
            </label>
            <label className="mt-3 flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-300">
              <input type="checkbox" className="mt-1" checked={privacyAck} onChange={(e) => setPrivacyAck(e.target.checked)} />
              <span>I understand code may be sent to the configured AI provider only if backend env privacy gates also allow it.</span>
            </label>
            <label className="mt-3 flex items-start gap-3 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm text-amber-100">
              <input type="checkbox" className="mt-1" checked={realOnlyAck} onChange={(e) => setRealOnlyAck(e.target.checked)} />
              <span>I acknowledge this is guidance only, not a guaranteed fix or certified audit.</span>
            </label>

            <button className="btn-primary mt-5 w-full" onClick={runAssistant} disabled={loading || !realOnlyAck}>{loading ? "Generating..." : "Generate safe fix suggestion"}</button>
            {error && <p className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}
          </div>

          {suggestion && <SuggestionCard suggestion={suggestion} />}
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-1 break-all text-sm font-black text-white">{value}</p>
    </div>
  );
}

function SuggestionCard({ suggestion }: { suggestion: AIFixSuggestion }) {
  return (
    <div className="card p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-black text-white">Fix suggestion result</p>
          <p className="mt-1 text-xs text-slate-400">{suggestion.provider} · {suggestion.status} · code sent: {String(suggestion.code_was_sent_to_provider)}</p>
        </div>
        <SeverityBadge severity={suggestion.finding_severity} />
      </div>
      <div className="mt-5 space-y-4 text-sm leading-6 text-slate-300">
        <Block title="Summary" text={suggestion.summary} />
        <Block title="Root cause" text={suggestion.root_cause} />
        <Block title="Safe patch strategy" text={suggestion.safe_patch_strategy} />
        {suggestion.fixed_code_snippet && <CodeBlock title="Suggested snippet/pattern" code={suggestion.fixed_code_snippet} />}
        {suggestion.suggested_patch_unified_diff && <CodeBlock title="Suggested unified diff" code={suggestion.suggested_patch_unified_diff} />}
        <List title="Test suggestions" items={suggestion.test_suggestions} />
        <List title="Validation steps" items={suggestion.validation_steps} />
        <List title="Risk notes" items={suggestion.risk_notes} />
        <Block title="Manual review" text={suggestion.manual_review_note} />
        <Block title="Confidence" text={suggestion.confidence_note} />
        <div className="rounded-2xl border border-cyan/20 bg-cyan/10 p-4 text-xs text-cyan-100">
          Auto apply allowed: {String(suggestion.auto_apply_allowed)} · Redaction applied: {String(suggestion.redaction_applied)} · Flags: {suggestion.safety_flags.join(", ") || "none"}
        </div>
      </div>
    </div>
  );
}

function Block({ title, text }: { title: string; text: string }) {
  return <div><p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">{title}</p><p className="mt-1">{text}</p></div>;
}

function CodeBlock({ title, code }: { title: string; code: string }) {
  return <div><p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">{title}</p><pre className="mono mt-2 overflow-auto rounded-2xl border border-white/10 bg-black/40 p-4 text-xs text-slate-200">{code}</pre></div>;
}

function List({ title, items }: { title: string; items: string[] }) {
  return <div><p className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">{title}</p><ul className="mt-2 list-disc space-y-1 pl-5">{items.map((item) => <li key={item}>{item}</li>)}</ul></div>;
}
