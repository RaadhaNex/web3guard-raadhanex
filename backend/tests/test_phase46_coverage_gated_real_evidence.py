from datetime import datetime, timezone

from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.unified_url_scan import _coverage_gate, _real_evidence_summary, _score_split


def _card(module: str, assessed: bool, score: int | None = None) -> dict:
    return {
        "module": module,
        "label": module,
        "status": "Live" if assessed else "Not assessed",
        "assessed": assessed,
        "score": score if assessed else None,
        "risk_label": "Low" if assessed else "Not assessed",
        "required_input": [] if assessed else [f"{module} evidence"],
    }


def test_partial_scan_blocks_overall_confidence_score() -> None:
    module_cards = [
        _card("website", True, 92),
        _card("dapp", False),
        _card("api", False),
        _card("github", False),
        _card("contract", False),
        _card("static_analysis", False),
        _card("wallet", False),
        _card("admin_opsec", False),
    ]
    combined = {
        "combined": {"overall_score": 92, "available_score": 92, "risk_label": "Low"},
        "coverage": {"total_modules": 6, "assessed_count": 1},
    }

    gate = _coverage_gate(module_cards, combined)
    split = _score_split(module_cards, combined)

    assert gate["overall_confidence_allowed"] is False
    assert gate["blocked_score_fields"] == ["overall_score", "overall_launch_confidence"]
    assert split["overall_launch_confidence"]["score"] is None
    assert split["overall_launch_confidence"]["risk_label"] == "Insufficient Evidence"
    assert split["website_surface_score"]["score"] == 92


def test_full_scan_allows_overall_confidence_score() -> None:
    module_cards = [_card(module, True, 88) for module in ["website", "dapp", "api", "github", "contract", "static_analysis", "wallet", "admin_opsec"]]
    combined = {
        "combined": {"overall_score": 88, "available_score": 88, "risk_label": "Low"},
        "coverage": {"total_modules": 8, "assessed_count": 8},
    }

    gate = _coverage_gate(module_cards, combined)
    split = _score_split(module_cards, combined)

    assert gate["overall_confidence_allowed"] is True
    assert split["overall_launch_confidence"]["score"] == 88


def test_real_evidence_summary_never_turns_passive_hints_into_exploits() -> None:
    finding = Finding(
        id="website-1",
        module="website",
        severity="medium",
        title="Content-Security-Policy Uses Risky Directives",
        confidence="medium",
        source="Passive Website Surface Scanner",
        category="security_headers",
        rule_id="WEB-CSP-WEAK",
        description="CSP contains risky directive(s): 'unsafe-inline'.",
        business_impact="Website surface hardening issue.",
        developer_explanation="Observed from response header.",
        recommendation="Tighten CSP.",
    )
    report = ScanResponse(
        report_id="W3G-WEBSITE-TEST",
        generated_at=datetime.now(timezone.utc),
        project_name="Test",
        module_score=ModuleScore(module="website", score=92, risk_label="Low"),
        findings=[finding],
        scan_metadata={
            "raw_response_evidence": {"http_status": 200, "csp_value": "script-src 'unsafe-inline'"},
            "finding_truth_taxonomy": {
                "confirmed_observed_issue_count": 1,
                "potential_hardening_hint_count": 0,
                "confirmed_observed_issues": [{"title": finding.title}],
                "potential_hardening_hints": [],
            },
        },
    )

    summary = _real_evidence_summary(report, [_card("website", True, 92), _card("api", False)])

    assert summary["real_observed_issue_count"] == 1
    assert summary["confirmed_exploit_count"] == 0
    assert summary["website_raw_evidence"]["http_status"] == 200
