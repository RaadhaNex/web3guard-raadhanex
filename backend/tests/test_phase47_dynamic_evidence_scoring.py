from datetime import datetime, timezone

from app.models.schemas import Finding, ModuleScore, ScanResponse
from app.services.scoring import score_findings_with_trace
from app.services.unified_url_scan import _real_evidence_summary


def _finding(idx: int, severity: str, title: str, category: str = "security_headers", confidence: str = "medium") -> Finding:
    return Finding(
        id=f"website-{idx}",
        module="website",
        severity=severity,  # type: ignore[arg-type]
        title=title,
        description=f"Observed {title}",
        confidence=confidence,  # type: ignore[arg-type]
        source="Passive Website Surface Scanner",
        category=category,
        rule_id=f"WEB-DYN-{idx}",
        business_impact="Launch surface hardening issue.",
        developer_explanation="Observed from real passive evidence.",
        recommendation="Fix and rerun the scan.",
    )


def test_dynamic_score_changes_when_real_findings_change() -> None:
    csp_only = [_finding(1, "medium", "Content-Security-Policy Uses Risky Directives")]
    csp_plus_error = csp_only + [_finding(2, "high", "Homepage Returns Server Error", "availability", "high")]

    first = score_findings_with_trace(csp_only)
    second = score_findings_with_trace(csp_plus_error)

    assert first["score"] != second["score"]
    assert first["score"] > second["score"]
    assert first["breakdown"][0]["title"] == "Content-Security-Policy Uses Risky Directives"
    assert second["severity_breakdown"]["high"] == 1
    assert second["total_penalty"] > first["total_penalty"]


def test_dynamic_score_trace_is_reportable_evidence_not_fake_claim() -> None:
    findings = [
        _finding(1, "medium", "Content-Security-Policy Uses Risky Directives"),
        _finding(2, "low", "High Inline Script Count", "frontend_supply_chain"),
    ]
    trace = score_findings_with_trace(findings)
    report = ScanResponse(
        report_id="W3G-WEBSITE-DYN",
        generated_at=datetime.now(timezone.utc),
        project_name="Dynamic Test",
        module_score=ModuleScore(module="website", score=trace["score"], risk_label=trace["risk_label"]),
        findings=findings,
        scan_metadata={
            "dynamic_score_trace": trace,
            "raw_response_evidence": {"http_status": 200, "csp_value": "script-src 'unsafe-inline'"},
            "finding_truth_taxonomy": {
                "confirmed_observed_issue_count": 2,
                "potential_hardening_hint_count": 0,
                "confirmed_observed_issues": [{"title": item.title} for item in findings],
                "potential_hardening_hints": [],
            },
        },
    )

    summary = _real_evidence_summary(report, [{"module": "website", "assessed": True}, {"module": "api", "assessed": False}])

    assert summary["dynamic_score_trace"]["score"] == trace["score"]
    assert summary["dynamic_score_trace"]["finding_count"] == 2
    assert summary["confirmed_exploit_count"] == 0
    assert "certified" not in summary["score_debug_note"].lower()
