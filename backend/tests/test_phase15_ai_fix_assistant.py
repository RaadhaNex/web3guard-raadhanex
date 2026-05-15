from fastapi.testclient import TestClient

from main import app
from app.models.schemas import AIFixAssistantRequest, Finding
from app.services.ai_fix_assistant import fix_assistant_status, redact_sensitive_code, suggest_ai_fix

client = TestClient(app)


def sample_finding() -> dict:
    return {
        "id": "finding-reentrancy-1",
        "module": "contract",
        "severity": "high",
        "title": "External call before state update can enable reentrancy",
        "description": "Withdraw sends ETH before updating balance.",
        "affected_line": 10,
        "affected_function": "withdraw",
        "affected_code": "msg.sender.call{value: amount}(\"\"); balances[msg.sender] -= amount;",
        "confidence": "high",
        "source": "Rule Engine",
        "category": "reentrancy",
        "business_impact": "Funds may be drained by a malicious receiver if the pattern is exploitable.",
        "developer_explanation": "State should be updated before external calls.",
        "recommendation": "Use checks-effects-interactions and add a reentrancy regression test.",
        "paid_review_recommended": True,
    }


def test_phase15_status_is_real_only_safe_by_default():
    status = fix_assistant_status()
    assert status["phase"] == "Phase 15 - Real AI Fix Assistant"
    assert status["auto_apply_allowed"] is False
    assert "No automatic production code modification" in status["blocked_claims"]
    assert status["mode"] in {"safe_fallback", "provider"}


def test_phase15_endpoint_requires_real_only_acknowledgement():
    response = client.post("/ai/fix-assistant/suggest", json={
        "finding": sample_finding(),
        "include_code": False,
        "privacy_acknowledged": False,
        "real_only_acknowledged": False,
    })
    assert response.status_code == 400
    assert "Real-only" in response.json()["detail"]


def test_phase15_fallback_suggests_safe_strategy_without_auto_apply():
    response = client.post("/ai/fix-assistant/suggest", json={
        "finding": sample_finding(),
        "preferred_language": "Hinglish",
        "include_code": True,
        "privacy_acknowledged": False,
        "real_only_acknowledged": True,
        "code_context": "PRIVATE_KEY=0x" + "a" * 64 + "\ncontract A{}",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"fallback", "provider_error", "provider_success"}
    assert data["auto_apply_allowed"] is False
    assert data["code_was_sent_to_provider"] is False
    assert "reentrancy" in (data["safe_patch_strategy"] + data["summary"]).lower()
    assert data["test_suggestions"]
    assert "guaranteed" not in data["summary"].lower()


def test_phase15_secret_redaction_detects_private_key_like_values():
    code = "PRIVATE_KEY=0x" + "b" * 64 + "\nAPI_KEY=sk-test-long-token-value-1234567890"
    redacted, changed, flags = redact_sensitive_code(code)
    assert changed is True
    assert "REDACTED" in redacted
    assert flags


def test_phase15_service_fallback_for_tx_origin_finding():
    finding = Finding(**{**sample_finding(), "title": "tx.origin authorization risk", "recommendation": "Use msg.sender access control."})
    payload = AIFixAssistantRequest(finding=finding, preferred_language="English", real_only_acknowledged=True)
    import asyncio
    suggestion = asyncio.run(suggest_ai_fix(payload))
    assert suggestion.auto_apply_allowed is False
    assert "msg.sender" in suggestion.safe_patch_strategy or "msg.sender" in suggestion.fixed_code_snippet
