param(
  [string]$FrontendUrl = "https://web3guard-raadhanex.vercel.app",
  [string]$BackendUrl = "https://web3guard-raadhanex-backend.onrender.com"
)

Write-Host "=== Web3Guard AI by RAADHANEX — Final External Activation Check ===" -ForegroundColor Cyan
Write-Host "Frontend: $FrontendUrl"
Write-Host "Backend : $BackendUrl"
Write-Host ""

function Test-JsonEndpoint($Name, $Url) {
  try {
    $res = Invoke-WebRequest -Uri $Url -Method GET -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
    Write-Host "[PASS] $Name -> $($res.StatusCode)" -ForegroundColor Green
    try {
      $json = $res.Content | ConvertFrom-Json
      return $json
    } catch {
      return $res.Content
    }
  } catch {
    Write-Host "[FAIL] $Name -> $($_.Exception.Message)" -ForegroundColor Red
    return $null
  }
}

function Test-Headers($Name, $Url) {
  try {
    $res = Invoke-WebRequest -Uri $Url -Method GET -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
    Write-Host "[PASS] $Name headers -> $($res.StatusCode)" -ForegroundColor Green
    $needed = @("content-security-policy", "x-content-type-options", "x-frame-options", "referrer-policy")
    foreach ($key in $needed) {
      $value = $res.Headers[$key]
      if (-not $value) { $value = $res.Headers[$key.ToUpper()] }
      if ($value) {
        Write-Host "  $key: present" -ForegroundColor Green
      } else {
        Write-Host "  $key: missing" -ForegroundColor Yellow
      }
    }
  } catch {
    Write-Host "[FAIL] $Name headers -> $($_.Exception.Message)" -ForegroundColor Red
  }
}

$health = Test-JsonEndpoint "Backend health" "$BackendUrl/health"
$readiness = Test-JsonEndpoint "Backend readiness" "$BackendUrl/health/readiness"
$auth = Test-JsonEndpoint "Supabase auth status" "$BackendUrl/auth/status"
$db = Test-JsonEndpoint "Database status" "$BackendUrl/db/status"
$payments = Test-JsonEndpoint "Payment status" "$BackendUrl/payments/status"
$providers = Test-JsonEndpoint "External providers" "$BackendUrl/final-qa/external-providers"
$remaining = Test-JsonEndpoint "Remaining work" "$BackendUrl/final-qa/remaining-work"
$ai = Test-JsonEndpoint "AI status" "$BackendUrl/ai/status"
$fix = Test-JsonEndpoint "AI fix assistant status" "$BackendUrl/ai/fix-assistant/status"
$static = Test-JsonEndpoint "Static tools status" "$BackendUrl/scan/static-analysis/status"
$deep = Test-JsonEndpoint "Deep tools status" "$BackendUrl/scan/deep-analysis/status"

Test-Headers "Frontend" $FrontendUrl
Test-Headers "Backend" $BackendUrl

Write-Host ""
Write-Host "Key truth states:" -ForegroundColor Cyan
if ($payments) {
  Write-Host "  Razorpay configured      : $($payments.razorpay_configured)"
  Write-Host "  Razorpay webhook configured: $($payments.razorpay_webhook_configured)"
  Write-Host "  Manual fallback          : $($payments.manual_verification_fallback)"
}
if ($auth) {
  Write-Host "  Supabase configured      : $($auth.configured)"
  Write-Host "  Backend auth required    : $($auth.auth_required)"
  Write-Host "  JWT verify enabled       : $($auth.jwt_verify_enabled)"
}
if ($fix) {
  Write-Host "  AI fix provider configured: $($fix.provider_configured)"
  Write-Host "  Code send enabled         : $($fix.ai_fix_send_code)"
}

Write-Host ""
Write-Host "Manual final checks still required:" -ForegroundColor Yellow
Write-Host "1. Supabase: signup -> confirmation email -> /auth/callback -> login -> logout."
Write-Host "2. Two-user BOLA/IDOR: User A saved scan/report must 404 for User B."
Write-Host "3. Razorpay: test checkout + checkout signature verify + payment.captured/order.paid webhook."
Write-Host "4. Custom domain: update Vercel, Render FRONTEND_ORIGIN, Supabase Site URL + Redirect URLs, and CSP env."
Write-Host "5. AI/OpenAI/Claude: verify Provider Not Configured without keys; verify real provider only after backend key setup."
Write-Host "6. Slither/Aderyn/Mythril: verify Tool Not Installed / Provider Not Configured unless worker/binary is actually installed."
Write-Host "7. Etherscan: verified contract succeeds, unverified/invalid address shows clear Needs API Key or not-assessed state."
