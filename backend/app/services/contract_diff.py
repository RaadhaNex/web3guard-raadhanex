from __future__ import annotations

import difflib
import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scan_contract import scan_solidity
from app.services.scoring import priority_actions, risk_label, score_findings, severity_breakdown
from app.services.solidity_utils import all_match_lines, extract_functions, line_text, sha12

ENGINE_VERSION = "web3guard-contract-diff-engine-v1.0-megaA"
RISK_PATTERNS = {
    # Specific launch/security surfaces are checked before generic owner/admin modifiers.
    "new_external_call": [r"\.call\s*\(", r"delegatecall", r"staticcall"],
    "new_supply_control": [r"\bmint\s*\(", r"MINTER_ROLE"],
    "new_upgrade_control": [r"upgradeTo", r"_authorizeUpgrade", r"UUPSUpgradeable", r"TransparentUpgradeableProxy"],
    "new_fee_control": [r"setFee", r"setTax", r"feeBps", r"taxFee"],
    "new_pause_freeze": [r"pause\s*\(", r"blacklist", r"freeze"],
    "new_owner_control": [r"onlyOwner", r"DEFAULT_ADMIN_ROLE", r"grantRole", r"transferOwnership"],
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_id(project_name: str | None) -> str:
    return f"W3G-DIFF-{sha12((project_name or 'diff') + str(_now()))}-{_now().strftime('%Y%m%d%H%M%S')}".upper()


def contract_diff_status() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Mega Phase A - Phase 18 Contract Diff + Audit History",
        "engine_version": ENGINE_VERSION,
        "mode": "read_only_old_vs_new_source_comparison",
        "live_capabilities": [
            "Unified diff generation",
            "Old/new rule-engine score comparison",
            "Newly introduced privileged/risky pattern detection",
            "Fixed/new/open finding summary using real scan outputs",
        ],
        "not_claimed": [
            "Does not prove semantic equivalence",
            "Does not run compiler storage layout unless Phase 19/13 tools are configured",
            "Does not auto-apply fixes",
        ],
    }


def _lines_added(old: str, new: str) -> list[tuple[int, str]]:
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    added: list[tuple[int, str]] = []
    new_line_no = 0
    for line in difflib.ndiff(old_lines, new_lines):
        prefix = line[:2]
        text = line[2:]
        if prefix == "  ":
            new_line_no += 1
        elif prefix == "+ ":
            new_line_no += 1
            added.append((new_line_no, text))
        elif prefix == "- ":
            continue
    return added


def _finding_key(f: Finding) -> str:
    return f"{f.rule_id or f.title}:{f.category}:{f.affected_function or ''}"


def _make_added_risk_finding(idx: int, category: str, line_no: int, snippet: str, project_name: str | None) -> Finding:
    title_map = {
        "new_external_call": "New external-call surface introduced",
        "new_owner_control": "New owner/admin control introduced",
        "new_supply_control": "New mint/supply control introduced",
        "new_upgrade_control": "New upgrade-control surface introduced",
        "new_fee_control": "New fee/tax control introduced",
        "new_pause_freeze": "New pause/freeze/blacklist control introduced",
    }
    severity_map = {
        "new_external_call": "high",
        "new_upgrade_control": "high",
        "new_supply_control": "high",
        "new_owner_control": "medium",
        "new_fee_control": "medium",
        "new_pause_freeze": "medium",
    }
    return Finding(
        id=f"contract-diff-{idx:03d}",
        module="contract_diff",  # type: ignore[arg-type]
        severity=severity_map.get(category, "medium"),  # type: ignore[arg-type]
        title=title_map.get(category, "New risky code pattern introduced"),
        description=f"The new version adds code matching {category}. Review before merging or deploying.",
        affected_line=line_no,
        affected_code=snippet,
        confidence="medium",
        source="Web3Guard Contract Diff Engine v1",
        category=category,
        rule_id=f"DIFF_{category.upper()}",
        fingerprint=hashlib.sha1(f"{category}:{line_no}:{snippet}:{project_name}".encode()).hexdigest()[:16],
        business_impact="A new version can fix old bugs but also introduce new launch/admin/security risk.",
        developer_explanation="This finding is based on added lines only. Confirm intended access control and test coverage.",
        recommendation="Review this added code, add tests, update transparency docs, and rerun contract/static/deep scanners before deployment.",
        paid_review_recommended=True,
    )


def build_contract_diff_report(*, project_name: str | None, old_code: str, new_code: str, contract_type: str | None = None) -> ScanResponse:
    if len(old_code.strip()) < 20 or len(new_code.strip()) < 20:
        raise ValueError("Both old and new Solidity source inputs are required. No fake diff report will be generated.")
    if old_code == new_code:
        raise ValueError("Old and new source are identical. Provide a real changed version to generate a diff report.")
    if len(old_code) + len(new_code) > 360000:
        raise ValueError("Diff input is too large for MVP scanner limits.")

    old_scan = scan_solidity(old_code, project_name=f"{project_name or 'Project'} old", contract_type=contract_type)
    new_scan = scan_solidity(new_code, project_name=f"{project_name or 'Project'} new", contract_type=contract_type)
    old_keys = {_finding_key(f) for f in old_scan.findings}
    new_keys = {_finding_key(f) for f in new_scan.findings}
    fixed = sorted(old_keys - new_keys)
    introduced_from_scan = sorted(new_keys - old_keys)
    still_open = sorted(old_keys & new_keys)

    diff_text = "\n".join(difflib.unified_diff(old_code.splitlines(), new_code.splitlines(), fromfile="old.sol", tofile="new.sol", lineterm=""))
    added = _lines_added(old_code, new_code)
    findings: list[Finding] = []
    idx = 1
    for line_no, snippet in added:
        for category, patterns in RISK_PATTERNS.items():
            if any(re.search(pattern, snippet, flags=re.IGNORECASE) for pattern in patterns):
                findings.append(_make_added_risk_finding(idx, category, line_no, snippet, project_name))
                idx += 1
                break
        if idx > 25:
            break

    for key in introduced_from_scan[:12]:
        findings.append(Finding(
            id=f"contract-diff-{idx:03d}",
            module="contract_diff",  # type: ignore[arg-type]
            severity="medium",
            title="New scanner finding appears in updated version",
            description=f"Rule-engine finding key appears in new version but not old version: {key}",
            confidence="medium",
            source="Web3Guard Contract Diff Engine v1 + Solidity Rule Engine",
            category="new_rule_engine_finding",
            rule_id="DIFF_NEW_RULE_ENGINE_FINDING",
            fingerprint=hashlib.sha1(key.encode()).hexdigest()[:16],
            business_impact="The update may introduce a new security or launch-readiness issue.",
            developer_explanation="Compare old/new findings and inspect the matching rule-engine finding in the new scan.",
            recommendation="Open the new scan finding, review affected code, and add regression tests before deployment.",
            paid_review_recommended=True,
        ))
        idx += 1

    # Score is intentionally based on new diff risks, not an invented audit certificate.
    score = score_findings(findings)
    report_id = _report_id(project_name)
    return ScanResponse(
        report_id=report_id,
        generated_at=_now(),
        project_name=project_name,
        module_score=ModuleScore(module="contract_diff", score=score, risk_label=risk_label(score)),  # type: ignore[arg-type]
        findings=findings,
        severity_breakdown=severity_breakdown(findings),
        priority_actions=priority_actions(findings),
        input_hash=_hash(old_code + "\n---NEW---\n" + new_code),
        engine_version=ENGINE_VERSION,
        scan_metadata={
            "phase": "Mega Phase A / Phase 18",
            "real_only_note": "Diff is generated only from provided old/new Solidity source. It does not auto-apply fixes.",
            "old_score": old_scan.module_score.score,
            "new_score": new_scan.module_score.score,
            "score_delta": new_scan.module_score.score - old_scan.module_score.score,
            "fixed_finding_keys": fixed,
            "introduced_finding_keys": introduced_from_scan,
            "still_open_finding_keys": still_open,
            "added_line_count": len(added),
            "removed_line_count": sum(1 for line in difflib.ndiff(old_code.splitlines(), new_code.splitlines()) if line.startswith('- ')),
            "diff_preview": diff_text[:30000],
            "old_report_id": old_scan.report_id,
            "new_report_id": new_scan.report_id,
            "next_steps": [
                "Review all new privileged/risky added lines.",
                "Run static analysis on the new version.",
                "If upgradeable, run Phase 19 upgrade safety analysis.",
                "Do not deploy until critical/high introduced findings are resolved or accepted with documented rationale.",
            ],
        },
    )
