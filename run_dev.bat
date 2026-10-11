@echo off
title Bhujal Full-Stack Environment
echo ========================================================
echo   Bhujal AI & Climate-Water Resilience Platform
echo ========================================================
echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "Bhujal Backend (FastAPI :8000)" cmd /k "python -m uvicorn backend.app:app --reload --port 8000"

echo [2/2] Launching Vite Frontend on http://localhost:5173 ...
cd frontend
call npm run dev
