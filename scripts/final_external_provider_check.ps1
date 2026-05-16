param(
  [string]$FrontendUrl = "https://web3guard-raadhanex.vercel.app",
  [string]$BackendUrl = "https://web3guard-raadhanex-backend.onrender.com"
)

Write-Host "=== Web3Guard Final External Provider Check ===" -ForegroundColor Cyan
Write-Host "Frontend: $FrontendUrl"
Write-Host "Backend : $BackendUrl"
Write-Host ""

$endpoints = @(
  "$BackendUrl/health",
  "$BackendUrl/health/readiness",
  "$BackendUrl/payments/status",
  "$BackendUrl/final-qa/completion-summary",
  "$BackendUrl/final-qa/external-providers",
  "$BackendUrl/final-qa/remaining-work"
)

foreach ($url in $endpoints) {
  try {
    $res = Invoke-WebRequest -Uri $url -Method GET -UseBasicParsing -TimeoutSec 30
    Write-Host "OK  $($res.StatusCode) $url" -ForegroundColor Green
  } catch {
    Write-Host "ERR $url" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
  }
}

Write-Host ""
Write-Host "Manual checks still required:" -ForegroundColor Yellow
Write-Host "1. Signup -> email confirm -> login -> dashboard."
Write-Host "2. Run scan only after login; save to dashboard."
Write-Host "3. Create report export from saved scan."
Write-Host "4. User A/User B BOLA test."
Write-Host "5. Razorpay test mode checkout + webhook if keys are configured."
Write-Host "6. Supabase SMTP + custom domain redirect if production domain is added."
