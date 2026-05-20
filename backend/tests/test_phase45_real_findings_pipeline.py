from app.services.real_findings_pipeline import build_real_findings_pipeline


def _base_payload():
    return {
        "report_id": "W3G-URL-LAUNCH-test",
        "module_cards": [
            {
                "module": "website",
                "label": "Website Surface",
                "status": "Live",
                "score": 82,
                "risk_label": "Medium risk",
                "assessed": True,
                "findings_count": 1,
                "critical_high_count": 0,
                "evidence": ["HTTP status: 200"],
                "limitations": [],
                "required_input": [],
            },
            {
                "module": "contract",
                "label": "Smart Contract",
                "status": "Not assessed",
                "score": None,
                "risk_label": "Not assessed",
                "assessed": False,
                "findings_count": 0,
                "critical_high_count": 0,
                "evidence": [],
                "limitations": ["No source"],
                "required_input": ["Paste Solidity"],
            },
        ],
        "surface_hints": {
            "static_analysis": {
                "state": "Assessed",
                "tools": [
                    {"tool": "slither", "state": "Assessed", "installed": True, "enabled_by_env": True, "will_run": True, "real_findings": 1},
                    {"tool": "semgrep", "state": "Tool Not Installed", "installed": False, "enabled_by_env": False, "will_run": False, "real_findings": 0},
                ],
                "findings": [
                    {
                        "id": "static-slither-001",
                        "module": "static_analysis",
                        "severity": "high",
                        "title": "Arbitrary Send Ether",
                        "description": "Slither reported a send pattern.",
                        "source": "Slither Real Tool Output",
                        "category": "static_analysis",
                        "rule_id": "SLITHER-arbitrary-send-eth",
                        "business_impact": "Funds risk.",
                        "developer_explanation": "Real tool output.",
                        "recommendation": "Restrict withdrawal logic.",
                    }
                ],
                "status_messages": [
                    {
                        "id": "static-semgrep-status-001",
                        "module": "static_analysis",
                        "severity": "info",
                        "title": "Semgrep Not Run",
                        "description": "binary missing",
                        "source": "Static Analysis Tool Status",
                        "category": "tool_status",
                        "business_impact": "Missing evidence.",
                        "developer_explanation": "Install tool.",
                        "recommendation": "Install Semgrep.",
                    }
                ],
            }
        },
        "combined_report": {
            "report_id": "W3G-COMBINED-test",
            "report_hash": "abc123",
            "top_findings": [],
            "client_delivery": {
                "delivery_formats": ["pdf", "html", "markdown", "json"],
                "manual_verification_required": True,
                "public_wording": "Pre-audit readiness report. Not a certified audit.",
            },
            "executive_summary": "Pre-audit readiness only.",
            "public_summary_note": "Does not replace professional review.",
            "markdown_report": "# Report",
            "json_export": {"ok": True},
        },
        "blocked_claims": [
            "Do not claim certified audit.",
            "Do not claim 100% secure.",
            "Do not claim all vulnerabilities found.",
        ],
        "safe_public_summary": "Pre-audit readiness only. Not a certified audit.",
        "disclaimer": "No security guarantee.",
    }


def test_pipeline_separates_real_findings_from_tool_status_messages():
    result = build_real_findings_pipeline(_base_payload())
    assert result["pipeline_ready"] is True
    assert result["summary"]["real_findings"] == 1
    assert result["summary"]["tool_status_messages"] == 1
    assert result["severity_breakdown"]["high"] == 1
    assert result["export_gate"]["export_ready"] is True
    assert result["normalized_findings"][0]["source_bucket"] == "surface.static_analysis.findings"


def test_pipeline_blocks_fake_score_for_unassessed_module():
    payload = _base_payload()
    payload["module_cards"][1]["score"] = 91
    result = build_real_findings_pipeline(payload)
    assert result["pipeline_ready"] is False
    assert any("score must stay null" in issue for issue in result["integrity"]["blockers"])


def test_pipeline_blocks_fake_tool_findings_when_tool_missing():
    payload = _base_payload()
    payload["surface_hints"]["static_analysis"]["tools"][1]["real_findings"] = 2
    result = build_real_findings_pipeline(payload)
    assert result["pipeline_ready"] is False
    assert any("fake tool output" in issue.lower() for issue in result["integrity"]["blockers"])


def test_pipeline_blocks_unsafe_public_claims():
    payload = _base_payload()
    payload["combined_report"]["executive_summary"] = "This project is 100% secure."
    result = build_real_findings_pipeline(payload)
    assert result["pipeline_ready"] is False
    assert any("unsafe claim" in issue.lower() for issue in result["integrity"]["blockers"])
