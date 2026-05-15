from fastapi import APIRouter, HTTPException

from app.models.schemas import OwnershipChallenge, OwnershipChallengeCreate, OwnershipVerifyRequest, OwnershipVerifyResponse, ScanPolicyResponse
from app.services.ownership import create_challenge, scan_policy, verify_challenge

router = APIRouter(prefix="/ownership", tags=["ownership-abuse-prevention"])


@router.get("/policy", response_model=ScanPolicyResponse)
def get_scan_policy():
    return scan_policy()


@router.get("/methods")
def get_verification_methods():
    return {
        "methods": [
            {
                "id": "well_known",
                "name": "Well-known file verification",
                "recommended_for": "Fast local/staging verification",
                "what_user_does": "Upload /.well-known/web3guard-verify.txt with the generated token.",
            },
            {
                "id": "dns_txt",
                "name": "DNS TXT verification",
                "recommended_for": "Production domain ownership proof",
                "what_user_does": "Add _web3guard.yourdomain.com TXT record with the generated token.",
            },
        ],
        "safety_note": "Verification proves control of a domain for future owner-approved workflows. It is not an audit certificate.",
    }


@router.post("/challenge", response_model=OwnershipChallenge)
def start_ownership_challenge(payload: OwnershipChallengeCreate):
    try:
        return create_challenge(
            website_url=payload.website_url,
            method=payload.method,
            project_name=payload.project_name,
            contact_email=str(payload.contact_email) if payload.contact_email else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/verify", response_model=OwnershipVerifyResponse)
async def verify_ownership_challenge(payload: OwnershipVerifyRequest):
    try:
        return await verify_challenge(
            challenge_id=payload.challenge_id,
            website_url=payload.website_url,
            method=payload.method,
            token=payload.token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
