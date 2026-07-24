@echo off
title Plastic Sorting System

echo ========================================
echo   Запуск системы сортировки пластика
echo ========================================

set PYTHON_PATH=C:\Users\rayph\AppData\Local\Microsoft\WindowsApps\python.exe

echo [1/3] Запуск FastAPI Backend (порт 8000)...
start "Backend" cmd /k "cd /d C:\Users\rayph\Desktop\cap_sorting_machine-dev\capsSortFastAPI && %PYTHON_PATH% -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/3] Запуск Frontend (порт 3000)...
start "Frontend" cmd /k "cd /d C:\Users\rayph\Desktop\cap_sorting_machine-dev\capsSortUi && npm run dev"

echo [3/3] Запуск Computer Vision (порт 5000)...
start "CV" cmd /k "cd /d C:\Users\rayph\Desktop\cap_sorting_machine-dev\CV_project && %PYTHON_PATH% main.py"

echo ========================================
echo   Все сервисы запущены!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   CV:       http://localhost:5000
echo ========================================
pause