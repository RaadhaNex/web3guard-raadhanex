from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def fake_scan(module: str, score: int, severity: str | None = None):
    finding = []
    if severity:
        finding = [
            {
                "id": f"{module}-finding-1",
                "module": module,
                "severity": severity,
                "title": f"{module} launch risk",
                "description": "A launch risk needs review before production.",
                "affected_line": None,
                "affected_function": None,
                "affected_code": None,
                "confidence": "high",
                "source": "Test Engine",
                "category": "test",
                "rule_id": f"{module.upper()}-TEST",
                "fingerprint": f"{module}123",
                "business_impact": "Can reduce user trust or expose funds during launch.",
                "developer_explanation": "Fix and validate before launch.",
                "recommendation": "Fix this issue and regenerate the report.",
                "references": [],
                "paid_review_recommended": severity in {"critical", "high"},
                "ai_explanation": None,
            }
        ]
    return {
        "report_id": f"scan-{module}",
        "generated_at": "2026-05-14T00:00:00Z",
        "project_name": "Full Launch",
        "module_score": {"module": module, "score": score, "risk_label": "Medium Risk, Fix Before Launch", "assessed": True},
        "findings": finding,
        "severity_breakdown": {"critical": 1 if severity == "critical" else 0, "high": 1 if severity == "high" else 0, "medium": 1 if severity == "medium" else 0, "low": 0, "info": 0},
        "priority_actions": ["Fix this issue"] if severity else [],
        "input_hash": f"hash-{module}",
        "engine_version": f"engine-{module}",
        "scan_metadata": {"phase": "test"},
        "disclaimer": "Preliminary security review only.",
    }


def test_phase58_combined_report_has_full_weighted_score_exports_and_delivery_fields():
    reports = [
        fake_scan("contract", 50, "critical"),
        fake_scan("website", 80, "medium"),
        fake_scan("dapp", 75, "high"),
        fake_scan("api", 70, "medium"),
        fake_scan("wallet", 65, "high"),
        fake_scan("admin_opsec", 40, "critical"),
    ]
    response = client.post("/report/combined", json={"project_name": "Full Launch", "reports": reports, "preferred_language": "Hinglish", "include_ai": True})
    assert response.status_code == 200
    data = response.json()
    assert data["report_id"].startswith("W3G-RAADHANEX-")
    assert len(data["report_hash"]) == 64
    assert data["combined"]["overall_score"] is not None
    assert data["coverage"]["coverage_percent"] == 100
    assert data["score_confidence"] == "high"
    assert len(data["module_matrix"]) == 7
    assert data["client_delivery"]["manual_verification_required"] is True
    assert "Certified audit" in data["client_delivery"]["do_not_use_wording"]
    assert "Verification hash" in data["markdown_report"]
    assert data["json_export"]["report_hash"] == data["report_hash"]
    assert data["before_launch_checklist"]


def test_phase58_partial_report_clearly_marks_missing_modules():
    response = client.post("/report/combined", json={"project_name": "Partial Launch", "reports": [fake_scan("contract", 82, "medium")], "include_ai": False})
    assert response.status_code == 200
    data = response.json()
    assert data["combined"]["overall_score"] is None
    assert data["combined"]["available_score"] == 82
    assert data["coverage"]["coverage_percent"] == 17
    assert data["score_confidence"] in {"low", "limited"}
    assert "website" in data["coverage"]["missing_modules"]
    assert any(row["module"] == "website" and row["assessed"] is False for row in data["module_matrix"])
    assert "Missing modules reduce confidence" in " ".join(data["limitations"])
