Write-Host "Starting Web3Guard AI by RAADHANEX local stack" -ForegroundColor Cyan
Write-Host "Open two terminals if this script cannot keep both processes visible." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; if (!(Test-Path .env)) { copy .env.example .env }; if (!(Test-Path .venv)) { py -3.12 -m venv .venv }; .\.venv\Scripts\activate; python -m pip install --upgrade pip setuptools wheel; pip install -r requirements.txt; uvicorn main:app --reload --host 0.0.0.0 --port 8000"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; if (!(Test-Path .env.local)) { copy .env.local.example .env.local }; npm install; npm run dev"
Write-Host "Backend: http://localhost:8000/health" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
