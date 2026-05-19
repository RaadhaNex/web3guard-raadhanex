from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

SECURITY_TESTS_REAL_ONLY_NOTE = (
    "Web3Guard Security Test Generator creates defensive starter templates and local verification commands only. "
    "It does not execute tools, does not attack live targets, does not generate exploit automation, and does not claim a certified audit."
)

SECURITY_TESTS_SAFE_BOUNDARY = (
    "Use generated templates only inside a local project, testnet, fork, or explicitly authorized environment. "
    "Never run generated commands against third-party systems without written authorization."
)

SUPPORTED_FRAMEWORKS = ["foundry", "echidna", "slither", "aderyn", "semgrep"]

DEFAULT_RISKS = [
    "reentrancy",
    "access_control",
    "pausable/emergency controls",
    "unchecked external calls",
    "approval/allowance UX",
    "upgrade authorization",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _safe_identifier(value: str | None, fallback: str = "TargetContract") -> str:
    raw = (value or fallback).strip()
    cleaned = "".join(ch for ch in raw if ch.isalnum() or ch == "_")
    if not cleaned:
        return fallback
    if cleaned[0].isdigit():
        cleaned = f"Contract{cleaned}"
    return cleaned[:64]


def _normalise_frameworks(frameworks: list[str] | None) -> list[str]:
    if not frameworks:
        return SUPPORTED_FRAMEWORKS[:]
    selected = []
    for item in frameworks:
        key = str(item).strip().lower()
        if key in SUPPORTED_FRAMEWORKS and key not in selected:
            selected.append(key)
    return selected or SUPPORTED_FRAMEWORKS[:]


def _normalise_risks(risks: list[str] | None) -> list[str]:
    values = [str(item).strip() for item in (risks or []) if str(item).strip()]
    return values[:20] or DEFAULT_RISKS[:]


def _foundry_template(contract_name: str, risks: list[str]) -> dict[str, Any]:
    risk_comments = "\n".join(f"    // TODO: Add assertion for {risk}." for risk in risks[:8])
    code = f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
// Import your contract after placing this file inside your Foundry project.
// import "../src/{contract_name}.sol";

contract {contract_name}SecurityTest is Test {{
    address internal owner = address(0xA11CE);
    address internal attacker = address(0xB0B);
    address internal user = address(0xCAFE);

    function setUp() public {{
        vm.label(owner, "owner");
        vm.label(attacker, "attacker");
        vm.label(user, "user");
        // TODO: Deploy {contract_name} here with realistic constructor args.
    }}

    function testUnauthorizedCallerCannotUsePrivilegedFunctions() public {{
        vm.startPrank(attacker);
        // TODO: call privileged functions and expect revert.
        // vm.expectRevert();
        // target.pause();
        vm.stopPrank();
    }}

    function testNoUnexpectedEtherStuckAfterUserFlow() public {{
        // TODO: Execute a normal deposit/withdraw/mint/burn flow.
        // assertEq(address(target).balance, expectedBalance);
    }}

    function testFuzzUserAmountDoesNotBreakAccounting(uint256 amount) public {{
        amount = bound(amount, 1, 1_000_000 ether);
        // TODO: apply operation with amount and assert supply/balance invariants.
    }}

{risk_comments}
}}
'''
    return {
        "id": "foundry_security_test",
        "framework": "foundry",
        "filename": f"test/{contract_name}.security.t.sol",
        "title": "Foundry defensive security test starter",
        "description": "Local unit/fuzz test scaffold for access control, accounting, and common launch blockers.",
        "language": "solidity",
        "content": code,
        "commands": [
            "forge test -vvv",
            f"forge test --match-contract {contract_name}SecurityTest -vvv",
        ],
        "review_note": "Developer must review and replace TODO sections with real contract deployment and assertions before trusting results.",
    }


def _echidna_template(contract_name: str, risks: list[str]) -> dict[str, Any]:
    code = f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Defensive Echidna property harness starter.
// Import and deploy your target contract locally. Do not run this against live systems.
// import "../src/{contract_name}.sol";

contract {contract_name}EchidnaProperties {{
    address internal owner = address(this);
    uint256 internal initialBalance;

    constructor() {{
        // TODO: Deploy {contract_name} and capture initial invariants.
        initialBalance = address(this).balance;
    }}

    function echidna_no_unexpected_eth_drain() public view returns (bool) {{
        // TODO: Replace with your treasury/accounting invariant.
        return address(this).balance >= initialBalance;
    }}

    function echidna_owner_never_zero() public view returns (bool) {{
        // TODO: Replace with target.owner() != address(0) when available.
        return owner != address(0);
    }}

    function echidna_supply_cap_not_exceeded() public view returns (bool) {{
        // TODO: Replace with totalSupply() <= cap() when token has a cap.
        return true;
    }}
}}
'''
    config = '''testMode: property
seqLen: 50
testLimit: 10000
corpusDir: echidna-corpus
shrinkLimit: 500
filterFunctions: []
'''
    return {
        "id": "echidna_property_harness",
        "framework": "echidna",
        "filename": f"test/{contract_name}.echidna.sol",
        "title": "Echidna property harness starter",
        "description": "Local property-based fuzzing starter for defensive invariants.",
        "language": "solidity",
        "content": code,
        "extra_files": [{"filename": "echidna.yaml", "content": config}],
        "commands": [
            f"echidna-test test/{contract_name}.echidna.sol --config echidna.yaml",
        ],
        "review_note": "Review properties carefully; they are placeholders until real invariants are wired to your contract.",
        "risk_focus": risks[:8],
    }


def _slither_pack(contract_name: str) -> dict[str, Any]:
    return {
        "id": "slither_command_pack",
        "framework": "slither",
        "filename": "security/slither-commands.md",
        "title": "Slither local analysis command pack",
        "description": "Commands to run Slither locally when installed. Web3Guard does not fake Slither output.",
        "language": "markdown",
        "content": f'''# Slither local command pack

Run only inside your own authorized local repository.

```bash
slither . --exclude-dependencies
slither . --json reports/slither-{contract_name}.json
slither . --print human-summary
slither . --print contract-summary
```

If Slither is not installed, keep the module status as `Tool Not Installed`.
''',
        "commands": [
            "slither . --exclude-dependencies",
            f"slither . --json reports/slither-{contract_name}.json",
        ],
        "review_note": "Treat Slither findings as analyst input; review false positives and confirm with tests.",
    }


def _aderyn_pack(contract_name: str) -> dict[str, Any]:
    return {
        "id": "aderyn_command_pack",
        "framework": "aderyn",
        "filename": "security/aderyn-commands.md",
        "title": "Aderyn local analysis command pack",
        "description": "Commands to run Aderyn locally when installed. No output is invented by Web3Guard.",
        "language": "markdown",
        "content": f'''# Aderyn local command pack

Run only inside your own authorized local repository.

```bash
aderyn .
aderyn . --output reports/aderyn-{contract_name}.md
```

If Aderyn is not installed, keep the module status as `Tool Not Installed`.
''',
        "commands": [
            "aderyn .",
            f"aderyn . --output reports/aderyn-{contract_name}.md",
        ],
        "review_note": "Aderyn output requires manual review and does not equal a certified audit.",
    }


def _semgrep_pack(project_type: str) -> dict[str, Any]:
    rules = '''rules:
  - id: web3guard-nextjs-dangerous-inner-html
    message: Avoid dangerouslySetInnerHTML unless content is sanitized and justified.
    severity: WARNING
    languages: [typescript, javascript]
    pattern: dangerouslySetInnerHTML
  - id: web3guard-hardcoded-private-key-like-value
    message: Potential hardcoded secret/private key-like value. Move secrets to environment variables.
    severity: ERROR
    languages: [typescript, javascript, python]
    patterns:
      - pattern-regex: '(private[_-]?key|secret|api[_-]?key)\\s*[:=]\\s*["\\'][A-Za-z0-9_\\-]{20,}["\\']'
  - id: web3guard-fastapi-wildcard-cors
    message: Avoid wildcard CORS in production APIs.
    severity: WARNING
    languages: [python]
    pattern-regex: 'allow_origins\\s*=\\s*\\[\\s*["\\']\\*["\\']\\s*\\]'
'''
    return {
        "id": "semgrep_starter_rules",
        "framework": "semgrep",
        "filename": "security/semgrep-web3guard.yml",
        "title": "Semgrep starter rules for frontend/API hygiene",
        "description": f"Starter Semgrep rules for {project_type or 'Web3'} app hygiene. These are defensive checks, not exploit automation.",
        "language": "yaml",
        "content": rules,
        "commands": [
            "semgrep scan --config security/semgrep-web3guard.yml .",
            "semgrep scan --config p/owasp-top-ten .",
        ],
        "review_note": "Review and tune Semgrep rules to your repository before using them for release gates.",
    }


def generate_security_test_pack(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    contract_name = _safe_identifier(str(payload.get("contract_name") or payload.get("project_name") or "TargetContract"))
    project_type = str(payload.get("project_type") or "Web3 launch")[:100]
    risks = _normalise_risks(payload.get("risk_focus") if isinstance(payload.get("risk_focus"), list) else None)
    frameworks = _normalise_frameworks(payload.get("frameworks") if isinstance(payload.get("frameworks"), list) else None)

    template_builders = {
        "foundry": lambda: _foundry_template(contract_name, risks),
        "echidna": lambda: _echidna_template(contract_name, risks),
        "slither": lambda: _slither_pack(contract_name),
        "aderyn": lambda: _aderyn_pack(contract_name),
        "semgrep": lambda: _semgrep_pack(project_type),
    }
    templates = [template_builders[name]() for name in frameworks]
    bundle_payload = {
        "contract_name": contract_name,
        "project_type": project_type,
        "risks": risks,
        "frameworks": frameworks,
        "template_ids": [item["id"] for item in templates],
    }
    bundle_hash = _sha(bundle_payload)

    return {
        "ok": True,
        "generated_at": _now(),
        "bundle_id": f"w3g_test_pack_{bundle_hash[:16]}",
        "contract_name": contract_name,
        "project_type": project_type,
        "risk_focus": risks,
        "frameworks": frameworks,
        "templates": templates,
        "commands": [
            {
                "label": "Run Foundry tests",
                "command": "forge test -vvv",
                "requires": "Foundry installed and local project configured",
                "safe_boundary": "Local defensive tests only",
            },
            {
                "label": "Run Echidna properties",
                "command": f"echidna-test test/{contract_name}.echidna.sol --config echidna.yaml",
                "requires": "Echidna installed and properties customized",
                "safe_boundary": "Local property fuzzing only",
            },
            {
                "label": "Run static analyzers",
                "command": "slither . --exclude-dependencies && aderyn .",
                "requires": "Slither/Aderyn installed locally",
                "safe_boundary": "No output is claimed unless tool actually runs",
            },
            {
                "label": "Run Semgrep hygiene checks",
                "command": "semgrep scan --config security/semgrep-web3guard.yml .",
                "requires": "Semgrep installed locally",
                "safe_boundary": "Static defensive checks only",
            },
        ],
        "blocked_use_cases": [
            "attacking live third-party targets",
            "bypassing authentication without authorization",
            "wallet signing or key collection",
            "claiming generated templates are a certified audit",
            "publishing unreviewed generated output as proof of safety",
        ],
        "real_only_note": SECURITY_TESTS_REAL_ONLY_NOTE,
        "safe_boundary": SECURITY_TESTS_SAFE_BOUNDARY,
    }


def security_tests_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Phase 17 - Security Test Generator",
        "version": "1.0",
        "capabilities": [
            "Foundry starter test templates",
            "Echidna property harness starter",
            "Slither command pack",
            "Aderyn command pack",
            "Semgrep starter rules",
            "defensive local verification commands",
        ],
        "frameworks": SUPPORTED_FRAMEWORKS,
        "blocked_capabilities": [
            "exploit automation",
            "unauthorized live target testing",
            "fake tool output",
            "certified audit claim",
            "wallet signing",
            "private key or seed phrase collection",
        ],
        "real_only_note": SECURITY_TESTS_REAL_ONLY_NOTE,
        "safe_boundary": SECURITY_TESTS_SAFE_BOUNDARY,
    }
