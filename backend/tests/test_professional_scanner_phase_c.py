import json

from app.models.schemas import UnifiedUrlScanRequest
from app.services.formal_fuzz_artifacts import analyze_formal_fuzz_artifacts, parse_echidna_output, parse_foundry_output, parse_invariant_artifact


def test_foundry_text_failure_parses_professional_fields():
    raw = """
[FAIL. Reason: invariant_totalSupplyNeverExceedsCap violated]
test/Invariant.t.sol:42:13
Counterexample: calldata=0x1234
"""
    findings, status = parse_foundry_output(raw)
    assert status["state"] == "Assessed"
    assert len(findings) >= 1
    finding = findings[0]
    assert finding.source_tools == ["foundry"]
    assert finding.affected_file == "test/Invariant.t.sol"
    assert finding.affected_line == 42
    assert finding.fix
    assert finding.repro_steps


def test_echidna_json_counterexample_parses():
    raw = json.dumps({
        "tests": [
            {
                "name": "echidna_no_drain",
                "status": "falsified",
                "counterexample": [{"call": "withdraw()", "gas": 12345}],
                "file": "contracts/Vault.sol",
                "line": 88,
            }
        ]
    })
    findings, status = parse_echidna_output(raw)
    assert status["failure_count"] == 1
    assert findings[0].severity in {"critical", "high"}
    assert findings[0].source_tools == ["echidna"]
    assert findings[0].affected_file == "contracts/Vault.sol"


def test_invariant_artifact_failure_parses():
    raw = json.dumps({
        "invariants": [
            {
                "name": "protocol_never_insolvent",
                "passed": False,
                "severity": "critical",
                "evidence": "debt exceeds collateral after oracle update",
                "file": "src/Accounting.sol",
                "line": 120,
            }
        ]
    })
    findings, status = parse_invariant_artifact(raw)
    assert status["failure_count"] == 1
    assert findings[0].severity == "critical"
    assert findings[0].source_tools == ["invariant_artifact"]


def test_formal_fuzz_report_is_none_without_artifacts():
    assert analyze_formal_fuzz_artifacts(project_name="x") is None


def test_formal_fuzz_report_summarizes_all_artifacts():
    report = analyze_formal_fuzz_artifacts(
        foundry_test_output="FAIL invariant_x contracts/X.sol:4:1",
        echidna_output_json=json.dumps({"tests": [{"property": "echidna_y", "status": "failed"}]}),
        invariant_artifact_json=json.dumps({"name": "z", "passed": False}),
        project_name="Phase C",
    )
    assert report is not None
    assert report.module_score.module == "deep_analysis"
    assert len(report.findings) >= 3
    assert report.scan_metadata["formal_fuzz_summary"]["total_findings"] >= 3
