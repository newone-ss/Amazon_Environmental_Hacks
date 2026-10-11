Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Bhujal AI & Climate-Water Resilience Platform        " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Write-Host "`n[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.app:app --reload --port 8000"

Write-Host "[2/2] Launching Vite Frontend on http://localhost:5173 ..." -ForegroundColor Green
Set-Location bhujal-frontend\bhujal-frontend
npm run dev
