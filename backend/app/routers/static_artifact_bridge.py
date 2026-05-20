from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.services.static_analysis_artifacts import analyze_static_artifacts, static_artifact_status

router = APIRouter(prefix="/static-artifact", tags=["Static Analysis Artifact Bridge"])


class StaticArtifactParseRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=160)
    slither_json: str | None = Field(default=None, max_length=1000000)
    semgrep_json: str | None = Field(default=None, max_length=1000000)
    aderyn_json: str | None = Field(default=None, max_length=1000000)
    real_only_acknowledged: bool = True


@router.get("/status")
def status() -> dict:
    return static_artifact_status()


@router.post("/parse")
def parse_artifacts(payload: StaticArtifactParseRequest) -> dict:
    report = analyze_static_artifacts(
        slither_json=payload.slither_json,
        semgrep_json=payload.semgrep_json,
        aderyn_json=payload.aderyn_json,
        project_name=payload.project_name,
    )
    if report is None:
        return {
            "ok": False,
            "state": "Not Assessed",
            "message": "No Slither/Semgrep/Aderyn JSON artifact was supplied.",
            "blocked_claims": ["No fake static-analysis output", "No certified audit claim"],
        }
    return {
        "ok": True,
        "state": "Assessed" if report.findings else "Manual Review Required",
        "report_id": report.report_id,
        "score": report.module_score.score if report.module_score.assessed else None,
        "risk_label": report.module_score.risk_label,
        "findings_count": len([finding for finding in report.findings if finding.category != "tool_status"]),
        "status_message_count": len([finding for finding in report.findings if finding.category == "tool_status"]),
        "severity_breakdown": report.severity_breakdown,
        "scan_metadata": report.scan_metadata,
        "findings": [finding.model_dump(mode="json") for finding in report.findings],
        "real_only_rule": "Parsed from supplied JSON artifact only. This endpoint does not fake backend tool execution or certified audit status.",
    }
