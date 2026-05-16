from __future__ import annotations

import hashlib
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import NotificationPreferenceCreate, NotificationSendRequest
from app.services.mega_phase_e_store import append_jsonl, new_id, now_iso, read_jsonl, storage_path

NOTIFICATIONS_REAL_ONLY_NOTE = (
    "Notification records are real, but delivery is only marked sent when a configured provider confirms it. "
    "If SMTP/Telegram/Discord/WhatsApp is disabled or dry_run=true, the event is saved as preview/manual_required."
)


def notification_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.0",
        "enabled": settings.notifications_enabled,
        "providers": {
            "smtp_email": {"enabled": settings.smtp_enabled, "configured": bool(settings.smtp_host and settings.smtp_from_email)},
            "telegram": {"enabled": settings.telegram_enabled, "configured": bool(settings.telegram_bot_token)},
            "discord": {"enabled": settings.discord_enabled, "configured": bool(settings.discord_webhook_url)},
            "whatsapp": {"enabled": settings.whatsapp_enabled, "provider": settings.whatsapp_provider, "configured": bool(settings.whatsapp_api_token and settings.whatsapp_from_number)},
        },
        "delivery_modes": ["dry_run_preview", "manual_required", "provider_sent"],
        "real_only_note": NOTIFICATIONS_REAL_ONLY_NOTE,
    }


def _prefs_path() -> Path:
    return storage_path(settings.notification_preferences_file)


def _events_path() -> Path:
    return storage_path(settings.notification_events_file)


def _logs_path() -> Path:
    return storage_path(settings.notification_logs_file)


def create_preference(payload: NotificationPreferenceCreate, user_id: str) -> dict[str, Any]:
    row = payload.model_dump(mode="json")
    row.update({"id": new_id("notif_pref"), "user_id": user_id, "created_at": now_iso(), "updated_at": now_iso(), "real_only_note": NOTIFICATIONS_REAL_ONLY_NOTE})
    append_jsonl(_prefs_path(), row)
    return row


def list_preferences(user_id: str | None = None) -> list[dict[str, Any]]:
    rows = read_jsonl(_prefs_path())
    if user_id:
        rows = [r for r in rows if r.get("user_id") == user_id]
    return sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)


def list_events(limit: int = 100) -> list[dict[str, Any]]:
    return sorted(read_jsonl(_events_path()), key=lambda r: r.get("created_at", ""), reverse=True)[:limit]


def _hash_payload(title: str, message: str) -> str:
    return hashlib.sha256(f"{title}\n{message}".encode("utf-8")).hexdigest()


def _send_email(payload: NotificationSendRequest) -> tuple[str, str]:
    if not (settings.smtp_enabled and settings.smtp_host and settings.smtp_from_email):
        return "manual_required", "SMTP provider not configured."
    if not payload.recipient_email:
        return "manual_required", "Recipient email missing."
    msg = EmailMessage()
    msg["Subject"] = payload.title
    msg["From"] = settings.smtp_from_email
    msg["To"] = str(payload.recipient_email)
    msg.set_content(payload.message)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12) as smtp:
        smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(msg)
    return "provider_sent", "SMTP accepted message."


def _send_telegram(payload: NotificationSendRequest) -> tuple[str, str]:
    if not (settings.telegram_enabled and settings.telegram_bot_token):
        return "manual_required", "Telegram provider not configured."
    chat_id = payload.telegram_chat_id or settings.telegram_default_chat_id
    if not chat_id:
        return "manual_required", "Telegram chat_id missing."
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    with httpx.Client(timeout=12) as client:
        resp = client.post(url, json={"chat_id": chat_id, "text": f"{payload.title}\n\n{payload.message}"})
    if resp.status_code >= 400:
        return "provider_error", f"Telegram error {resp.status_code}: {resp.text[:200]}"
    return "provider_sent", "Telegram API accepted message."


def _send_discord(payload: NotificationSendRequest) -> tuple[str, str]:
    webhook = payload.discord_webhook_url or settings.discord_webhook_url
    if not (settings.discord_enabled and webhook):
        return "manual_required", "Discord webhook provider not configured."
    with httpx.Client(timeout=12) as client:
        resp = client.post(webhook, json={"content": f"**{payload.title}**\n{payload.message}"})
    if resp.status_code >= 400:
        return "provider_error", f"Discord error {resp.status_code}: {resp.text[:200]}"
    return "provider_sent", "Discord webhook accepted message."


def _send_whatsapp(payload: NotificationSendRequest) -> tuple[str, str]:
    if not settings.whatsapp_enabled:
        return "manual_required", "WhatsApp provider not enabled."
    # Provider-specific implementations require Twilio/Meta account templates and sender approval.
    return "manual_required", "WhatsApp provider configured flag exists, but template/send adapter must be completed with Twilio/Meta credentials and approved templates."


def send_notification(payload: NotificationSendRequest, user_id: str) -> dict[str, Any]:
    event_id = new_id("notif_evt")
    results: list[dict[str, Any]] = []
    if payload.dry_run or not settings.notifications_enabled:
        for channel in payload.channels:
            results.append({"channel": channel, "status": "dry_run_preview", "detail": "No provider call made."})
    else:
        for channel in payload.channels:
            try:
                if channel == "email":
                    status, detail = _send_email(payload)
                elif channel == "telegram":
                    status, detail = _send_telegram(payload)
                elif channel == "discord":
                    status, detail = _send_discord(payload)
                elif channel == "whatsapp":
                    status, detail = _send_whatsapp(payload)
                else:
                    status, detail = "manual_required", "Manual notification record only."
            except Exception as exc:
                status, detail = "provider_error", str(exc)[:300]
            results.append({"channel": channel, "status": status, "detail": detail})
    row = payload.model_dump(mode="json")
    row.update({"id": event_id, "user_id": user_id, "created_at": now_iso(), "payload_hash": _hash_payload(payload.title, payload.message), "delivery_results": results, "real_only_note": NOTIFICATIONS_REAL_ONLY_NOTE})
    append_jsonl(_events_path(), row)
    append_jsonl(_logs_path(), {"id": new_id("notif_log"), "event_id": event_id, "created_at": now_iso(), "results": results})
    return row
