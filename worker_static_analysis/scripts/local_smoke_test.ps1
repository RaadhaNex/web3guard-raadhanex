$body = @{
  project_name = "Worker Smoke Test"
  files = @(@{ path = "src/Test.sol"; content = "// SPDX-License-Identifier: MIT`npragma solidity ^0.8.20; contract Test { function bad() external view returns(address){ return tx.origin; } }" })
  tools = @("slither", "semgrep", "aderyn")
  authorization_confirmed = $true
  real_only_acknowledged = $true
} | ConvertTo-Json -Depth 6

Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8001/static-analysis/run" `
  -Headers @{ Authorization = "Bearer $env:STATIC_WORKER_TOKEN" } `
  -ContentType "application/json" `
  -Body $body
