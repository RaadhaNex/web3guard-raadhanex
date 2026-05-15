# Phase 6 local QA helper for Windows PowerShell.
# Run from project root after extracting the ZIP.

Write-Host "== Web3Guard AI by RAADHANEX - Phase 6 Local QA ==" -ForegroundColor Cyan

Write-Host "\nBackend commands:" -ForegroundColor Yellow
Write-Host "cd backend"
Write-Host "py -3.12 -m venv .venv"
Write-Host ".\.venv\Scripts\activate"
Write-Host "python -m pip install --upgrade pip setuptools wheel"
Write-Host "pip install -r requirements.txt"
Write-Host "copy .env.example .env"
Write-Host "uvicorn main:app --reload --host 0.0.0.0 --port 8000"

Write-Host "\nFrontend commands:" -ForegroundColor Yellow
Write-Host "cd frontend"
Write-Host "npm install"
Write-Host "copy .env.local.example .env.local"
Write-Host "npm run dev"

Write-Host "\nAfter both are running, open:" -ForegroundColor Green
Write-Host "Backend health: http://localhost:8000/health"
Write-Host "Backend readiness: http://localhost:8000/health/readiness"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Local QA console: http://localhost:3000/local-qa"
