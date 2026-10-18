@echo off
echo ==============================================================================
echo Starting AI Tech Consultant Suite (T1, T2, T3) locally on Windows
echo ==============================================================================

echo [1/4] Starting Task 1 Knowledge Brain FastAPI Backend on http://localhost:8000 ...
start "T1 Knowledge Brain API" cmd /k "cd task1-knowledge-brain && uvicorn app.main:app --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/4] Starting Task 1 Knowledge Brain Streamlit UI on http://localhost:8501 ...
start "T1 Knowledge Brain UI" cmd /k "cd task1-knowledge-brain && streamlit run ui/streamlit_app.py --server.port 8501"

echo [3/4] Starting Task 2 Inbox Agent Next.js on http://localhost:3000 ...
start "T2 Inbox Agent" cmd /k "cd task2-inbox-agent && npm run dev"

echo [4/4] Starting Task 3 Meeting-to-Scope Streamlit UI on http://localhost:8502 ...
start "T3 Meeting Scope UI" cmd /k "cd task3-meeting-to-scope && streamlit run ui/streamlit_app.py --server.port 8502"

echo ==============================================================================
echo All services launched!
echo - T1 API:          http://localhost:8000/docs
echo - T1 Chat UI:      http://localhost:8501
echo - T2 Inbox Agent:  http://localhost:3000
echo - T3 Scope UI:     http://localhost:8502
echo ==============================================================================
pause
