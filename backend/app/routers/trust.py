import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["trust"])
DATA_DIR = Path("app/data")


def _load_json(name: str):
    path = DATA_DIR / name
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"Missing trust data file: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/trust-kit")
def trust_kit():
    content = _load_json("trust_content.json")
    return {
        "version": content["version"],
        "positioning": content["positioning"],
        "primary_disclaimer": content["primary_disclaimer"],
        "not_claimed": content["what_we_do_not_do"],
        "safe_scanning": content["scan_boundaries"],
        "company": content["company"],
        "product": content["product"],
    }


@router.get("/trust/policy")
def trust_policy():
    return _load_json("trust_content.json")


@router.get("/trust/methodology")
def methodology():
    return {
        "module_weights": {
            "smart_contract": 35,
            "website_surface": 15,
            "dapp_frontend": 15,
            "api_backend": 15,
            "wallet_flow": 10,
            "admin_opsec": 10,
        },
        "penalties": {
            "critical": -25,
            "high": -15,
            "medium": -8,
            "low": -3,
            "info": -1,
        },
        "confidence_multiplier": {
            "high": 1.0,
            "medium": 0.7,
            "low": 0.4,
        },
        "risk_labels": [
            {"range": "90-100", "label": "Launch Ready with Minor Notes"},
            {"range": "75-89", "label": "Low Risk, Fix Recommended"},
            {"range": "60-74", "label": "Medium Risk, Fix Before Launch"},
            {"range": "40-59", "label": "High Risk, Manual Review Recommended"},
            {"range": "0-39", "label": "Critical Launch Risk"},
        ],
        "disclaimer": "Scoring is preliminary readiness scoring, not a certified audit score.",
    }


@router.get("/trust/scope-refund")
def scope_refund_policy():
    content = _load_json("trust_content.json")
    return {
        "manual_review_scope": content["manual_review_scope"],
        "refund_scope_rules": content["refund_scope_rules"],
        "disclaimer": content["primary_disclaimer"],
    }


@router.get("/sample-reports")
def sample_reports():
    return {"reports": _load_json("sample_reports.json")}


@router.get("/sample-reports/{report_id}")
def sample_report_detail(report_id: str):
    reports = _load_json("sample_reports.json")
    for report in reports:
        if report["id"] == report_id:
            return report
    raise HTTPException(status_code=404, detail="Sample report not found")
