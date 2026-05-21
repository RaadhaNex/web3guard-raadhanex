from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scan_contract import scan_solidity
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.solidity_utils import sha12

ENGINE_VERSION = "web3guard-source-evidence-mapper-v1.0"
MAX_FILES = 80
MAX_FILE_CHARS = 220_000
MAX_TOTAL_CHARS = 900_000
MAX_FINDINGS = 160

SENSITIVE_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}
SENSITIVE_EXTENSIONS = {".pem", ".key", ".p12", ".pfx", ".jks"}
CODE_EXTENSIONS = (
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".java", ".rb", ".php",
    ".sol", ".json", ".yaml", ".yml", ".toml", ".env", ".config",
)

SECRET_ASSIGNMENT_RE = re.compile(r"(?i)([A-Z0-9_\-]*(?:KEY|SECRET|TOKEN|PASSWORD|MNEMONIC|SEED|PRIVATE)[A-Z0-9_\-]*)\s*[:=]\s*['\"]?([^'\"\s#]{12,})")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")
ETH_PRIVATE_KEY_RE = re.compile(r"(?i)(private[_-]?key|deployer[_-]?key)\s*[:=]\s*['\"]?(0x)?[a-f0-9]{64}['\"]?")
JWT_RE = re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}")
AWS_ACCESS_KEY_RE = re.compile(r"AKIA[0-9A-Z]{16}")
GENERIC_LONG_TOKEN_RE = re.compile(r"(?i)(sk-[a-z0-9]{20,}|ghp_[a-z0-9_]{20,}|xox[baprs]-[a-z0-9-]{20,})")


@dataclass(frozen=True)
class SourceFile:
    path: str
    content: str
    origin: str = "user_supplied_source_artifact"


def _safe_path(value: Any, fallback: str) -> str:
    raw = str(value or fallback).strip().replace("\\", "/")
    raw = re.sub(r"^/+", "", raw)
    raw = raw.replace("..", "_")
    return raw[:260] or fallback


def _suffix(path: str) -> str:
    lower = path.lower()
    if lower in SENSITIVE_FILENAMES or lower.split("/")[-1] in SENSITIVE_FILENAMES:
        return ".env" if ".env" in lower else lower.split("/")[-1]
    match = re.search(r"(\.[a-z0-9]+)$", lower)
    return match.group(1) if match else ""


def _is_probably_code_file(path: str, content: str) -> bool:
    lower = path.lower()
    if lower.split("/")[-1] in SENSITIVE_FILENAMES or _suffix(path) in SENSITIVE_EXTENSIONS:
        return True
    if lower.endswith(CODE_EXTENSIONS):
        return True
    sample = content[:4000]
    code_markers = ("function ", "const ", "import ", "class ", "pragma solidity", "def ", "package ", "router.", "app.")
    return any(marker in sample for marker in code_markers)


def _line(content: str, line_no: int | None) -> str | None:
    if not line_no:
        return None
    parts = content.splitlines()
    if line_no < 1 or line_no > len(parts):
        return None
    return parts[line_no - 1][:1200]


def _redact(code: str | None) -> str | None:
    if not code:
        return code
    redacted = SECRET_ASSIGNMENT_RE.sub(lambda m: f"{m.group(1)}=<redacted>", code)
    redacted = ETH_PRIVATE_KEY_RE.sub(lambda m: f"{m.group(1)}=<redacted-private-key>", redacted)
    redacted = JWT_RE.sub("<redacted-jwt>", redacted)
    redacted = AWS_ACCESS_KEY_RE.sub("<redacted-aws-access-key>", redacted)
    redacted = GENERIC_LONG_TOKEN_RE.sub("<redacted-token>", redacted)
    return redacted[:1200]


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {ch: value.count(ch) for ch in set(value)}
    return -sum((count / len(value)) * math.log2(count / len(value)) for count in counts.values())


def _finding(
    idx: int,
    *,
    module: str,
    severity: str,
    title: str,
    description: str,
    path: str,
    line_no: int | None,
    code: str | None,
    business: str,
    dev: str,
    fix: str,
    confidence: str = "medium",
    category: str = "source_code",
    rule_id: str,
    references: list[str] | None = None,
) -> Finding:
    return Finding(
        id=f"source-map-{idx:03d}",
        module=module,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        title=title[:180],
        description=description[:3000],
        evidence=description[:3000],
        fix=fix,
        affected_file=path,
        affected_line=line_no,
        affected_column=None,
        end_line=line_no,
        affected_function=None,
        affected_code=_redact(code),
        confidence=confidence,  # type: ignore[arg-type]
        source="Web3Guard Source Evidence Mapper",
        category=category,
        rule_id=rule_id,
        fingerprint=sha12(f"{rule_id}|{path}|{line_no}|{code or ''}"),
        business_impact=business,
        developer_explanation=dev,
        recommendation=fix,
        references=references or ["source-code-evidence", "exact-file-line"],
        paid_review_recommended=severity in {"critical", "high"},
    )


def _add(findings: list[Finding], candidate: Finding) -> None:
    key = (candidate.rule_id, candidate.affected_file, candidate.affected_line, candidate.title)
    existing = {(f.rule_id, f.affected_file, f.affected_line, f.title) for f in findings}
    if key not in existing and len(findings) < MAX_FINDINGS:
        findings.append(candidate)


def _iter_lines(source: SourceFile):
    for number, text in enumerate(source.content.splitlines(), start=1):
        yield number, text


def _extract_from_mapping(data: dict[str, Any], origin: str) -> list[SourceFile]:
    files: list[SourceFile] = []
    for key in ("sources", "files", "source_files", "sourceFiles"):
        value = data.get(key)
        if isinstance(value, dict):
            for path, raw in value.items():
                if isinstance(raw, str):
                    files.append(SourceFile(_safe_path(path, f"artifact/{len(files)+1}.txt"), raw[:MAX_FILE_CHARS], origin))
                elif isinstance(raw, dict):
                    content = raw.get("content") or raw.get("source") or raw.get("body") or raw.get("text")
                    if isinstance(content, str):
                        files.append(SourceFile(_safe_path(raw.get("path") or raw.get("filename") or path, f"artifact/{len(files)+1}.txt"), content[:MAX_FILE_CHARS], origin))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    content = item.get("content") or item.get("source") or item.get("body") or item.get("text")
                    path = item.get("path") or item.get("filename") or item.get("file") or item.get("name")
                    if isinstance(content, str):
                        files.append(SourceFile(_safe_path(path, f"artifact/{len(files)+1}.txt"), content[:MAX_FILE_CHARS], origin))
                elif isinstance(item, str) and len(item) > 20:
                    files.append(SourceFile(f"artifact/{len(files)+1}.txt", item[:MAX_FILE_CHARS], origin))
    return files


def extract_source_files(*raw_inputs: str | None) -> tuple[list[SourceFile], list[dict[str, Any]]]:
    files: list[SourceFile] = []
    status: list[dict[str, Any]] = []
    total_chars = 0
    for input_index, raw in enumerate(raw_inputs, start=1):
        if not raw or not raw.strip():
            continue
        origin = f"expert_artifact_{input_index}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            status.append({"state": "Invalid JSON", "input_index": input_index, "error": f"{exc.msg} at line {exc.lineno}, column {exc.colno}"})
            continue
        candidates: list[SourceFile] = []
        if isinstance(data, dict):
            candidates = _extract_from_mapping(data, origin)
            # Support a single-file shape too.
            content = data.get("content") or data.get("source") or data.get("code")
            if isinstance(content, str):
                candidates.append(SourceFile(_safe_path(data.get("path") or data.get("filename"), f"artifact/{input_index}.txt"), content[:MAX_FILE_CHARS], origin))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    content = item.get("content") or item.get("source") or item.get("body") or item.get("text")
                    path = item.get("path") or item.get("filename") or item.get("file") or item.get("name")
                    if isinstance(content, str):
                        candidates.append(SourceFile(_safe_path(path, f"artifact/{len(candidates)+1}.txt"), content[:MAX_FILE_CHARS], origin))
        accepted = 0
        for candidate in candidates:
            if len(files) >= MAX_FILES or total_chars >= MAX_TOTAL_CHARS:
                break
            if not _is_probably_code_file(candidate.path, candidate.content):
                continue
            files.append(candidate)
            total_chars += len(candidate.content)
            accepted += 1
        status.append({"state": "Parsed", "input_index": input_index, "candidate_files": len(candidates), "accepted_files": accepted})
    return files, status


def _scan_secret_rules(source: SourceFile, findings: list[Finding], start_idx: int) -> int:
    idx = start_idx
    basename = source.path.lower().split("/")[-1]
    suffix = _suffix(source.path)
    if basename in SENSITIVE_FILENAMES or suffix in SENSITIVE_EXTENSIONS:
        _add(findings, _finding(
            idx,
            module="static_analysis",
            severity="high",
            title="Sensitive File Included In Submitted Source Evidence",
            description="A sensitive-looking configuration/key file was included in the source evidence. If this file exists in a public repo or frontend bundle, secrets may be exposed.",
            path=source.path,
            line_no=1,
            code=_line(source.content, 1),
            business="Leaked environment files or private keys can lead to account takeover, stolen funds, API abuse, or cloud billing damage.",
            dev="Secret-bearing files should never be committed, bundled, or uploaded to public client builds.",
            fix="Remove this file from source control, rotate any exposed secrets, add it to .gitignore, and verify it is absent from production/public assets.",
            confidence="high",
            category="secrets",
            rule_id="WG-SRC-SECRET-001",
        ))
        idx += 1
    for line_no, text in _iter_lines(source):
        clean = text.strip()
        if not clean or clean.startswith("//") or clean.startswith("#"):
            continue
        if PRIVATE_KEY_RE.search(clean) or ETH_PRIVATE_KEY_RE.search(clean):
            _add(findings, _finding(
                idx,
                module="static_analysis",
                severity="critical",
                title="Private Key Material Detected",
                description="Private-key-like material appears in source evidence.",
                path=source.path,
                line_no=line_no,
                code=clean,
                business="A leaked deployer/admin/private key can directly compromise funds, admin roles, contracts, cloud infra, or production services.",
                dev="Keys must be kept outside code and deployment artifacts. This finding is based on local/source evidence, not guessing.",
                fix="Immediately rotate/revoke the key, remove it from history, move secrets to a secure vault, and audit all actions performed by the exposed identity.",
                confidence="high",
                category="secrets",
                rule_id="WG-SRC-SECRET-002",
            ))
            idx += 1
            continue
        if JWT_RE.search(clean) or AWS_ACCESS_KEY_RE.search(clean) or GENERIC_LONG_TOKEN_RE.search(clean):
            _add(findings, _finding(
                idx,
                module="static_analysis",
                severity="high",
                title="Hardcoded Token / Credential Pattern",
                description="A token/key-like value appears hardcoded in source evidence.",
                path=source.path,
                line_no=line_no,
                code=clean,
                business="Hardcoded tokens can enable unauthorized API access, repo access, cloud abuse, or backend impersonation.",
                dev="The scanner redacts the raw evidence in output; rotate the actual secret before sharing reports externally.",
                fix="Rotate the token, remove it from source/history, and load it from server-only environment variables or a secret manager.",
                confidence="high",
                category="secrets",
                rule_id="WG-SRC-SECRET-003",
            ))
            idx += 1
        assignment = SECRET_ASSIGNMENT_RE.search(clean)
        if assignment:
            value = assignment.group(2)
            if len(value) >= 20 and _entropy(value) >= 3.2 and "example" not in value.lower() and "placeholder" not in value.lower():
                severity = "critical" if any(term in assignment.group(1).lower() for term in ("private", "mnemonic", "seed", "service_role")) else "high"
                _add(findings, _finding(
                    idx,
                    module="static_analysis",
                    severity=severity,
                    title="Secret-Like Assignment In Source",
                    description=f"A secret-like variable named {assignment.group(1)} appears to contain a real value.",
                    path=source.path,
                    line_no=line_no,
                    code=clean,
                    business="Real credentials inside source can leak through repository history, frontend bundles, logs, or shared reports.",
                    dev="This rule uses variable names, value length, and entropy to identify likely secrets; confirm and rotate if real.",
                    fix="Move the value to a server-side secret store, rotate it, and replace code with a runtime environment lookup.",
                    confidence="medium",
                    category="secrets",
                    rule_id="WG-SRC-SECRET-004",
                ))
                idx += 1
    return idx


def _scan_frontend_rules(source: SourceFile, findings: list[Finding], start_idx: int) -> int:
    idx = start_idx
    lower_path = source.path.lower()
    if not lower_path.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")):
        return idx
    for line_no, text in _iter_lines(source):
        compact = text.strip()
        low = compact.lower()
        if "dangerouslysetinnerhtml" in low:
            _add(findings, _finding(
                idx,
                module="dapp",
                severity="high",
                title="Unsanitized HTML Injection Sink Review",
                description="React dangerouslySetInnerHTML is present. If it receives user-controlled content without sanitization, it can become XSS.",
                path=source.path,
                line_no=line_no,
                code=compact,
                business="XSS on a dApp can alter wallet prompts, steal session tokens, mislead users, or redirect payments/claims.",
                dev="The rule flags an injection sink, not proven exploitability. Review data flow into this line.",
                fix="Sanitize with a reviewed HTML sanitizer, avoid raw HTML where possible, and add tests proving user content cannot reach this sink unsanitized.",
                confidence="medium",
                category="frontend_xss",
                rule_id="WG-SRC-FE-001",
            ))
            idx += 1
        if re.search(r"\b(innerHTML|outerHTML|insertAdjacentHTML)\b", compact) and "sanitize" not in low and "dompurify" not in low:
            _add(findings, _finding(
                idx,
                module="dapp",
                severity="medium",
                title="DOM HTML Assignment Needs Sanitization Proof",
                description="A raw DOM HTML assignment API is used without obvious sanitizer evidence on the same line.",
                path=source.path,
                line_no=line_no,
                code=compact,
                business="DOM injection can compromise wallet UX, user sessions, and trust pages.",
                dev="This is a source-level sink finding. Confirm whether the assigned value can contain user or remote content.",
                fix="Use textContent/safe rendering or sanitize the HTML input before assignment.",
                confidence="medium",
                category="frontend_xss",
                rule_id="WG-SRC-FE-002",
            ))
            idx += 1
        if re.search(r"\b(eval|new Function)\s*\(", compact):
            _add(findings, _finding(
                idx,
                module="dapp",
                severity="high",
                title="Dynamic Code Execution In Frontend",
                description="eval/new Function is present in frontend/source evidence.",
                path=source.path,
                line_no=line_no,
                code=compact,
                business="Dynamic code execution can turn a content injection or dependency compromise into full client-side execution.",
                dev="Avoid runtime string execution in production dApp/frontend code.",
                fix="Replace dynamic evaluation with explicit parsing or a safe interpreter. Block this in lint/CI.",
                confidence="high",
                category="frontend_xss",
                rule_id="WG-SRC-FE-003",
            ))
            idx += 1
        if "target=\"_blank\"" in compact or "target='_blank'" in compact:
            if "noopener" not in low and "noreferrer" not in low:
                _add(findings, _finding(
                    idx,
                    module="dapp",
                    severity="low",
                    title="target=_blank Without noopener/noreferrer",
                    description="A new-tab link is missing rel=noopener/noreferrer protection.",
                    path=source.path,
                    line_no=line_no,
                    code=compact,
                    business="Reverse-tabnabbing can redirect users from trusted pages to phishing or wallet-drainer pages.",
                    dev="This is a small but easy-to-fix frontend hardening issue.",
                    fix="Add rel=\"noopener noreferrer\" to external target=_blank links.",
                    confidence="high",
                    category="frontend_hardening",
                    rule_id="WG-SRC-FE-004",
                ))
                idx += 1
        if re.search(r"localStorage\.(setItem|getItem)|sessionStorage\.(setItem|getItem)", compact) and re.search(r"(?i)token|jwt|secret|private|session", compact):
            _add(findings, _finding(
                idx,
                module="dapp",
                severity="medium",
                title="Sensitive Token Stored In Browser Storage",
                description="Token/session-like data appears to be stored or read from localStorage/sessionStorage.",
                path=source.path,
                line_no=line_no,
                code=compact,
                business="Browser storage tokens are easier to steal after XSS and can extend account takeover impact.",
                dev="Use secure httpOnly cookies or short-lived memory tokens where practical.",
                fix="Move sensitive auth/session material to httpOnly secure cookies or reduce token lifetime and scope.",
                confidence="medium",
                category="auth_storage",
                rule_id="WG-SRC-FE-005",
            ))
            idx += 1
        if "next_public_" in low and re.search(r"(?i)secret|service[_-]?role|private|token|password", compact):
            _add(findings, _finding(
                idx,
                module="dapp",
                severity="critical",
                title="Server Secret Exposed Through NEXT_PUBLIC Variable",
                description="A secret-like variable is prefixed with NEXT_PUBLIC, which exposes it to the browser bundle in Next.js.",
                path=source.path,
                line_no=line_no,
                code=compact,
                business="Publishing service-role or backend secrets in frontend JS can give attackers direct privileged API access.",
                dev="Only non-sensitive public configuration may use NEXT_PUBLIC_. Server secrets must stay server-only.",
                fix="Remove NEXT_PUBLIC_ from secrets, rotate the exposed value, and access it only in server routes/actions.",
                confidence="high",
                category="secrets",
                rule_id="WG-SRC-FE-006",
            ))
            idx += 1
    return idx


def _scan_backend_rules(source: SourceFile, findings: list[Finding], start_idx: int) -> int:
    idx = start_idx
    path = source.path.lower()
    if not path.endswith((".py", ".ts", ".js", ".mjs", ".cjs", ".go", ".java", ".php", ".rb")):
        return idx
    for line_no, text in _iter_lines(source):
        compact = text.strip()
        low = compact.lower()
        if "allow_origins" in low and "*" in compact and "allow_credentials" in source.content[max(0, source.content.find(text) - 300): source.content.find(text) + 500].lower():
            _add(findings, _finding(
                idx,
                module="api",
                severity="high",
                title="Wildcard CORS With Credentials Review",
                description="CORS appears to allow wildcard origins near credentialed requests.",
                path=source.path,
                line_no=line_no,
                code=compact,
                business="Over-permissive CORS can expose authenticated API responses to malicious websites.",
                dev="This rule detects risky CORS configuration evidence; verify runtime config too.",
                fix="Restrict allowed origins to production frontend domains and avoid wildcard origins when credentials are enabled.",
                confidence="medium",
                category="api_cors",
                rule_id="WG-SRC-BE-001",
            ))
            idx += 1
        if re.search(r"verify\s*=\s*False", compact) or "rejectunauthorized: false" in low:
            _add(findings, _finding(
                idx,
                module="api",
                severity="high",
                title="TLS Verification Disabled",
                description="Source evidence disables TLS certificate verification.",
                path=source.path,
                line_no=line_no,
                code=compact,
                business="Disabling TLS verification can allow man-in-the-middle attacks against API/provider calls.",
                dev="This is usually unsafe outside local test code.",
                fix="Remove TLS verification bypasses and configure proper CA trust/certificates.",
                confidence="high",
                category="transport_security",
                rule_id="WG-SRC-BE-002",
            ))
            idx += 1
        if re.search(r"subprocess\.(run|popen|call)|os\.system\s*\(", compact, re.IGNORECASE) and ("shell=true" in low or "os.system" in low):
            _add(findings, _finding(
                idx,
                module="api",
                severity="high",
                title="Shell Command Execution Needs Strict Input Control",
                description="Backend source uses shell execution. If user-controlled input reaches this line, command injection may be possible.",
                path=source.path,
                line_no=line_no,
                code=compact,
                business="Command injection can compromise servers, secrets, customer data, and scanner infrastructure.",
                dev="This is a sink finding; confirm input source and arguments.",
                fix="Avoid shell=True/os.system. Use argument arrays, strict allowlists, sandboxing, timeouts, and no user-controlled shell strings.",
                confidence="medium",
                category="command_injection",
                rule_id="WG-SRC-BE-003",
            ))
            idx += 1
        if re.search(r"pickle\.loads|yaml\.load\s*\(", compact):
            _add(findings, _finding(
                idx,
                module="api",
                severity="high",
                title="Unsafe Deserialization Sink",
                description="Unsafe deserialization API appears in backend source evidence.",
                path=source.path,
                line_no=line_no,
                code=compact,
                business="Unsafe deserialization can lead to remote code execution if attacker-controlled input is processed.",
                dev="Use safe parsers and schemas for untrusted input.",
                fix="Replace pickle.loads/yaml.load with safe formats/parsers such as JSON or yaml.safe_load, and validate schema.",
                confidence="medium",
                category="deserialization",
                rule_id="WG-SRC-BE-004",
            ))
            idx += 1
        if re.search(r"debug\s*=\s*True|app\.run\(.*debug\s*=\s*True", compact):
            _add(findings, _finding(
                idx,
                module="api",
                severity="medium",
                title="Debug Mode Enabled In Source",
                description="Debug mode appears enabled in backend source evidence.",
                path=source.path,
                line_no=line_no,
                code=compact,
                business="Debug mode can expose stack traces, internals, or interactive consoles in production.",
                dev="Confirm this is not active in production runtime.",
                fix="Disable debug mode in production and gate it by environment.",
                confidence="medium",
                category="deployment_hardening",
                rule_id="WG-SRC-BE-005",
            ))
            idx += 1
        if re.search(r"jwt\.decode\s*\(", compact, re.IGNORECASE) and "verify" in low and "false" in low:
            _add(findings, _finding(
                idx,
                module="api",
                severity="high",
                title="JWT Verification Disabled",
                description="JWT decoding appears to disable signature/claim verification.",
                path=source.path,
                line_no=line_no,
                code=compact,
                business="Unverified JWTs can allow forged sessions or role escalation.",
                dev="JWT parsing without signature/issuer/audience/expiry validation is not authentication.",
                fix="Verify signature, issuer, audience, expiry, and algorithm allowlist for every protected route.",
                confidence="high",
                category="auth",
                rule_id="WG-SRC-BE-006",
            ))
            idx += 1
    return idx


def _scan_config_rules(source: SourceFile, findings: list[Finding], start_idx: int) -> int:
    idx = start_idx
    lower = source.path.lower()
    if lower.endswith(("package.json", "next.config.js", "next.config.mjs", "vercel.json", "render.yaml", "render.yml", "dockerfile")) or "config" in lower:
        for line_no, text in _iter_lines(source):
            compact = text.strip()
            low = compact.lower()
            if "content-security-policy" in low and ("unsafe-inline" in low or "unsafe-eval" in low):
                _add(findings, _finding(
                    idx,
                    module="dapp",
                    severity="medium",
                    title="Weak CSP Allows Unsafe Script Behavior",
                    description="Security header config appears to allow unsafe-inline/unsafe-eval.",
                    path=source.path,
                    line_no=line_no,
                    code=compact,
                    business="Weak CSP reduces protection against script injection and dependency compromise.",
                    dev="Some frameworks need nonce/hash-based CSP instead of broad unsafe directives.",
                    fix="Replace unsafe-inline/unsafe-eval with nonces/hashes and strict allowed sources where possible.",
                    confidence="medium",
                    category="security_headers",
                    rule_id="WG-SRC-CFG-001",
                ))
                idx += 1
            if "x-powered-by" in low and ("true" in low or "1" in low):
                _add(findings, _finding(
                    idx,
                    module="website",
                    severity="low",
                    title="Technology Fingerprinting Header Enabled",
                    description="Config appears to expose X-Powered-By or framework fingerprinting.",
                    path=source.path,
                    line_no=line_no,
                    code=compact,
                    business="Fingerprinting makes targeted attacks and automated reconnaissance easier.",
                    dev="This is a hardening issue, not a confirmed vulnerability.",
                    fix="Disable X-Powered-By/framework version headers in production.",
                    confidence="medium",
                    category="deployment_hardening",
                    rule_id="WG-SRC-CFG-002",
                ))
                idx += 1
    return idx


def _scan_solidity_source(source: SourceFile, findings: list[Finding], start_idx: int, project_name: str | None, project_type: str | None) -> int:
    if not source.path.lower().endswith(".sol") and "pragma solidity" not in source.content[:3000].lower():
        return start_idx
    idx = start_idx
    report = scan_solidity(source.content, project_name=project_name, contract_type=project_type)
    for item in report.findings[:80]:
        if len(findings) >= MAX_FINDINGS:
            break
        item.id = f"source-sol-{idx:03d}"
        item.affected_file = source.path
        item.end_line = item.affected_line
        item.source = "Web3Guard Solidity Rule Engine + Source Evidence Mapper"
        item.fingerprint = sha12(f"{item.rule_id}|{source.path}|{item.affected_line}|{item.affected_code or ''}")
        _add(findings, item)
        idx += 1
    return idx


def analyze_source_evidence_artifacts(
    *,
    security_tool_artifacts_json: str | None = None,
    crawler_artifact_json: str | None = None,
    review_context_json: str | None = None,
    project_name: str | None = None,
    project_type: str | None = None,
) -> ScanResponse | None:
    files, parse_status = extract_source_files(security_tool_artifacts_json, crawler_artifact_json, review_context_json)
    if not files:
        if any(raw and raw.strip() for raw in (security_tool_artifacts_json, crawler_artifact_json, review_context_json)):
            return ScanResponse(
                report_id=f"WG-SOURCE-MAP-{uuid4().hex[:12]}",
                generated_at=datetime.now(timezone.utc),
                project_name=project_name,
                module_score=ModuleScore(module="static_analysis", score=98, risk_label="No source files parsed", assessed=False),  # type: ignore[arg-type]
                findings=[],
                severity_breakdown=severity_breakdown([]),
                priority_actions=[],
                input_hash=sha12(json.dumps(parse_status, sort_keys=True)),
                engine_version=ENGINE_VERSION,
                scan_metadata={
                    "state": "No Source Files Parsed",
                    "parse_status": parse_status,
                    "supported_shapes": [
                        '{"files":[{"path":"src/file.ts","content":"..."}]}',
                        '{"sources":{"contracts/Token.sol":{"content":"..."}}}',
                        '[{"filename":"api/routes.ts","source":"..."}]',
                    ],
                    "real_only_note": "No file/path/line findings were generated because no supported source-file shape was supplied.",
                },
            )
        return None

    findings: list[Finding] = []
    idx = 1
    for source in files:
        idx = _scan_secret_rules(source, findings, idx)
        idx = _scan_frontend_rules(source, findings, idx)
        idx = _scan_backend_rules(source, findings, idx)
        idx = _scan_config_rules(source, findings, idx)
        idx = _scan_solidity_source(source, findings, idx, project_name, project_type)
        if len(findings) >= MAX_FINDINGS:
            break

    score = score_findings(findings) if findings else 98
    location_index = [
        {
            "id": item.id,
            "severity": item.severity,
            "title": item.title,
            "module": item.module,
            "rule_id": item.rule_id,
            "path": item.affected_file,
            "line": item.affected_line,
            "column": item.affected_column,
            "code": item.affected_code,
            "fix": item.recommendation,
        }
        for item in findings[:MAX_FINDINGS]
    ]
    return ScanResponse(
        report_id=f"WG-SOURCE-MAP-{uuid4().hex[:12]}",
        generated_at=datetime.now(timezone.utc),
        project_name=project_name,
        module_score=ModuleScore(module="static_analysis", score=score, risk_label=risk_label(score), assessed=bool(findings)),  # type: ignore[arg-type]
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=sha12("|".join(f"{f.path}:{sha12(f.content)}" for f in files)),
        engine_version=ENGINE_VERSION,
        scan_metadata={
            "state": "Assessed" if findings else "Assessed - No Findings",
            "files_parsed": len(files),
            "findings_with_exact_location": len([f for f in findings if f.affected_file and f.affected_line]),
            "parse_status": parse_status,
            "location_index": location_index,
            "file_inventory": [{"path": f.path, "origin": f.origin, "chars": len(f.content)} for f in files[:MAX_FILES]],
            "safety_controls": {
                "executes_code": False,
                "installs_dependencies": False,
                "clones_repos": False,
                "uses_exploit_payloads": False,
                "collects_private_keys": False,
                "redacts_secret_values_in_output": True,
                "real_only": True,
            },
            "real_only_note": "Findings come from user-supplied source files/artifacts and include exact affected_file + affected_line when available. The mapper does not execute code or claim all bugs are found.",
        },
        disclaimer="This is static source evidence mapping, not a certified audit. Exact paths/lines are shown only from supplied evidence and must be manually validated before production decisions.",
    )


def source_evidence_mapper_status() -> dict[str, Any]:
    return {
        "ok": True,
        "engine_version": ENGINE_VERSION,
        "purpose": "Parse user-supplied source artifacts and produce exact file/path/line findings without executing code.",
        "supported_shapes": [
            '{"files":[{"path":"src/file.ts","content":"..."}]}',
            '{"sources":{"contracts/Token.sol":{"content":"..."}}}',
            '[{"filename":"api/routes.ts","source":"..."}]',
        ],
        "safe_boundaries": [
            "No exploit automation",
            "No dependency install",
            "No repo clone",
            "No private-key collection",
            "Secret values are redacted in output",
        ],
    }
