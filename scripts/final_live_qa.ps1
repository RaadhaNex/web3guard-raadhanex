param(
  [string]$FrontendUrl = "https://web3guard-raadhanex.vercel.app",
  [string]$BackendUrl = "https://web3guard-raadhanex-backend.onrender.com"
)

Write-Host "Web3Guard Final Live QA" -ForegroundColor Cyan
Write-Host "Frontend: $FrontendUrl"
Write-Host "Backend : $BackendUrl"

function Test-Endpoint($Name, $Url) {
  try {
    $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 30 -ErrorAction Stop
    Write-Host "[PASS] $Name -> $($response.StatusCode)" -ForegroundColor Green
    return $true
  } catch {
    Write-Host "[FAIL] $Name -> $($_.Exception.Message)" -ForegroundColor Red
    return $false
  }
}

$ok = $true
$ok = (Test-Endpoint "Frontend home" $FrontendUrl) -and $ok
$ok = (Test-Endpoint "Backend root" $BackendUrl) -and $ok
$ok = (Test-Endpoint "Backend health" "$BackendUrl/health") -and $ok
$ok = (Test-Endpoint "Backend readiness" "$BackendUrl/health/readiness") -and $ok

Write-Host "\nManual checks:" -ForegroundColor Yellow
Write-Host "1. Login -> header should show Dashboard/Logout, not Login."
Write-Host "2. Dashboard should not show local-demo-user."
Write-Host "3. Unified scanner should require login and show progress while scanning."
Write-Host "4. Save scan -> create report -> export PDF/HTML/Markdown/JSON."
Write-Host "5. Admin pages should require ADMIN_TOKEN."
Write-Host "6. Razorpay should stay disabled unless test keys + webhook secret are configured."
Write-Host "7. Random third-party targets must not be scanned without authorization."

if ($ok) {
  Write-Host "\nCore live endpoints passed." -ForegroundColor Green
  exit 0
}

Write-Host "\nSome live endpoints failed. Check Vercel/Render logs." -ForegroundColor Red
exit 1
