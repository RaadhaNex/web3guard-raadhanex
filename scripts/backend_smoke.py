"""Mega Phase E backend smoke test.
Run from project root or backend folder. This uses FastAPI TestClient, so no live server is required.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make this script work whether it is called from backend/ or project root.
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

checks = [
    ("GET", "/health", None, 200),
    ("GET", "/health/readiness", None, 200),
    ("GET", "/qa/status", None, 200),
    ("GET", "/qa/runbook", None, 200),
    ("GET", "/launch/pack", None, 200),
    ("GET", "/db/status", None, 200),
    ("GET", "/workspace/status", None, 200),
    ("GET", "/securescore/status", None, 200),
    ("GET", "/securescore/overview?user_id=local-demo-user", None, 200),
    ("GET", "/findings?user_id=local-demo-user", None, 200),
    ("GET", "/payments/status", None, 200),
    ("GET", "/subscriptions", None, 200),
    ("GET", "/dashboard/overview?user_id=local-demo-user", None, 200),
    ("GET", "/packages", None, 200),
    ("GET", "/scan/feature-status", None, 200),
    ("GET", "/scan/github/status", None, 200),
    ("GET", "/scan/contract-address/status", None, 200),
    ("GET", "/scan/static-analysis/status", None, 200),
    ("GET", "/scan/deep-analysis/status", None, 200),
    ("GET", "/scan/permission-map/status", None, 200),
    ("GET", "/ai/fix-assistant/status", None, 200),
    ("GET", "/monitoring/status", None, 200),
    ("GET", "/monitoring/dashboard", None, 200),
    ("GET", "/threat-intel/status", None, 200),
    ("GET", "/threat-intel/feed?project_type=Token&tags=approval", None, 200),
    ("GET", "/bug-bounty/status", None, 200),
    ("GET", "/bug-bounty/dashboard", None, 200),
    ("GET", "/registry/status", None, 200),
    ("GET", "/registry/publications", None, 200),
    ("GET", "/developer-api/status", None, 200),
    ("GET", "/developer-api/keys?user_id=local-demo-user", None, 200),
    ("GET", "/cicd/status", None, 200),
    ("POST", "/cicd/template", {"api_base_url":"http://localhost:8000", "fail_on":"critical", "real_only_acknowledged": True}, 200),
    ("POST", "/cicd/validate", {"config_text":"name: Web3Guard\non: [pull_request]\njobs:\n  scan:\n    steps:\n      - uses: actions/checkout@v4", "real_only_acknowledged": True}, 200),
    ("GET", "/learning/status", None, 200),
    ("GET", "/learning/lessons", None, 200),
    ("POST", "/learning/progress", {"lesson_id":"reentrancy-basics", "status":"completed", "real_only_acknowledged": True}, 200),
    ("POST", "/scan/contract", {"solidity_code":"// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20; contract T { address public owner; constructor(){owner=msg.sender;} function withdraw() external { require(msg.sender==owner); payable(owner).call{value: address(this).balance}(\"\"); } }", "project_name":"Smoke", "authorization_confirmed": True}, 200),
    ("POST", "/scan/static-analysis", {"solidity_code":"// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20; contract T { function x() external {} }", "project_name":"Smoke Static", "authorization_confirmed": True, "real_only_acknowledged": True}, 200),
    ("POST", "/scan/deep-analysis", {"solidity_code":"// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20; contract T { function x() external {} }", "project_name":"Smoke Deep", "authorization_confirmed": True, "real_only_acknowledged": True}, 200),
    ("POST", "/scan/permission-map", {"solidity_code":"// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20; contract T { address public owner; modifier onlyOwner(){ require(msg.sender==owner); _; } function mint(address to,uint256 amount) external onlyOwner {} function upgradeTo(address impl) external onlyOwner {} }", "project_name":"Smoke Permission", "owner_address":"0x" + "a" * 40, "multisig_enabled": False, "timelock_enabled": False, "authorization_confirmed": True, "real_only_acknowledged": True}, 200),
    ("POST", "/monitoring/configs", {"project_name":"Smoke Monitor", "contract_address":"0x" + "b" * 40, "chain":"ethereum", "authorization_confirmed": True, "real_only_acknowledged": True}, 200),
    ("POST", "/threat-intel/admin/entries", {"title":"Smoke threat note", "category":"admin_opsec", "severity":"medium", "summary":"Manual smoke threat intelligence entry with real-only acknowledgement.", "affected_project_types":["Token"], "relevance_tags":["owner"], "real_only_acknowledged": True}, 200),
    ("POST", "/ai/fix-assistant/suggest", {"finding":{"id":"smoke-finding","module":"contract","severity":"high","title":"tx.origin authorization risk","description":"Authorization uses tx.origin.","confidence":"high","source":"Rule Engine","category":"access_control","business_impact":"Authorization can behave unexpectedly through intermediary contracts.","developer_explanation":"Use msg.sender or role-based access control instead of tx.origin.","recommendation":"Replace tx.origin checks with msg.sender/AccessControl and add tests.","paid_review_recommended":True},"preferred_language":"English","real_only_acknowledged":True}, 200),
    ("POST", "/scan/unified-url", {"website_url":"http://127.0.0.1", "project_name":"Smoke URL Safety Block", "authorization_confirmed": True, "real_only_acknowledged": True}, 400),
    ("POST", "/payment-intent", {"package_id":"quick-risk-report", "customer_name":"Smoke Tester", "customer_email":"smoke@example.com", "project_name":"Smoke"}, 200),
    ("GET", "/notifications/status", None, 200),
    ("POST", "/notifications/send", {"event_type":"critical_finding", "channels":["manual"], "title":"Smoke notification", "message":"Dry-run notification preview.", "severity":"high", "dry_run": True, "real_only_acknowledged": True}, 200),
    ("GET", "/compliance/status", None, 200),
    ("POST", "/compliance/scan", {"project_name":"Smoke Compliance", "jurisdictions":["general_web3","india_vda"], "collects_personal_data": True, "handles_payments_in_inr": True, "real_only_acknowledged": True}, 200),
    ("GET", "/cross-chain/status", None, 200),
    ("POST", "/cross-chain/scan", {"chain_family":"evm", "chains":["ethereum","polygon"], "source_code":"contract X { function lzReceive(bytes calldata payload) external {} function verify(bytes memory signature) external {} }", "real_only_acknowledged": True}, 200),
    ("GET", "/report/delivery-policy", None, 200),
]

failed = 0
for method, path, payload, expected in checks:
    response = client.request(method, path, json=payload) if payload is not None else client.request(method, path)
    ok = response.status_code == expected
    print(f"{'PASS' if ok else 'FAIL'} {method} {path} -> {response.status_code}")
    if not ok:
        failed += 1
        print(response.text[:500])

if failed:
    raise SystemExit(f"{failed} smoke checks failed")
print("All Mega Phase F backend smoke checks passed. The unified URL smoke case intentionally expects private-IP blocking.")
