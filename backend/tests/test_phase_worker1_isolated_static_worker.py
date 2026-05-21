import pytest

from app.core.config import settings
from app.services.isolated_static_worker import isolated_static_worker_status, run_isolated_static_worker_files


@pytest.mark.asyncio
async def test_isolated_static_worker_disabled_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "static_worker_enabled", False)
    monkeypatch.setattr(settings, "static_worker_auto_dispatch_enabled", False)
    monkeypatch.setattr(settings, "static_worker_url", None)
    monkeypatch.setattr(settings, "static_worker_token", None)

    result = await run_isolated_static_worker_files(
        [{"path": "src/Test.sol", "content": "pragma solidity ^0.8.20; contract Test {}"}],
        project_name="Test",
    )

    assert result is None


def test_isolated_static_worker_status_is_safe_by_default(monkeypatch):
    monkeypatch.setattr(settings, "static_worker_enabled", False)
    monkeypatch.setattr(settings, "static_worker_auto_dispatch_enabled", False)
    monkeypatch.setattr(settings, "static_worker_url", None)
    monkeypatch.setattr(settings, "static_worker_token", None)

    status = isolated_static_worker_status()

    assert status["configured"] is False
    assert status["will_auto_run"] is False
    assert status["main_backend_executes_tools"] is False
