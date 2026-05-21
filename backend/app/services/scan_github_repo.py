from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from app.core.config import settings
from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scan_contract import scan_solidity
from app.services.scan_dapp_api import scan_api_backend, scan_dapp_frontend
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.accuracy_upgrade import run_dependency_osv_engine

GITHUB_OWNER_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
EVM_ADDRESS_RE = re.compile(r"0x[a-fA-F0-9]{40}")
PRIVATE_KEY_RE = re.compile(r"(?i)(private[_-]?key|secret[_-]?key|mnemonic|seed[_-]?phrase|wallet[_-]?key)\s*[:=]\s*['\"]?([A-Fa-f0-9]{64}|[a-z]+(?:\s+[a-z]+){11,23})")
OPENAI_KEY_RE = re.compile(r"sk-[A-Za-z0-9_\-]{20,}")
RAZORPAY_SECRET_RE = re.compile(r"(?i)(razorpay|stripe|alchemy|infura|moralis|etherscan|bscscan|polygonscan)[A-Za-z0-9_\-]*\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}")
CORS_WILDCARD_RE = re.compile(r"(?i)(allow_origins\s*=\s*\[?['\"]\*|origin\s*:\s*['\"]\*|Access-Control-Allow-Origin['\"]?\s*[:,]\s*['\"]\*)")
DEBUG_TRUE_RE = re.compile(r"(?i)(debug\s*=\s*true|DEBUG\s*=\s*True|NODE_ENV\s*!=\s*['\"]production|app\.run\([^)]*debug\s*=\s*True)")
RATE_LIMIT_RE = re.compile(r"(?i)(rate.?limit|slowapi|limiter|throttle|express-rate-limit|upstash|redis)")
AUTH_RE = re.compile(r"(?i)(auth|jwt|session|passport|next-auth|supabase\.auth|getServerSession|requireAuth|Depends\(.*auth)")
HARDCODED_RPC_RE = re.compile(r"https?://[A-Za-z0-9.\-]*(alchemy|infura|moralis|quicknode|ankr|rpc)[^'\"\s]+", re.I)
WALLET_FRONTEND_RE = re.compile(r"(?i)(walletconnect|wagmi|rainbowkit|metamask|window\.ethereum|ethers\.|viem|connectWallet|setApprovalForAll|MaxUint256|permit2)")
DANGEROUS_JS_RE = re.compile(r"(?i)(dangerouslySetInnerHTML|eval\(|new Function\(|innerHTML\s*=)")

TEXT_EXTENSIONS = {
    ".sol", ".ts", ".tsx", ".js", ".jsx", ".json", ".py", ".go", ".rs", ".toml", ".yml", ".yaml", ".env", ".example", ".md", ".config",
}
SOLIDITY_EXTENSIONS = {".sol"}
PACKAGE_FILENAMES = {"package.json"}
ENV_RISK_NAMES = {".env", ".env.local", ".env.production", ".env.development", ".env.staging"}
CONFIG_HINT_NAMES = {"hardhat.config.js", "hardhat.config.ts", "foundry.toml", "truffle-config.js", "truffle.js", "next.config.js", "next.config.mjs", "vite.config.ts", "vite.config.js"}
LOCKFILE_NAMES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock", "poetry.lock", "requirements.txt", "Cargo.lock"}
CI_WORKFLOW_RE = re.compile(r"(?i)^\.github/workflows/.*\.(yml|yaml)$")
SECURITY_POLICY_NAMES = {"security.md", "security.txt", "security-policy.md"}
TEST_PATH_RE = re.compile(r"(?i)(^|/)(test|tests|spec|__tests__)/|(_test\.|\.test\.|\.spec\.)")
CODEOWNERS_RE = re.compile(r"(?i)(^|/)(CODEOWNERS)$")
LICENSE_RE = re.compile(r"(?i)(^|/)(LICENSE|LICENSE\.md|COPYING)$")
README_RE = re.compile(r"(?i)(^|/)(README|README\.md)$")
GITIGNORE_RE = re.compile(r"(?i)(^|/)\.gitignore$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_report_id() -> str:
    return f"W3G-GITHUB-{_now().strftime('%Y%m%d%H%M%S')}"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_github_repo_url(repo_url: str) -> dict[str, str | None]:
    parsed = urlparse(repo_url.strip())
    if parsed.scheme not in {"https", "http"}:
        raise ValueError("Only http/https GitHub repository URLs are allowed.")
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError("Only github.com repository URLs are supported.")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("GitHub URL must be in the form https://github.com/owner/repo")
    owner = parts[0]
    repo = parts[1].removesuffix(".git")
    if not GITHUB_OWNER_REPO_RE.match(owner) or not GITHUB_OWNER_REPO_RE.match(repo):
        raise ValueError("GitHub owner/repo contains unsupported characters.")
    branch = None
    if len(parts) >= 4 and parts[2] == "tree":
        branch = parts[3]
    return {"owner": owner, "repo": repo, "branch_from_url": branch}


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Web3GuardAI-RAADHANEX-RepoScanner/11.0 (read-only-public-repo-scan)",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_api_token:
        headers["Authorization"] = f"Bearer {settings.github_api_token}"
    return headers


async def _get_json(client: httpx.AsyncClient, url: str) -> Any:
    response = await client.get(url, headers=_headers())
    if response.status_code == 404:
        raise ValueError("GitHub repository/branch was not found or is not public.")
    if response.status_code == 403:
        raise ValueError("GitHub API rate limit or access policy blocked this scan. Add a GitHub token or retry later.")
    response.raise_for_status()
    return response.json()


async def _get_text(client: httpx.AsyncClient, url: str, *, max_bytes: int) -> str | None:
    response = await client.get(url, headers={"User-Agent": _headers()["User-Agent"]}, follow_redirects=True)
    if response.status_code != 200:
        return None
    content = response.content[: max_bytes + 1]
    if len(content) > max_bytes:
        content = content[:max_bytes]
    try:
        return content.decode("utf-8", errors="replace")
    except Exception:
        return None


def _raw_url(owner: str, repo: str, branch: str, path: str) -> str:
    safe_branch = quote(branch, safe="")
    safe_path = "/".join(quote(part, safe="") for part in path.split("/"))
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{safe_branch}/{safe_path}"


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _ext(path: str) -> str:
    name = _basename(path)
    if name.startswith(".env"):
        return ".env"
    if "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1].lower()


def _is_text_candidate(path: str) -> bool:
    name = _basename(path)
    if name in PACKAGE_FILENAMES or name in CONFIG_HINT_NAMES or name.startswith(".env"):
        return True
    return _ext(path) in TEXT_EXTENSIONS


def _finding(
    *,
    idx: int,
    severity: str,
    title: str,
    description: str,
    category: str,
    rule_id: str,
    confidence: str,
    source: str,
    business_impact: str,
    developer_explanation: str,
    recommendation: str,
    path: str | None = None,
    line: int | None = None,
    snippet: str | None = None,
    paid: bool = False,
    refs: list[str] | None = None,
) -> Finding:
    fingerprint = _hash(f"github|{rule_id}|{path or ''}|{line or ''}|{title}")[:16]
    return Finding(
        id=f"github-{idx:03d}-{fingerprint[:6]}",
        module="github",
        severity=severity,  # type: ignore[arg-type]
        title=title,
        description=description,
        evidence=snippet or description,
        fix=recommendation,
        affected_file=path,
        affected_line=line,
        affected_function=None,
        affected_code=snippet,
        confidence=confidence,  # type: ignore[arg-type]
        source=source,
        category=category,
        rule_id=rule_id,
        fingerprint=fingerprint,
        business_impact=business_impact,
        developer_explanation=developer_explanation,
        recommendation=recommendation,
        references=refs or [],
        paid_review_recommended=paid,
    )


def _line_for_pattern(text: str, pattern: re.Pattern[str]) -> tuple[int | None, str | None]:
    match = pattern.search(text)
    if not match:
        return None, None
    before = text[: match.start()]
    line = before.count("\n") + 1
    line_text = text.splitlines()[line - 1] if line - 1 < len(text.splitlines()) else match.group(0)
    return line, line_text[:240]


def _file_path_findings(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    idx = 1
    for path in paths:
        name = _basename(path)
        lower = name.lower()
        if lower in ENV_RISK_NAMES:
            findings.append(_finding(
                idx=idx,
                severity="critical",
                title="Sensitive Environment File Committed",
                description=f"Repository tree contains {path}. Even if values are empty, production projects should not commit real .env files.",
                category="repo_secret_hygiene",
                rule_id="GITHUB-PATH-ENV-FILE",
                confidence="high",
                source="GitHub Repository Tree Scanner",
                business_impact="Committed env files can expose private keys, API keys, webhook secrets, or admin tokens and can destroy launch trust.",
                developer_explanation="The scanner only saw the path name from the public repository tree; it did not need to execute or clone the repo.",
                recommendation="Remove committed env files, rotate any exposed secrets, add .env* to .gitignore except safe .env.example, and review git history.",
                path=path,
                paid=True,
                refs=["secret management", "git hygiene"],
            ))
            idx += 1
        if re.search(r"(?i)(private[_-]?key|seed|mnemonic|wallet[_-]?key|service[_-]?account|credentials\.json|firebase-adminsdk)", path):
            findings.append(_finding(
                idx=idx,
                severity="critical",
                title="Secret-Like File Path Found",
                description=f"Repository tree contains a path that looks sensitive: {path}",
                category="repo_secret_hygiene",
                rule_id="GITHUB-PATH-SECRET-LIKE",
                confidence="medium",
                source="GitHub Repository Tree Scanner",
                business_impact="Secret-like files in repos can compromise treasury/admin wallets, APIs, Firebase, payments, or deployment infrastructure.",
                developer_explanation="This is path-based evidence only. It must be manually verified, but it should be treated urgently.",
                recommendation="Verify the file is not sensitive, remove it if needed, rotate credentials, and purge from git history if real secrets were committed.",
                path=path,
                paid=True,
                refs=["secret management"],
            ))
            idx += 1
    return findings


def _content_findings(path: str, text: str, start_idx: int) -> list[Finding]:
    findings: list[Finding] = []
    checks: list[tuple[re.Pattern[str], str, str, str, str, str, str, bool, list[str]]] = [
        (PRIVATE_KEY_RE, "critical", "Hardcoded Private Key / Seed Phrase Pattern", "A secret-looking private key or mnemonic pattern appears in a public repo file.", "secrets", "GITHUB-CONTENT-PRIVATE-KEY", "Remove the secret, rotate affected wallet/API credentials, and scrub git history before launch.", True, ["private key leak"]),
        (OPENAI_KEY_RE, "high", "Hardcoded AI/API Key Pattern", "An API key-like value appears in repository content.", "secrets", "GITHUB-CONTENT-API-KEY", "Move API keys to backend-only env/secret manager, rotate exposed keys, and avoid public client bundles.", True, ["API key exposure"]),
        (RAZORPAY_SECRET_RE, "high", "Hardcoded Provider Secret Pattern", "Payment/RPC/explorer provider secret-like value appears in code.", "secrets", "GITHUB-CONTENT-PROVIDER-SECRET", "Move provider secrets to env/secret manager and rotate if this repo is public.", True, ["provider key exposure"]),
        (CORS_WILDCARD_RE, "high", "Wildcard CORS Pattern in Repo", "Open CORS appears in backend/config code.", "cors", "GITHUB-CONTENT-WILDCARD-CORS", "Restrict CORS to trusted frontend origins and avoid wildcard credentials.", True, ["CORS"]),
        (DEBUG_TRUE_RE, "medium", "Debug Mode Pattern in Repo", "Debug/development mode appears in application code/config.", "debug", "GITHUB-CONTENT-DEBUG", "Disable debug/verbose errors in production and sanitize error responses.", False, ["production hardening"]),
        (HARDCODED_RPC_RE, "medium", "Hardcoded RPC Provider URL", "RPC provider URL appears in repo content and may include a public key or quota-limited endpoint.", "rpc", "GITHUB-CONTENT-RPC", "Use restricted public keys or backend proxy with domain/quota controls. Keep private provider keys backend-only.", False, ["RPC key exposure"]),
        (DANGEROUS_JS_RE, "high", "Dangerous Frontend Rendering Pattern", "Unsafe JS rendering/eval pattern appears in frontend code.", "xss", "GITHUB-CONTENT-DANGEROUS-JS", "Remove eval/innerHTML patterns or sanitize carefully before wallet/mint flows.", True, ["XSS", "frontend security"]),
        (WALLET_FRONTEND_RE, "info", "Web3 Wallet/Transaction Code Detected", "Repository contains wallet/transaction related frontend code that should be reviewed before launch.", "wallet_frontend", "GITHUB-CONTENT-WALLET-HINT", "Run dApp and wallet flow review with source context; verify chain, spender, approval, and transaction preview UX.", False, ["wallet UX"]),
    ]
    idx = start_idx
    for pattern, severity, title, desc, category, rule_id, rec, paid, refs in checks:
        line, snippet = _line_for_pattern(text, pattern)
        if line:
            findings.append(_finding(
                idx=idx,
                severity=severity,
                title=title,
                description=desc,
                category=category,
                rule_id=rule_id,
                confidence="high" if severity in {"critical", "high"} else "medium",
                source="GitHub File Content Hint Engine",
                business_impact="Repository-level issues can expose funds, admin powers, payment state, dApp users, or launch trust.",
                developer_explanation=f"Pattern detected in {path} near line {line}. This is static read-only analysis, not code execution.",
                recommendation=rec,
                path=path,
                line=line,
                snippet=f"{path}:{line} â€” {snippet}",
                paid=paid,
                refs=refs,
            ))
            idx += 1
    if path.endswith("package.json"):
        try:
            pkg = json.loads(text)
        except json.JSONDecodeError:
            pkg = {}
        deps: dict[str, str] = {}
        for key in ("dependencies", "devDependencies"):
            if isinstance(pkg.get(key), dict):
                deps.update(pkg[key])
        risky = []
        for dep in ("web3modal", "@walletconnect/client", "@walletconnect/web3-provider"):
            version = deps.get(dep)
            if version and re.search(r"(?:\^|~)?1\.", str(version)):
                risky.append(f"{dep}@{version}")
        for dep in ("bip39", "hdkey", "ethereumjs-wallet"):
            version = deps.get(dep)
            if version:
                risky.append(f"{dep}@{version}")
        if risky:
            findings.append(_finding(
                idx=idx,
                severity="medium",
                title="package.json Dependency Review Needed",
                description="Wallet/key-management related or older Web3 dependencies were found.",
                category="dependencies",
                rule_id="GITHUB-PACKAGE-DEPENDENCY-REVIEW",
                confidence="medium",
                source="GitHub package.json Hint Engine",
                business_impact="Risky/older dependencies can impact wallet connection, bundle trust, and signing UX.",
                developer_explanation=f"Detected dependency hints: {', '.join(risky)}",
                recommendation="Review package versions, remove client-side seed/key libraries unless absolutely necessary, and run npm audit/manual dependency review.",
                path=path,
                paid=False,
                refs=["dependency risk"],
            ))
    return findings


def _repo_structure_summary(paths: list[str]) -> dict[str, Any]:
    solidity = [p for p in paths if p.endswith(".sol")]
    package_json = [p for p in paths if _basename(p) == "package.json"]
    lockfiles = [p for p in paths if _basename(p) in LOCKFILE_NAMES]
    ci_workflows = [p for p in paths if CI_WORKFLOW_RE.search(p)]
    security_policies = [p for p in paths if _basename(p).lower() in SECURITY_POLICY_NAMES or p.lower().endswith("/.well-known/security.txt")]
    codeowners = [p for p in paths if CODEOWNERS_RE.search(p)]
    licenses = [p for p in paths if LICENSE_RE.search(p)]
    readmes = [p for p in paths if README_RE.search(p)]
    gitignore = [p for p in paths if GITIGNORE_RE.search(p)]
    tests = [p for p in paths if TEST_PATH_RE.search(p)]
    env_like = [p for p in paths if _basename(p).lower() in ENV_RISK_NAMES or _basename(p).lower().startswith(".env.")]
    configs = [p for p in paths if _basename(p) in CONFIG_HINT_NAMES]
    api_like = [p for p in paths if re.search(r"(?i)(^|/)(api|backend|server|routes|controllers|app|main)\b", p) or _basename(p) in {"server.js", "server.ts", "main.py", "app.py"}]
    frontend_like = [p for p in paths if re.search(r"(?i)(^|/)(pages|app|src|components|frontend|web)\b", p) and _ext(p) in {".ts", ".tsx", ".js", ".jsx"}]
    deploy_like = [p for p in paths if re.search(r"(?i)(deploy|migration|script)", p)]
    return {
        "total_files_seen": len(paths),
        "solidity_files": solidity[:50],
        "solidity_count": len(solidity),
        "package_json_files": package_json[:20],
        "package_json_count": len(package_json),
        "lockfiles": lockfiles[:30],
        "lockfile_count": len(lockfiles),
        "ci_workflows": ci_workflows[:30],
        "ci_workflow_count": len(ci_workflows),
        "security_policy_files": security_policies[:20],
        "security_policy_count": len(security_policies),
        "codeowners_files": codeowners[:20],
        "codeowners_count": len(codeowners),
        "license_files": licenses[:20],
        "license_count": len(licenses),
        "readme_files": readmes[:20],
        "readme_count": len(readmes),
        "gitignore_files": gitignore[:20],
        "gitignore_count": len(gitignore),
        "test_files": tests[:50],
        "test_file_count": len(tests),
        "env_like_files": env_like[:20],
        "env_like_count": len(env_like),
        "config_files": configs[:30],
        "config_count": len(configs),
        "api_like_files": api_like[:50],
        "api_like_count": len(api_like),
        "frontend_like_files": frontend_like[:50],
        "frontend_like_count": len(frontend_like),
        "deployment_script_hints": deploy_like[:50],
        "deployment_script_count": len(deploy_like),
    }


def _package_manifest_summary(path: str, text: str) -> dict[str, Any] | None:
    if _basename(path) != "package.json":
        return None
    try:
        pkg = json.loads(text)
    except json.JSONDecodeError:
        return {"path": path, "valid_json": False, "dependency_count": 0, "script_names": [], "security_relevant_dependencies": []}
    deps: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        value = pkg.get(key)
        if isinstance(value, dict):
            deps.update({str(name): str(version) for name, version in value.items()})
    security_relevant = []
    for name, version in sorted(deps.items()):
        if re.search(r"(?i)(wagmi|viem|ethers|web3|wallet|rainbowkit|solana|hardhat|foundry|slither|semgrep|openzeppelin|supabase|jsonwebtoken|next-auth|express|fastify|cors|helmet)", name):
            security_relevant.append({"name": name, "version": version})
    scripts = pkg.get("scripts") if isinstance(pkg.get("scripts"), dict) else {}
    return {
        "path": path,
        "valid_json": True,
        "dependency_count": len(deps),
        "script_names": sorted(str(k) for k in scripts.keys())[:40],
        "security_relevant_dependencies": security_relevant[:80],
        "has_audit_script": any("audit" in str(k).lower() or "audit" in str(v).lower() for k, v in scripts.items()),
        "has_test_script": any(str(k).lower() in {"test", "test:unit", "test:ci"} or "test" in str(v).lower() for k, v in scripts.items()),
    }


def _repo_readiness_findings(summary: dict[str, Any], start_idx: int) -> list[Finding]:
    findings: list[Finding] = []
    idx = start_idx
    has_code = bool(summary.get("frontend_like_count") or summary.get("api_like_count") or summary.get("solidity_count"))
    if has_code and not summary.get("ci_workflow_count"):
        findings.append(_finding(
            idx=idx, severity="medium", title="CI Security Workflow Missing",
            description="No GitHub Actions workflow was found in the scanned branch.",
            category="repo_readiness", rule_id="GITHUB-READINESS-CI-MISSING", confidence="medium",
            source="GitHub Repository Readiness Analyzer",
            business_impact="Without CI, obvious lint/test/security checks may be missed before launch or before a contest/audit.",
            developer_explanation="This is structure-level evidence from the public repository tree only.",
            recommendation="Add a GitHub Actions workflow that runs typecheck/tests, dependency review, secret scanning, and optional Web3Guard static analysis.",
            refs=["CI security"],
        )); idx += 1
    if has_code and not summary.get("security_policy_count"):
        findings.append(_finding(
            idx=idx, severity="low", title="Security Policy Missing",
            description="No SECURITY.md or security.txt-style disclosure policy was found.",
            category="repo_readiness", rule_id="GITHUB-READINESS-SECURITY-POLICY-MISSING", confidence="medium",
            source="GitHub Repository Readiness Analyzer",
            business_impact="Researchers and users may not know where to report security issues safely.",
            developer_explanation="The scanner checked repository paths only; it did not verify external policy pages.",
            recommendation="Add SECURITY.md and publish security.txt/disclosure contact before public launch or bug bounty readiness.",
            refs=["responsible disclosure"],
        )); idx += 1
    if summary.get("package_json_count") and not summary.get("lockfile_count"):
        findings.append(_finding(
            idx=idx, severity="medium", title="Dependency Lockfile Missing",
            description="package.json exists, but no common lockfile was found in the scanned branch.",
            category="dependencies", rule_id="GITHUB-READINESS-LOCKFILE-MISSING", confidence="medium",
            source="GitHub Repository Readiness Analyzer",
            business_impact="Unpinned dependency resolution can change build behavior and complicate incident response.",
            developer_explanation="This is not npm audit output; it is a repository structure readiness check.",
            recommendation="Commit the correct lockfile for your package manager and run dependency review in CI.",
            refs=["dependency reproducibility"],
        )); idx += 1
    if (summary.get("solidity_count") or summary.get("config_count")) and not summary.get("test_file_count"):
        findings.append(_finding(
            idx=idx, severity="medium", title="Test Evidence Missing",
            description="Solidity/config files were found, but no test/spec directory or test file pattern was detected.",
            category="test_readiness", rule_id="GITHUB-READINESS-TESTS-MISSING", confidence="medium",
            source="GitHub Repository Readiness Analyzer",
            business_impact="Auditors and contest participants expect reproducible tests, edge-case coverage, and regression evidence.",
            developer_explanation="This is a path-based evidence gap, not a claim that no tests exist elsewhere.",
            recommendation="Add Foundry/Hardhat tests, include invariant/fuzz starters where relevant, and document how to run them.",
            refs=["test readiness", "Foundry", "Hardhat"],
        )); idx += 1
    if has_code and not summary.get("codeowners_count"):
        findings.append(_finding(
            idx=idx, severity="info", title="CODEOWNERS Not Found",
            description="No CODEOWNERS file was found in the scanned branch.",
            category="repo_governance", rule_id="GITHUB-READINESS-CODEOWNERS-MISSING", confidence="medium",
            source="GitHub Repository Readiness Analyzer",
            business_impact="Sensitive changes may miss required reviewer routing in team repositories.",
            developer_explanation="This is repository governance evidence only.",
            recommendation="Add CODEOWNERS for contracts, backend, payment, deployment, and admin/security-critical paths.",
            refs=["review controls"],
        )); idx += 1
    if has_code and not summary.get("license_count"):
        findings.append(_finding(
            idx=idx, severity="info", title="License File Not Found",
            description="No common LICENSE/COPYING file was found.",
            category="repo_governance", rule_id="GITHUB-READINESS-LICENSE-MISSING", confidence="low",
            source="GitHub Repository Readiness Analyzer",
            business_impact="Public projects may create legal/compliance ambiguity for users and contributors.",
            developer_explanation="This is a public repository hygiene signal, not a security vulnerability.",
            recommendation="Add the correct license or keep the repository private until legal posture is clear.",
            refs=["open source governance"],
        )); idx += 1
    if has_code and not summary.get("readme_count"):
        findings.append(_finding(
            idx=idx, severity="info", title="README Not Found",
            description="No README was found in the scanned branch.",
            category="repo_governance", rule_id="GITHUB-READINESS-README-MISSING", confidence="medium",
            source="GitHub Repository Readiness Analyzer",
            business_impact="Auditors, bounty researchers, and builders need architecture/setup context before review.",
            developer_explanation="This is repository documentation evidence only.",
            recommendation="Add setup, architecture, threat model, env variable descriptions, and test commands to README.",
            refs=["documentation readiness"],
        )); idx += 1
    if has_code and not summary.get("gitignore_count"):
        findings.append(_finding(
            idx=idx, severity="low", title=".gitignore Not Found",
            description="No .gitignore file was found in the scanned branch.",
            category="repo_secret_hygiene", rule_id="GITHUB-READINESS-GITIGNORE-MISSING", confidence="medium",
            source="GitHub Repository Readiness Analyzer",
            business_impact="Build artifacts, env files, caches, or local secrets are more likely to be committed accidentally.",
            developer_explanation="This is a repository hygiene check from the public tree.",
            recommendation="Add .gitignore entries for env files, build output, caches, node_modules, virtualenvs, and local data stores.",
            refs=["secret hygiene"],
        )); idx += 1
    return findings


async def scan_github_repository(repo_url: str, *, project_name: str | None = None, branch: str | None = None) -> ScanResponse:
    parsed = parse_github_repo_url(repo_url)
    owner = str(parsed["owner"])
    repo = str(parsed["repo"])
    requested_branch = branch or parsed.get("branch_from_url")
    api_base = settings.github_api_base.rstrip("/")

    timeout = httpx.Timeout(settings.github_scan_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        repo_meta = await _get_json(client, f"{api_base}/repos/{owner}/{repo}")
        default_branch = repo_meta.get("default_branch") or "main"
        effective_branch = requested_branch or default_branch
        tree_url = f"{api_base}/repos/{owner}/{repo}/git/trees/{quote(effective_branch, safe='')}?recursive=1"
        tree_payload = await _get_json(client, tree_url)
        tree = tree_payload.get("tree", []) if isinstance(tree_payload, dict) else []
        blob_entries = [item for item in tree if item.get("type") == "blob" and item.get("path")]
        visible_paths = [str(item["path"]) for item in blob_entries]
        limited_paths = visible_paths[: settings.max_github_files]
        findings = _file_path_findings(limited_paths)
        idx = len(findings) + 1

        summary = _repo_structure_summary(limited_paths)
        fetched_files: list[dict[str, Any]] = []
        linked_reports: list[dict[str, Any]] = []
        dependency_manifests: list[dict[str, Any]] = []
        total_bytes = 0

        priority_paths: list[str] = []
        priority_paths.extend(summary["env_like_files"][:10])
        priority_paths.extend(summary["package_json_files"][: settings.max_github_package_files])
        priority_paths.extend(summary["config_files"][:10])
        priority_paths.extend(summary["api_like_files"][: settings.max_github_api_files])
        priority_paths.extend(summary["frontend_like_files"][: settings.max_github_frontend_files])
        priority_paths.extend(summary["deployment_script_hints"][:10])
        priority_paths.extend(summary["solidity_files"][: settings.max_github_solidity_files])
        # Keep order but deduplicate.
        seen: set[str] = set()
        fetch_paths = []
        for path in priority_paths:
            if path in seen or not _is_text_candidate(path):
                continue
            entry = next((item for item in blob_entries if item.get("path") == path), {})
            size = int(entry.get("size") or 0)
            if size > settings.max_github_file_bytes:
                continue
            if total_bytes + size > settings.max_github_total_bytes:
                break
            seen.add(path)
            fetch_paths.append(path)
            total_bytes += max(size, 0)

        for path in fetch_paths:
            entry = next((item for item in blob_entries if item.get("path") == path), {})
            size = int(entry.get("size") or 0)
            raw = await _get_text(client, _raw_url(owner, repo, effective_branch, path), max_bytes=settings.max_github_file_bytes)
            if raw is None:
                fetched_files.append({"path": path, "size": size, "fetched": False, "reason": "raw fetch failed"})
                continue
            fetched_files.append({"path": path, "size": size or len(raw.encode("utf-8", errors="ignore")), "fetched": True})
            manifest_summary = _package_manifest_summary(path, raw)
            if manifest_summary:
                dependency_manifests.append(manifest_summary)
            findings.extend(_content_findings(path, raw, idx))
            idx = len(findings) + 1
            if path.endswith(".sol"):
                try:
                    contract_report = scan_solidity(raw, project_name or repo, "GitHub Solidity")
                    linked_reports.append({
                        "path": path,
                        "module": "contract",
                        "score": contract_report.module_score.score,
                        "risk_label": contract_report.module_score.risk_label,
                        "findings_count": len(contract_report.findings),
                        "critical_high_count": sum(1 for f in contract_report.findings if f.severity in {"critical", "high"}),
                        "report_id": contract_report.report_id,
                    })
                    for finding in contract_report.findings[: settings.max_github_contract_findings_per_file]:
                        data = finding.model_copy(update={
                            "id": f"github-contract-{idx:03d}-{_hash(path + finding.id)[:6]}",
                            "source": f"GitHub Solidity Rule Engine ({path})",
                            "affected_file": path,
                            "evidence": f"{path}:{finding.affected_line or '?'} — {finding.affected_code or finding.title}",
                            "fix": finding.recommendation,
                            "affected_code": f"{path}:{finding.affected_line or '?'} — {finding.affected_code or finding.title}",
                        })
                        findings.append(data)
                        idx += 1
                except Exception as exc:  # Keep repo scanner usable if one Solidity file cannot parse.
                    findings.append(_finding(
                        idx=idx,
                        severity="info",
                        title="Solidity File Could Not Be Fully Scanned",
                        description=f"The repo scanner fetched {path}, but the contract rule engine could not process it cleanly.",
                        category="contract_parse",
                        rule_id="GITHUB-SOLIDITY-SCAN-ERROR",
                        confidence="low",
                        source="GitHub Repo Scanner",
                        business_impact="One source file may need manual review before a full launch-readiness report.",
                        developer_explanation=str(exc)[:240],
                        recommendation="Run a dedicated contract scan with flattened/complete Solidity source or enable Slither/Aderyn in later phases.",
                        path=path,
                    ))
                    idx += 1

        osv_dependency_engine = await run_dependency_osv_engine(manifests=dependency_manifests)
        if isinstance(osv_dependency_engine, dict):
            osv_payload = osv_dependency_engine.get("osv", {}) if isinstance(osv_dependency_engine.get("osv"), dict) else {}
            vulnerabilities = osv_payload.get("vulnerabilities", []) if isinstance(osv_payload, dict) else []
            iterable_vulns = vulnerabilities[:20] if isinstance(vulnerabilities, list) else []
            for vuln in iterable_vulns:
                if not isinstance(vuln, dict):
                    continue
                severity = "high"
                raw_severity = str(vuln.get("severity") or vuln.get("database_specific") or "").lower()
                if "critical" in raw_severity:
                    severity = "critical"
                package = str(vuln.get("package") or "unknown-package")
                version = str(vuln.get("version") or "unknown-version")
                advisory = str(vuln.get("id") or "OSV advisory")
                manifest = str(vuln.get("manifest") or "package.json")
                findings.append(_finding(
                    idx=idx,
                    severity=severity,
                    title=f"OSV Vulnerability Matched: {package}@{version}",
                    description=f"OSV matched dependency {package}@{version} to advisory {advisory}: {str(vuln.get('summary') or 'No summary supplied by OSV')[:500]}",
                    category="dependency_cve",
                    rule_id=f"GITHUB-OSV-{advisory}",
                    confidence="high",
                    source="OSV.dev Real Dependency Advisory",
                    business_impact="Known vulnerable dependencies can expose frontend, API, wallet, build, or deployment surfaces depending on package usage.",
                    developer_explanation=str(vuln.get("proof") or f"OSV returned {advisory} for {package}@{version}"),
                    recommendation="Upgrade to a patched version, review advisory impact, regenerate lockfiles, run tests, and redeploy after verifying no vulnerable transitive version remains.",
                    path=manifest,
                    line=None,
                    snippet=str(vuln.get("proof") or advisory),
                    paid=severity in {"critical", "high"},
                    refs=[advisory, "OSV.dev"],
                ))
                idx += 1
        else:
            osv_dependency_engine = {"state": "Not Assessed", "reason": "OSV dependency engine did not return a structured result."}

        package_texts = []
        api_texts = []
        frontend_texts = []
        for path in fetch_paths:
            # We do not keep full file bodies in metadata; fetch again avoided by only using pattern summaries above.
            if _basename(path) == "package.json":
                package_texts.append(path)
            if path in summary["api_like_files"]:
                api_texts.append(path)
            if path in summary["frontend_like_files"]:
                frontend_texts.append(path)

    # Add structure-level findings after fetch completes.
    if summary["solidity_count"] == 0:
        findings.append(_finding(
            idx=len(findings) + 1,
            severity="info",
            title="No Solidity Files Detected in Repository Tree",
            description="The public repository tree did not contain .sol files in the scanned branch.",
            category="repo_structure",
            rule_id="GITHUB-STRUCTURE-NO-SOLIDITY",
            confidence="medium",
            source="GitHub Repository Tree Scanner",
            business_impact="If smart contracts live elsewhere, this repo scan cannot assess contract launch risk.",
            developer_explanation="Provide the correct repo/branch or paste contract code for a real contract score.",
            recommendation="Add verified contract source or the correct contract repo for contract-level review.",
        ))
    if summary["package_json_count"] and summary["frontend_like_count"]:
        findings.append(_finding(
            idx=len(findings) + 1,
            severity="info",
            title="Frontend Application Surface Detected",
            description="The repository appears to contain frontend application files and package metadata.",
            category="repo_structure",
            rule_id="GITHUB-STRUCTURE-FRONTEND",
            confidence="medium",
            source="GitHub Repository Tree Scanner",
            business_impact="Frontend wallet flow, transaction preview, chain checks, and dependency risk should be reviewed before launch.",
            developer_explanation="This is a structure-level hint, not a vulnerability by itself.",
            recommendation="Run the dApp scanner with full frontend source and package.json context, then complete wallet-flow checklist.",
        ))
    if summary["api_like_count"]:
        findings.append(_finding(
            idx=len(findings) + 1,
            severity="info",
            title="Backend/API Surface Detected",
            description="The repository appears to contain backend/API-like files.",
            category="repo_structure",
            rule_id="GITHUB-STRUCTURE-API",
            confidence="medium",
            source="GitHub Repository Tree Scanner",
            business_impact="Backend endpoints may need auth, rate limit, webhook signature, and CORS review.",
            developer_explanation="This is a structure-level hint, not an authenticated API test.",
            recommendation="Run the API scanner with API base URL and source snippets for deeper readiness checks.",
        ))

    findings.extend(_repo_readiness_findings(summary, len(findings) + 1))

    score = score_findings(findings)
    metadata = {
        "version": "1.0",
        "mode": "read_only_public_github_api_scan",
        "repo": {"owner": owner, "name": repo, "url": f"https://github.com/{owner}/{repo}", "default_branch": default_branch, "scanned_branch": effective_branch},
        "repo_metadata": {
            "private": bool(repo_meta.get("private")),
            "fork": bool(repo_meta.get("fork")),
            "archived": bool(repo_meta.get("archived")),
            "stargazers_count": repo_meta.get("stargazers_count"),
            "pushed_at": repo_meta.get("pushed_at"),
        },
        "tree_truncated": bool(tree_payload.get("truncated")) if isinstance(tree_payload, dict) else False,
        "limits": {
            "max_files_seen": settings.max_github_files,
            "max_file_bytes": settings.max_github_file_bytes,
            "max_total_bytes": settings.max_github_total_bytes,
            "max_solidity_files": settings.max_github_solidity_files,
        },
        "structure_summary": summary,
        "dependency_manifests": dependency_manifests,
        "dependency_osv_engine": osv_dependency_engine,
        "fetched_files": fetched_files,
        "linked_contract_reports": linked_reports,
        "safety_controls": {
            "clone_repo": False,
            "execute_code": False,
            "install_dependencies": False,
            "private_repo_access": bool(settings.github_api_token),
            "read_only_public_api": True,
            "no_secret_collection": True,
        },
        "real_only_note": "Only actually fetched public repo evidence is scored. Missing private repo access, full dependency audit, CI execution, Slither/Aderyn, and deep analysis are not faked.",
    }
    return ScanResponse(
        report_id=_new_report_id(),
        generated_at=_now(),
        project_name=project_name or repo,
        module_score=ModuleScore(module="github", score=score, risk_label=risk_label(score)),  # type: ignore[arg-type]
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings, limit=8),
        input_hash=_hash(f"{owner}/{repo}@{effective_branch}|{len(limited_paths)}")[:16],
        engine_version="web3guard-github-repo-scanner-v12.1-osv-path-line",
        scan_metadata=metadata,
        disclaimer="This is a read-only public GitHub repository readiness scan. It does not clone, execute, install, exploit, or replace a full manual audit.",
    )


def github_scanner_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.0",
        "engine_version": "web3guard-github-repo-scanner-v12.0",
        "github_token_configured": bool(settings.github_api_token),
        "live_features": [
            "Public GitHub repo URL parsing",
            "GitHub API repository metadata fetch",
            "Recursive tree scanning with file/byte limits",
            "Solidity file discovery and limited rule-engine scan",
            "package.json, frontend, API, config, deploy script hints",
            "secret-like path/content pattern detection",
            "CI workflow, SECURITY.md, CODEOWNERS, lockfile, tests, README, license, and .gitignore readiness checks",
            "package.json dependency manifest summary without npm install/audit execution",
            "real-only output with no fake private repo/deep audit claims",
        ],
        "not_enabled_or_not_claimed": [
            "No repository cloning",
            "No dependency install or npm audit execution",
            "No private repo scan unless a real GitHub token is configured and authorized",
            "No Slither/Aderyn/Mythril execution in current",
            "No automatic code patching",
        ],
        "limits": {
            "max_github_files": settings.max_github_files,
            "max_github_file_bytes": settings.max_github_file_bytes,
            "max_github_total_bytes": settings.max_github_total_bytes,
            "max_github_solidity_files": settings.max_github_solidity_files,
            "timeout_seconds": settings.github_scan_timeout_seconds,
        },
    }
