from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_sentinel_status_and_sources():
    status = client.get("/sentinel/status")
    assert status.status_code == 200
    body = status.json()
    assert body["ok"] is True
    assert "public vulnerability intelligence" in body["real_only_note"].lower()
    assert "indexed_public_advisories" in body["counts"]

    sources = client.get("/sentinel/sources")
    assert sources.status_code == 200
    source_body = sources.json()
    assert source_body["ok"] is True
    ids = {item["id"] for item in source_body["sources"]}
    assert {"nvd", "osv", "github_advisory", "cisa_kev"}.issubset(ids)


def test_sentinel_ingest_requires_acknowledgement():
    response = client.post("/sentinel/intelligence/ingest", json={"source": "osv", "records": [{"id": "OSV-TEST-1", "title": "Test advisory"}]}, headers={"x-admin-token": "change-this-admin-token"})
    assert response.status_code == 400
    assert "acknowledgement" in response.json()["detail"].lower()


def test_sentinel_ingest_and_intelligence_listing():
    payload = {
        "source": "osv",
        "real_only_acknowledged": True,
        "imported_by": "pytest",
        "records": [
            {
                "id": "OSV-PHASE15-TEST",
                "title": "Phase 15 test dependency advisory",
                "severity": "high",
                "package": "phase15-test-package",
                "ecosystem": "npm",
                "summary": "Test-only record used to validate indexing wording.",
                "tags": ["dependency", "npm"],
            }
        ],
    }
    response = client.post("/sentinel/intelligence/ingest", json=payload, headers={"x-admin-token": "change-this-admin-token"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["safe_counting_note"].startswith("Inserted records are counted")

    listing = client.get("/sentinel/intelligence?query=phase15-test-package")
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert any(item["id"] == "OSV-PHASE15-TEST" for item in items)


def test_sentinel_project_alerts_empty_is_real_only():
    response = client.get("/sentinel/project-alerts?user_id=phase15-nonexistent-user")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["alerts"] == []
    assert "does not generate fake" in body["real_only_note"].lower()


def test_sentinel_disclosure_draft_is_not_sent():
    payload = {
        "target": "Example project",
        "contact": "security@example.com",
        "finding_summary": "Missing security.txt file on public website.",
        "evidence_summary": "Passive HTTP check found no /.well-known/security.txt response.",
        "confidence": "needs_manual_validation",
        "real_only_acknowledged": True,
    }
    response = client.post("/sentinel/disclosure/draft", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["draft"]["status"] == "draft_only_not_sent"
    assert "No exploit attempt" in body["draft"]["draft"]
