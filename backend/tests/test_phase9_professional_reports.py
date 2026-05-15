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
                "fingerprint": f"{module}123phase9",
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
        "project_name": "Phase 9 Launch",
        "module_score": {"module": module, "score": score, "risk_label": "Medium Risk, Fix Before Launch", "assessed": True},
        "findings": finding,
        "severity_breakdown": {"critical": 1 if severity == "critical" else 0, "high": 1 if severity == "high" else 0, "medium": 1 if severity == "medium" else 0, "low": 0, "info": 0},
        "priority_actions": ["Fix this issue"] if severity else [],
        "input_hash": f"hash-{module}",
        "engine_version": f"engine-{module}",
        "scan_metadata": {"phase": "phase9-test"},
        "disclaimer": "Preliminary security review only.",
    }


def build_report():
    response = client.post("/report/combined", json={
        "project_name": "Phase 9 Launch",
        "reports": [
            fake_scan("contract", 72, "high"),
            fake_scan("website", 84, "medium"),
            fake_scan("dapp", 81, None),
        ],
        "include_ai": False,
    })
    assert response.status_code == 200, response.text
    return response.json()


def test_phase9_delivery_policy_is_real_only():
    response = client.get("/report/delivery-policy")
    assert response.status_code == 200
    data = response.json()
    assert "server_pdf" in data["live_formats"]
    assert "Certified audit" in data["blocked_claims"]
    assert "not a certified audit" in data["real_only_note"].lower()


def test_phase9_artifacts_and_pdf_export_are_real_bytes():
    report = build_report()
    artifacts = client.post("/report/artifacts", json={"report": report})
    assert artifacts.status_code == 200, artifacts.text
    data = artifacts.json()
    assert data["formats"]["server_pdf"] is True
    assert data["pdf_size_bytes"] > 1000
    assert "Professional Launch Readiness Report" in data["html_preview"]

    pdf = client.post("/report/export/pdf", json={"report": report})
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")
    assert len(pdf.content) > 1000

    html = client.post("/report/export/html", json={"report": report})
    assert html.status_code == 200
    assert "text/html" in html.headers["content-type"]
    assert b"Pre-audit readiness" in html.content


def test_phase9_publication_and_hash_verification():
    report = build_report()
    create = client.post("/report/publication", json={"report": report, "visibility": "public"})
    assert create.status_code == 200, create.text
    record = create.json()["record"]
    assert record["visibility"] == "public"
    assert record["manual_review_claim_allowed"] is False
    assert "Certified audit" in record["blocked_wording"]

    verify = client.get(f"/report/public/{record['id']}/verify", params={"report_hash": report["report_hash"]})
    assert verify.status_code == 200
    assert verify.json()["verified"] is True

    wrong = client.get(f"/report/public/{record['id']}/verify", params={"report_hash": "0" * 64})
    assert wrong.status_code == 200
    assert wrong.json()["verified"] is False
