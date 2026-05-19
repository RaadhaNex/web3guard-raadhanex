#!/usr/bin/env python3
"""Phase 25 launch hardening helper.

Runs lightweight, read-only checks against the deployed/backend URL. It does not
perform active security scanning and it never sends secrets, private keys, seed
phrases, mnemonics, or wallet-signing requests.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


SAFE_PATHS = ("/", "/health")


@dataclass
class CheckResult:
    path: str
    status: str
    http_status: int | None
    latency_ms: int | None
    note: str


def read_url(url: str, timeout: float) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Web3Guard-Phase25-Launch-Hardening/1.0",
            "Accept": "application/json,text/plain,*/*",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - user-supplied deployment health URL only
        return response.status, response.read(4096)


def check_path(base_url: str, path: str, timeout: float) -> CheckResult:
    url = f"{base_url.rstrip('/')}{path}"
    started = time.perf_counter()
    try:
        http_status, body = read_url(url, timeout)
        latency_ms = int((time.perf_counter() - started) * 1000)
        status = "PASS" if 200 <= http_status < 400 else "MANUAL"
        note = "reachable"
        if body:
            try:
                parsed: Any = json.loads(body.decode("utf-8", errors="replace"))
                if isinstance(parsed, dict):
                    note = ", ".join(list(parsed.keys())[:6]) or note
            except json.JSONDecodeError:
                note = body.decode("utf-8", errors="replace")[:120].strip() or note
        return CheckResult(path, status, http_status, latency_ms, note)
    except urllib.error.HTTPError as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return CheckResult(path, "MANUAL", exc.code, latency_ms, f"HTTP error: {exc.reason}")
    except Exception as exc:  # noqa: BLE001 - CLI diagnostics should report all safe failures
        latency_ms = int((time.perf_counter() - started) * 1000)
        return CheckResult(path, "NOT ASSESSED", None, latency_ms, str(exc))


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only backend latency and health check for Phase 25.")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000", help="Backend base URL, for example your Render URL.")
    parser.add_argument("--timeout", type=float, default=12.0, help="Timeout per safe GET request in seconds.")
    args = parser.parse_args()

    print("Web3Guard Phase 25 Launch Hardening Check")
    print("Read-only paths only. No active scanning. No wallet signing. No secrets requested.\n")

    results = [check_path(args.backend_url, path, args.timeout) for path in SAFE_PATHS]
    for item in results:
        latency = f"{item.latency_ms}ms" if item.latency_ms is not None else "n/a"
        http_status = item.http_status if item.http_status is not None else "n/a"
        print(f"{item.status:12} {item.path:8} http={http_status} latency={latency} note={item.note}")

    if any(item.status == "NOT ASSESSED" for item in results):
        return 2
    if any(item.status == "MANUAL" for item in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
