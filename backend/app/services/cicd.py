from __future__ import annotations

import re
from typing import Any

from app.core.config import settings
from app.models.schemas import CiConfigValidateRequest, CiTemplateRequest
from app.services.mega_phase_e_store import MEGA_PHASE_E_REAL_ONLY_NOTE

DEFAULT_WEB3GUARD_YML = """# Web3Guard AI by RAADHANEX CI configuration
# Real-only note: this config triggers your backend API; it does not fake scans.
api_base_url: https://your-backend.example.com
severity_threshold: critical
fail_on: critical
scan_mode: rule-engine
paths:
  - contracts/**/*.sol
  - src/**/*.sol
max_files: 20
"""

WORKFLOW_TEMPLATE = """name: Web3Guard AI Pre-Audit Scan

on:
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: write

jobs:
  web3guard-preaudit:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Run Web3Guard pre-audit scan
        env:
          WEB3GUARD_API_BASE_URL: ${{ secrets.WEB3GUARD_API_BASE_URL }}
          WEB3GUARD_API_KEY: ${{ secrets.WEB3GUARD_API_KEY }}
          WEB3GUARD_FAIL_ON: critical
        run: |
          python .github/web3guard/scan.py
"""

SCAN_SCRIPT = r'''#!/usr/bin/env python3
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
'''


def cicd_status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "1.0",
        "live": True,
        "real_only_note": MEGA_PHASE_E_REAL_ONLY_NOTE,
        "available_templates": ["github_action", "web3guard_yml", "scan_py"],
        "not_claimed": [
            "No fake CI run result is generated.",
            "No PR comment is posted until a real GitHub token/workflow is configured.",
            "No dependencies are installed or project code executed by the scan helper.",
            "The action calls the real /api/v1/audit endpoint with a real API key.",
        ],
        "manual_setup_required": [
            "Create a Web3Guard Developer API key with audit:start permission.",
            "Add WEB3GUARD_API_BASE_URL secret in GitHub repository settings.",
            "Add WEB3GUARD_API_KEY secret in GitHub repository settings.",
            "Copy .github/workflows/web3guard-preaudit.yml and .github/web3guard/scan.py to the target repo.",
        ],
    }


def render_template(payload: CiTemplateRequest) -> dict[str, Any]:
    api_base = (payload.api_base_url or settings.backend_url).rstrip("/")
    fail_on = payload.fail_on or "critical"
    workflow = WORKFLOW_TEMPLATE.replace("critical", fail_on)
    config = DEFAULT_WEB3GUARD_YML.replace("https://your-backend.example.com", api_base).replace("fail_on: critical", f"fail_on: {fail_on}").replace("severity_threshold: critical", f"severity_threshold: {fail_on}")
    return {
        "ok": True,
        "workflow_path": ".github/workflows/web3guard-preaudit.yml",
        "config_path": "web3guard.yml",
        "script_path": ".github/web3guard/scan.py",
        "workflow_yml": workflow,
        "web3guard_yml": config,
        "scan_py": SCAN_SCRIPT,
        "real_only_note": MEGA_PHASE_E_REAL_ONLY_NOTE,
    }


def validate_ci_config(payload: CiConfigValidateRequest) -> dict[str, Any]:
    text = payload.config_text or ""
    findings: list[dict[str, str]] = []
    if "WEB3GUARD_API_KEY" in text and "secrets.WEB3GUARD_API_KEY" not in text:
        findings.append({"severity": "high", "title": "Potential API key hardcoded", "recommendation": "Use GitHub Actions secrets instead of hardcoding API keys."})
    if "pull_request" not in text and "workflow_dispatch" not in text:
        findings.append({"severity": "low", "title": "No pull_request or manual trigger found", "recommendation": "Add pull_request and/or workflow_dispatch trigger."})
    if "actions/checkout" not in text:
        findings.append({"severity": "medium", "title": "Repository checkout step missing", "recommendation": "Add actions/checkout before scanning files."})
    if re.search(r"private[_-]?key\s*[:=]", text, re.I):
        findings.append({"severity": "critical", "title": "Private key-like value in CI config", "recommendation": "Remove private keys from CI config and rotate exposed secrets."})
    return {
        "ok": True,
        "valid": not any(f["severity"] in {"critical", "high"} for f in findings),
        "findings": findings,
        "real_only_note": "Validation is static text review only. It does not execute the workflow or call GitHub.",
    }
