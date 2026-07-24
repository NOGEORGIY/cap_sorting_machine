@echo off
chcp 65001 >nul
title Установка зависимостей проекта

echo ================================================================================
echo                   УСТАНОВКА ЗАВИСИМОСТЕЙ ПРОЕКТА
echo ================================================================================
echo.

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: Проверка Python
echo [1/4] Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден! Установите Python 3.8 или выше
    echo    Скачать: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo ✅ Python %PYTHON_VER% найден
echo.

:: Обновление pip
echo [2/4] Обновление pip...
python -m pip install --upgrade pip -q
if %errorlevel% equ 0 (
    echo ✅ Pip обновлен
) else (
    echo ⚠️ Не удалось обновить pip
)
echo.

:: Установка зависимостей FastAPI
echo [3/4] Установка зависимостей FastAPI...
echo.
if exist "%ROOT_DIR%capsSortFastAPI\requirements.txt" (
    echo 📦 Найден requirements.txt в capsSortFastAPI
    echo    Установка зависимостей для FastAPI...
    cd /d "%ROOT_DIR%capsSortFastAPI"
    
    echo    Установка основных пакетов...
    pip install fastapi==0.135.1 -q
    pip install "uvicorn[standard]==0.41.0" -q
    pip install pydantic==2.12.5 -q
    pip install pydantic-settings==2.13.1 -q
    pip install python-multipart==0.0.22 -q
    pip install sqlalchemy==2.0.48 -q
    pip install httpx==0.28.1 -q
    pip install psycopg2-binary==2.9.11 -q
    pip install alembic==1.18.4 -q
    
    echo    ✅ FastAPI зависимости установлены
    cd /d "%ROOT_DIR%"
) else (
    echo ⚠️ requirements.txt не найден в capsSortFastAPI
    echo    Устанавливаем вручную...
    pip install -q fastapi==0.135.1 "uvicorn[standard]==0.41.0" pydantic==2.12.5 pydantic-settings==2.13.1 python-multipart==0.0.22 sqlalchemy==2.0.48 httpx==0.28.1 psycopg2-binary==2.9.11 alembic==1.18.4
)
echo.

:: Установка зависимостей CV
echo [4/4] Установка зависимостей CV сервиса...
echo.
if exist "%ROOT_DIR%CV_project\requirements.txt" (
    echo 📦 Найден requirements.txt в CV_project
    echo    Установка зависимостей для CV сервиса...
    cd /d "%ROOT_DIR%CV_project"
    
    echo    Установка ultralytics (может занять несколько минут)...
    pip install ultralytics>=8.0.0 -q
    pip install opencv-python>=4.8.0 -q
    pip install websockets>=12.0 -q
    pip install python-dotenv>=1.0.0 -q
    pip install requests>=2.31.0 -q
    pip install asyncio>=3.4.3 -q
    
    echo    ✅ CV зависимости установлены
    cd /d "%ROOT_DIR%"
) else (
    echo ⚠️ requirements.txt не найден в CV_project
    echo    Устанавливаем вручную...
    pip install -q "ultralytics>=8.0.0" "opencv-python>=4.8.0" "websockets>=12.0" "python-dotenv>=1.0.0" "requests>=2.31.0" "asyncio>=3.4.3"
)
echo.

:: Дополнительная проверка
echo.
echo ================================================================================
echo                        ПРОВЕРКА УСТАНОВКИ
echo ================================================================================
echo.

call :CheckModule "fastapi" "FastAPI"
call :CheckModule "uvicorn" "Uvicorn"
call :CheckModule "sqlalchemy" "SQLAlchemy"
call :CheckModule "pydantic" "Pydantic"
call :CheckModule "ultralytics" "Ultralytics (YOLO)"
call :CheckModule "cv2" "OpenCV"
call :CheckModule "websockets" "WebSockets"
call :CheckModule "requests" "Requests"
call :CheckModule "dotenv" "python-dotenv"

echo.
echo ================================================================================
echo                        РЕЗУЛЬТАТ УСТАНОВКИ
echo ================================================================================
echo.
echo ✅ Установка завершена!
echo.
echo 🚀 Для запуска проекта используйте:
echo    python start_all.py
echo.
echo ИЛИ
echo.
echo    start_simple.bat
echo.
echo ================================================================================
pause
exit /b 0

:: ===================================================================
:: Функция проверки модуля
:: ===================================================================
:CheckModule
set "MODULE=%~1"
set "NAME=%~2"

python -c "import %MODULE%" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ %NAME% - установлен
) else (
    echo ❌ %NAME% - НЕ УСТАНОВЛЕН
)
exit /b 0