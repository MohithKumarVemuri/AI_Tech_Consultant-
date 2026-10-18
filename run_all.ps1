# PowerShell script to run all AI Tech Consultant tasks locally
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "Starting AI Tech Consultant Suite (T1, T2, T3) locally on Windows" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Start Task 1 API
Write-Host "[1/4] Starting Task 1 Knowledge Brain FastAPI on http://localhost:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\task1-knowledge-brain'; uvicorn app.main:app --port 8000 --reload"

Start-Sleep -Seconds 3

# 2. Start Task 1 UI
Write-Host "[2/4] Starting Task 1 Knowledge Brain UI on http://localhost:8501..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\task1-knowledge-brain'; streamlit run ui/streamlit_app.py --server.port 8501"

# 3. Start Task 2 Next.js
Write-Host "[3/4] Starting Task 2 Inbox Agent Next.js on http://localhost:3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\task2-inbox-agent'; npm run dev"

# 4. Start Task 3 UI
Write-Host "[4/4] Starting Task 3 Meeting Scope UI on http://localhost:8502..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\task3-meeting-to-scope'; streamlit run ui/streamlit_app.py --server.port 8502"

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "All 4 interfaces started successfully:" -ForegroundColor Yellow
Write-Host "  - T1 REST API:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - T1 Chat UI:    http://localhost:8501" -ForegroundColor White
Write-Host "  - T2 Inbox UI:   http://localhost:3000" -ForegroundColor White
Write-Host "  - T3 Scope UI:   http://localhost:8502" -ForegroundColor White
Write-Host "==============================================================================" -ForegroundColor Cyan
