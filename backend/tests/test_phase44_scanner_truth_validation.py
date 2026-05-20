from app.services.scanner_truth_validation import validate_scanner_truth, scanner_truth_validation_status


def _sample_unified_result():
    return {
        "report_id": "W3G-URL-LAUNCH-test",
        "generated_at": "2026-05-20T00:00:00+00:00",
        "website_url": "https://example.com",
        "project_name": "Truth QA Sample",
        "realness_rule": "Only modules with real input/evidence receive a score.",
        "safe_public_summary": "This is a preliminary URL launch-surface review. It is not a certified audit.",
        "disclaimer": "This is a preliminary security review and does not replace a full manual audit.",
        "blocked_claims": ["Do not say this project is certified audited."],
        "module_cards": [
            {
                "module": "website",
                "label": "Website Surface",
                "status": "Live",
                "score": 82,
                "risk_label": "Medium",
                "assessed": True,
                "findings_count": 1,
                "critical_high_count": 0,
                "evidence": ["HTTP status: 200"],
                "limitations": ["Passive only"],
                "required_input": [],
            },
            {
                "module": "dapp",
                "label": "dApp Frontend Hints",
                "status": "Live limited hints",
                "score": None,
                "risk_label": "Not assessed",
                "assessed": False,
                "findings_count": 0,
                "critical_high_count": 0,
                "evidence": ["No wallet hints found"],
                "limitations": ["Need source review"],
                "required_input": ["Frontend source/GitHub repo"],
            },
            {
                "module": "api",
                "label": "API Backend",
                "status": "Not assessed",
                "score": None,
                "risk_label": "Not assessed",
                "assessed": False,
                "findings_count": 0,
                "critical_high_count": 0,
                "evidence": [],
                "limitations": ["Need API URL"],
                "required_input": ["API base URL"],
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
                "limitations": ["Need Solidity source"],
                "required_input": ["Solidity source"],
            },
            {
                "module": "static_analysis",
                "label": "Slither / Semgrep Static Analysis",
                "status": "Tool Not Installed",
                "score": None,
                "risk_label": "Tool Not Installed",
                "assessed": False,
                "findings_count": 0,
                "critical_high_count": 0,
                "evidence": ["Slither: Tool Not Installed (0 real finding(s))"],
                "limitations": ["No fake tool findings"],
                "required_input": ["Install/enable tools"],
            },
            {
                "module": "wallet",
                "label": "Wallet Flow",
                "status": "Manual input required",
                "score": None,
                "risk_label": "Not assessed",
                "assessed": False,
                "findings_count": 0,
                "critical_high_count": 0,
                "evidence": [],
                "limitations": ["No signing"],
                "required_input": ["Wallet checklist"],
            },
            {
                "module": "admin_opsec",
                "label": "Founder/Admin OpSec",
                "status": "Manual input required",
                "score": None,
                "risk_label": "Not assessed",
                "assessed": False,
                "findings_count": 0,
                "critical_high_count": 0,
                "evidence": [],
                "limitations": ["Need admin checklist"],
                "required_input": ["Admin OpSec checklist"],
            },
            {
                "module": "github",
                "label": "GitHub Repository",
                "status": "Not assessed",
                "score": None,
                "risk_label": "Not assessed",
                "assessed": False,
                "findings_count": 0,
                "critical_high_count": 0,
                "evidence": [],
                "limitations": ["Need repo URL"],
                "required_input": ["GitHub repo URL"],
            },
        ],
        "surface_hints": {
            "static_analysis": {
                "state": "Not Assessed",
                "assessed": False,
                "tools": [
                    {"tool": "slither", "state": "Tool Not Installed", "status": "not_run", "installed": False, "real_findings": 0},
                    {"tool": "semgrep", "state": "Provider Not Configured", "status": "not_run", "installed": True, "real_findings": 0},
                ],
                "findings": [],
            },
            "github_dependency_risk": {
                "state": "Not Assessed",
                "dependency_manifests": [],
                "osv_state": "Provider Not Configured",
            },
            "api_admin_exposure": {
                "state": "Not Assessed",
                "safe_endpoints_checked": [],
                "safety_controls": {"no_fuzzing": True, "no_auth_bypass": True, "no_payload_spraying": True},
            },
        },
        "combined_report": {
            "coverage": {"assessed_count": 1, "total_modules": 8, "confidence": "partial"},
            "module_matrix": [{"module": "website", "assessed": True}],
            "priority_action_plan": [{"title": "Provide Solidity source", "severity": "info"}],
            "markdown_report": "# Truth QA Sample\n\nPre-audit readiness only.",
            "json_export": {"report_id": "W3G-URL-LAUNCH-test"},
            "client_delivery": {"delivery_formats": ["PDF", "HTML", "MD", "JSON"]},
        },
    }


def test_phase44_status_is_safe():
    status = scanner_truth_validation_status()
    assert status["ok"] is True
    assert "does not install" in " ".join(status["what_this_does_not_do"]).lower()
    assert "Not Assessed" in status["safe_states"]


def test_phase44_accepts_truthful_partial_scan():
    result = validate_scanner_truth({"unified_scan_result": _sample_unified_result(), "real_only_acknowledged": True})
    assert result["ok"] is True
    assert result["truth_score"] >= 70
    assert not result["blockers"]
    assert result["surface_truth"]["static_analysis"]["tools"][0]["state"] == "Tool Not Installed"


def test_phase44_blocks_unassessed_module_score():
    sample = _sample_unified_result()
    sample["module_cards"][1]["score"] = 99
    result = validate_scanner_truth({"unified_scan_result": sample, "real_only_acknowledged": True})
    assert any(item["title"] == "Unassessed module has a score" for item in result["blockers"])
    assert result["truth_score"] < 90


def test_phase44_blocks_fake_static_tool_findings():
    sample = _sample_unified_result()
    sample["surface_hints"]["static_analysis"]["tools"][0]["real_findings"] = 3
    result = validate_scanner_truth({"unified_scan_result": sample, "real_only_acknowledged": True})
    assert any("Static tool has findings" in item["title"] for item in result["blockers"])


def test_phase44_blocks_fake_security_claims():
    sample = _sample_unified_result()
    sample["safe_public_summary"] = "This scan proves the project is 100% secure."
    result = validate_scanner_truth({"unified_scan_result": sample, "real_only_acknowledged": True})
    assert any(item["title"] == "Blocked/fake security claim detected" for item in result["blockers"])
