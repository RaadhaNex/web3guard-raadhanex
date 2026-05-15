#!/usr/bin/env python3
"""Web3Guard AI by RAADHANEX GitHub Action scan helper.

Real-only rules:
- Does not execute contracts.
- Does not install project dependencies.
- Does not collect private keys or seed phrases.
- Sends selected Solidity files to your configured Web3Guard backend API.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = os.environ.get("WEB3GUARD_API_BASE_URL", "").rstrip("/")
API_KEY = os.environ.get("WEB3GUARD_API_KEY", "")
FAIL_ON = os.environ.get("WEB3GUARD_FAIL_ON", "critical").lower()
PATTERNS = ["contracts/**/*.sol", "src/**/*.sol", "**/*.sol"]
MAX_FILES = int(os.environ.get("WEB3GUARD_MAX_FILES", "20"))
MAX_BYTES = int(os.environ.get("WEB3GUARD_MAX_FILE_BYTES", "180000"))
SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def collect_files() -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()
    for pattern in PATTERNS:
        for raw in glob.glob(pattern, recursive=True):
            path = Path(raw)
            key = str(path.resolve())
            if not path.is_file() or key in seen:
                continue
            if path.stat().st_size > MAX_BYTES:
                print(f"::warning::Skipping large file {path} ({path.stat().st_size} bytes)")
                continue
            seen.add(key)
            found.append(path)
            if len(found) >= MAX_FILES:
                return found
    return found


def api_audit(path: Path) -> dict:
    if not API_BASE or not API_KEY:
        raise RuntimeError("WEB3GUARD_API_BASE_URL and WEB3GUARD_API_KEY secrets are required.")
    payload = {
        "project_name": f"GitHub Action: {path}",
        "solidity_code": path.read_text(encoding="utf-8", errors="ignore"),
        "real_only_acknowledged": True,
    }
    req = urllib.request.Request(
        f"{API_BASE}/api/v1/audit",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Web3Guard-API-Key": API_KEY},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Web3Guard API failed for {path}: HTTP {exc.code} {body}") from exc


def main() -> int:
    files = collect_files()
    if not files:
        print("No Solidity files found. Nothing to scan.")
        return 0
    threshold = SEVERITY_ORDER.get(FAIL_ON, 4)
    should_fail = False
    summary: list[dict] = []
    for path in files:
        result = api_audit(path)
        findings = result.get("result", {}).get("findings", [])
        score = result.get("result", {}).get("module_score", {}).get("score")
        worst = "info"
        for finding in findings:
            sev = str(finding.get("severity", "info")).lower()
            if SEVERITY_ORDER.get(sev, 0) > SEVERITY_ORDER.get(worst, 0):
                worst = sev
            if SEVERITY_ORDER.get(sev, 0) >= threshold:
                should_fail = True
        summary.append({"file": str(path), "score": score, "findings": len(findings), "worst": worst})
        print(f"{path}: score={score} findings={len(findings)} worst={worst}")
    Path("web3guard-report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if should_fail:
        print(f"::error::Web3Guard found findings at or above threshold: {FAIL_ON}")
        return 1
    print("Web3Guard CI scan completed without blocking findings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
