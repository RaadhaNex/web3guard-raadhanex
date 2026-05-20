from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.schemas import UnifiedUrlScanRequest
from app.services.detection_expansion import build_detection_expansion_package

router = APIRouter(prefix="/detection-expansion", tags=["Detection expansion phases 60-67"])


class DetectionExpansionPreviewRequest(BaseModel):
    website_url: str = Field(min_length=8, max_length=2048)
    project_name: str | None = Field(default=None, max_length=160)
    project_type: str | None = Field(default="Full Web3 Startup", max_length=80)
    chain: str | None = Field(default="Web only", max_length=80)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


@router.get("/status")
def status():
    return {
        "ok": True,
        "phase_range": "60-67",
        "engine_version": "deep-detection-expansion-v1.0",
        "purpose": "Increase bug discovery depth without fake findings: deep crawler, GitHub deep risk, API/auth evidence, smart-contract/static runner readiness, wallet decoder, business logic builder, DeFi artifacts, false-positive learning.",
        "real_only_rule": "Evidence found becomes a finding; missing proof stays Not Assessed or Manual Review Required.",
        "safe_scope": [
            "Same-origin bounded passive crawl only.",
            "No exploit automation, brute force, credential stuffing, DoS, wallet signing, or private-key collection.",
            "Business logic and DeFi findings require supplied context/artifacts or manual triage.",
        ],
        "phases": {
            "60": "Deep Website Crawler + JS/API Endpoint Discovery",
            "61": "GitHub Repo Deep Risk Scanner",
            "62": "OpenAPI/Auth Evidence API Tester",
            "63": "Smart Contract Compile + Static Tool Runner Hardening",
            "64": "Wallet Transaction/Signature Risk Decoder",
            "65": "Business Logic + Payment Abuse Review Builder",
            "66": "DeFi Invariant/Simulation Artifact Analyzer",
            "67": "False Positive Learning + Accuracy Dashboard",
        },
    }


@router.post("/preview")
async def preview(payload: DetectionExpansionPreviewRequest):
    unified = UnifiedUrlScanRequest(
        website_url=payload.website_url,
        project_name=payload.project_name,
        project_type=payload.project_type,
        chain=payload.chain,
        authorization_confirmed=payload.authorization_confirmed,
        real_only_acknowledged=payload.real_only_acknowledged,
    )
    return await build_detection_expansion_package(website_url=payload.website_url, payload=unified)
