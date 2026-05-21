import json

from app.models.schemas import Finding
from app.services.source_evidence_mapper import analyze_source_evidence_artifacts
from app.services.static_analysis_artifacts import analyze_static_artifacts


def test_source_evidence_mapper_emits_exact_file_line_and_redacts_secret():
    artifact = json.dumps({
        "files": [
            {"path": "backend/main.py", "content": "import subprocess\ndef run(user):\n    subprocess.run(user, shell=True)\n"},
            {"path": ".env.local", "content": "SUPABASE_SERVICE_ROLE_KEY=abcd1234abcd1234abcd1234abcd1234\n"},
        ]
    })

    report = analyze_source_evidence_artifacts(security_tool_artifacts_json=artifact, project_name="Demo")

    assert report is not None
    assert report.scan_metadata["files_parsed"] == 2
    assert report.scan_metadata["findings_with_exact_location"] >= 2
    assert any(f.affected_file == "backend/main.py" and f.affected_line == 3 for f in report.findings)
    secret_finding = next(f for f in report.findings if f.affected_file == ".env.local" and f.rule_id == "WG-SRC-SECRET-001")
    assert "abcd1234" not in (secret_finding.affected_code or "")
    assert report.scan_metadata["safety_controls"]["executes_code"] is False


def test_semgrep_artifact_preserves_path_line_column():
    semgrep = json.dumps({
        "results": [
            {
                "check_id": "js.lang.security.eval",
                "path": "src/app.ts",
                "start": {"line": 12, "col": 5},
                "end": {"line": 12, "col": 20},
                "extra": {"severity": "ERROR", "message": "eval found", "lines": "eval(user)"},
            }
        ]
    })

    report = analyze_static_artifacts(semgrep_json=semgrep, project_name="Demo")

    assert report is not None
    finding = report.findings[0]
    assert finding.affected_file == "src/app.ts"
    assert finding.affected_line == 12
    assert finding.affected_column == 5
    assert finding.end_line == 12


def test_finding_model_accepts_exact_location_fields():
    finding = Finding(
        id="f-1",
        module="api",
        severity="high",
        title="Exact location",
        description="desc",
        affected_file="api/routes.ts",
        affected_line=7,
        affected_column=3,
        end_line=8,
        confidence="high",
        source="test",
        category="test",
        business_impact="impact",
        developer_explanation="explain",
        recommendation="fix",
        paid_review_recommended=True,
    )
    dumped = finding.model_dump(mode="json")
    assert dumped["affected_file"] == "api/routes.ts"
    assert dumped["affected_line"] == 7
    assert dumped["affected_column"] == 3
    assert dumped["end_line"] == 8
