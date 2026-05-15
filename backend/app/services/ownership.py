import hashlib
import json
import secrets
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import settings
from app.core.security import validate_public_http_url
from app.models.schemas import OwnershipChallenge, OwnershipVerifyResponse

CHALLENGE_TTL_HOURS = 24
VERIFY_PATH = "/.well-known/web3guard-verify.txt"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _storage_path() -> Path:
    path = Path(settings.ownership_challenges_file)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / Path(settings.ownership_challenges_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return path


def _host(url: str) -> str:
    safe_url = validate_public_http_url(url)
    parsed = urlparse(safe_url)
    if not parsed.hostname:
        raise ValueError("Website hostname is required")
    return parsed.hostname.lower()


def _base_origin(url: str) -> str:
    safe_url = validate_public_http_url(url)
    parsed = urlparse(safe_url)
    scheme = parsed.scheme
    host = parsed.netloc
    return f"{scheme}://{host}"


def _challenge_id(host: str, token: str) -> str:
    digest = hashlib.sha256(f"{host}:{token}".encode("utf-8")).hexdigest()[:18]
    return f"W3G-OWN-{digest.upper()}"


def _record(challenge: OwnershipChallenge) -> dict:
    return challenge.model_dump(mode="json")


def _read_all() -> list[dict]:
    path = _storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _write_all(records: list[dict]) -> None:
    path = _storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in records) + ("\n" if records else ""), encoding="utf-8")


def save_challenge(challenge: OwnershipChallenge) -> None:
    records = _read_all()
    records.append(_record(challenge))
    _write_all(records)


def get_challenge(challenge_id: str) -> OwnershipChallenge | None:
    for item in reversed(_read_all()):
        if item.get("id") == challenge_id:
            return OwnershipChallenge(**item)
    return None


def update_challenge(challenge: OwnershipChallenge) -> None:
    records = _read_all()
    updated = False
    for idx, item in enumerate(records):
        if item.get("id") == challenge.id:
            records[idx] = _record(challenge)
            updated = True
    if not updated:
        records.append(_record(challenge))
    _write_all(records)


def create_challenge(*, website_url: str, method: str, project_name: str | None = None, contact_email: str | None = None) -> OwnershipChallenge:
    safe_url = validate_public_http_url(website_url)
    host = _host(safe_url)
    token = f"web3guard-raadhanex-verify-{secrets.token_urlsafe(28)}"
    challenge_id = _challenge_id(host, token)
    created_at = _now()
    expires_at = created_at + timedelta(hours=CHALLENGE_TTL_HOURS)
    origin = _base_origin(safe_url)
    dns_txt_name = f"_web3guard.{host}"
    well_known_url = urljoin(origin, VERIFY_PATH)

    if method == "dns_txt":
        instructions = [
            f"Add this DNS TXT record name: {dns_txt_name}",
            f"TXT value: {token}",
            "Wait for DNS propagation, then click Verify.",
            "Keep the TXT record until your owner-approved review is complete.",
        ]
    else:
        instructions = [
            f"Create this public file: {VERIFY_PATH}",
            f"Put exactly this token in the file: {token}",
            f"The scanner will fetch: {well_known_url}",
            "Remove the file after owner-approved review if you want.",
        ]

    challenge = OwnershipChallenge(
        id=challenge_id,
        created_at=created_at,
        expires_at=expires_at,
        project_name=project_name,
        website_url=safe_url,
        normalized_host=host,
        method=method,  # type: ignore[arg-type]
        token=token,
        status="pending",
        dns_txt_name=dns_txt_name,
        dns_txt_value=token,
        well_known_url=well_known_url,
        well_known_path=VERIFY_PATH,
        instructions=instructions,
        evidence={"contact_email": contact_email} if contact_email else {},
    )
    save_challenge(challenge)
    return challenge


def _dns_txt_values(host: str) -> list[str]:
    # Python stdlib has no direct TXT resolver. Try dnspython if available; otherwise return helpful evidence.
    try:
        import dns.resolver  # type: ignore
    except Exception:
        return []
    values: list[str] = []
    try:
        answers = dns.resolver.resolve(host, "TXT")
    except Exception:
        return []
    for answer in answers:
        for text in answer.strings:
            values.append(text.decode("utf-8", errors="replace"))
    return values


async def _check_well_known(url: str, token: str) -> tuple[bool, dict]:
    origin = _base_origin(url)
    target = urljoin(origin, VERIFY_PATH)
    safe_target = validate_public_http_url(target)
    timeout = httpx.Timeout(settings.website_scan_timeout_seconds)
    evidence: dict = {"method": "well_known", "url": safe_target}
    headers = {"User-Agent": settings.website_scanner_user_agent}
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=False) as client:
            response = await client.get(safe_target)
            evidence["status_code"] = response.status_code
            evidence["content_type"] = response.headers.get("content-type", "")
            text = response.text[:1000]
            evidence["body_preview"] = text[:120]
            return token in text, evidence
    except Exception as exc:
        evidence["error"] = str(exc)
        return False, evidence


def _check_dns_txt(challenge: OwnershipChallenge, token: str) -> tuple[bool, dict]:
    txt_name = challenge.dns_txt_name or f"_web3guard.{challenge.normalized_host}"
    values = _dns_txt_values(txt_name)
    evidence = {"method": "dns_txt", "txt_name": txt_name, "txt_values_found": len(values), "resolver_available": bool(values)}
    evidence["values_preview"] = [value[:80] for value in values[:5]]
    return any(token in value for value in values), evidence


async def verify_challenge(*, challenge_id: str, website_url: str, method: str, token: str) -> OwnershipVerifyResponse:
    challenge = get_challenge(challenge_id)
    checked_at = _now()
    if challenge is None:
        return OwnershipVerifyResponse(
            challenge_id=challenge_id,
            status="failed",
            verified=False,
            checked_at=checked_at,
            evidence={"error": "Challenge not found"},
            next_steps=["Create a new ownership challenge from the ownership verification page."],
        )

    if checked_at > challenge.expires_at:
        challenge.status = "expired"
        challenge.last_checked_at = checked_at
        challenge.evidence = {"error": "Challenge expired", **challenge.evidence}
        update_challenge(challenge)
        return OwnershipVerifyResponse(
            challenge_id=challenge.id,
            status="expired",
            verified=False,
            checked_at=checked_at,
            evidence={"error": "Challenge expired"},
            next_steps=["Create a fresh challenge and publish the new token."],
        )

    requested_host = _host(website_url)
    if requested_host != challenge.normalized_host:
        return OwnershipVerifyResponse(
            challenge_id=challenge.id,
            status="failed",
            verified=False,
            checked_at=checked_at,
            evidence={"error": "Website host does not match original challenge", "expected_host": challenge.normalized_host, "received_host": requested_host},
            next_steps=["Use the same website URL/host that was used to create the challenge."],
        )

    if token != challenge.token or method != challenge.method:
        return OwnershipVerifyResponse(
            challenge_id=challenge.id,
            status="failed",
            verified=False,
            checked_at=checked_at,
            evidence={"error": "Challenge token or method mismatch"},
            next_steps=["Copy the exact token and verification method from the challenge response."],
        )

    if method == "dns_txt":
        verified, evidence = _check_dns_txt(challenge, token)
        if not evidence.get("resolver_available"):
            evidence["note"] = "DNS TXT runtime resolver is optional in MVP. If this fails locally, use well-known file verification or install dnspython later."
    else:
        verified, evidence = await _check_well_known(website_url, token)

    challenge.status = "verified" if verified else "failed"
    challenge.last_checked_at = checked_at
    challenge.evidence = evidence
    update_challenge(challenge)

    return OwnershipVerifyResponse(
        challenge_id=challenge.id,
        status=challenge.status,
        verified=verified,
        checked_at=checked_at,
        evidence=evidence,
        next_steps=(
            [
                "You can use this verification evidence for future owner-approved deep scan workflows.",
                "MVP still keeps website scans passive-only and does not run exploit payloads.",
            ]
            if verified
            else [
                "Confirm the token is publicly reachable exactly as provided.",
                "Check DNS propagation or hosting route configuration.",
                "Do not share private keys, seed phrases, admin credentials, or server secrets.",
            ]
        ),
    )


def scan_policy() -> dict:
    return {
        "mode": "preliminary_passive_checklist_code_submitted",
        "allowed_methods": ["Solidity/code submitted by user", "Passive public website HEAD/GET", "Checklist review", "Owner-verification challenge"],
        "blocked_actions": [
            "Exploit automation",
            "Credential testing",
            "Login bypass attempts",
            "Brute force crawling or wordlists",
            "Destructive testing",
            "Private/internal network scanning",
            "Payload spraying",
            "Collection of seed phrases, private keys, or admin passwords",
        ],
        "ownership_required_for": ["Future deep website scan", "Future repo-connected scan", "Future authenticated API review", "Future monitoring setup"],
        "consent_text": "I own this project or have authorization to run this preliminary passive/checklist/code-submitted review.",
        "private_network_blocking": True,
        "deep_scan_available": False,
        "note": "Phase 5.9 adds ownership verification architecture and abuse prevention. MVP remains passive/checklist/code-submitted only.",
    }
