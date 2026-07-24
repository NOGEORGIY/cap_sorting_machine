#!/usr/bin/env python3
"""
Единый скрипт запуска всех компонентов системы сортировки крышек
Запускает: FastAPI, CV сервис, Frontend (React/Vite)
"""

import subprocess
import sys
import os
import time
import signal
import threading
import psutil
from pathlib import Path

# Определяем пути
ROOT_DIR = Path(__file__).parent.absolute()
FASTAPI_DIR = ROOT_DIR / "capsSortFastAPI"
CV_DIR = ROOT_DIR / "CV_project"
FRONTEND_DIR = ROOT_DIR / "capsSortUi"

# Цвета для вывода
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_status(service, message, status="info"):
    """Вывод статуса с цветом"""
    colors = {
        "info": Colors.BLUE,
        "success": Colors.GREEN,
        "error": Colors.RED,
        "warning": Colors.YELLOW
    }
    color = colors.get(status, Colors.RESET)
    print(f"{color}[{service}]{Colors.RESET} {message}")

def check_dependencies():
    """Проверка установленных зависимостей"""
    try:
        import pip
        return True
    except ImportError:
        print_status("System", "Pip не найден!", "error")
        return False

def run_command(cmd, cwd, name, capture_output=False):
    """Запуск команды в подпроцессе"""
    try:
        print_status(name, f"Запуск: {' '.join(cmd)}", "info")
        
        if capture_output:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
        else:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                shell=True
            )
        return process
    except Exception as e:
        print_status(name, f"Ошибка запуска: {e}", "error")
        return None

def install_requirements():
    """Установка Python зависимостей"""
    requirements_files = [
        (FASTAPI_DIR / "requirements.txt", "FastAPI"),
        (CV_DIR / "requirements.txt", "CV Service")
    ]
    
    for req_file, service in requirements_files:
        if req_file.exists():
            print_status(service, "Установка зависимостей...", "info")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print_status(service, "Зависимости установлены", "success")
            else:
                print_status(service, f"Ошибка установки: {result.stderr}", "error")

def install_frontend_deps():
    """Установка фронтенд зависимостей"""
    if (FRONTEND_DIR / "package.json").exists():
        print_status("Frontend", "Установка npm зависимостей...", "info")
        result = subprocess.run(
            ["npm", "install"],
            cwd=FRONTEND_DIR,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_status("Frontend", "npm зависимости установлены", "success")
        else:
            print_status("Frontend", f"Ошибка npm install: {result.stderr}", "error")

def start_all():
    """Запуск всех сервисов"""
    processes = {}
    
    # Проверяем наличие Python
    python_cmd = sys.executable
    print_status("System", f"Python: {python_cmd}", "info")
    
    # Проверяем наличие Node.js
    try:
        node_version = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print_status("System", f"Node.js: {node_version.stdout.strip()}", "info")
    except FileNotFoundError:
        print_status("System", "Node.js не найден! Установите Node.js", "error")
        return
    
    # 1. Запуск FastAPI
    print_status("FastAPI", "Запуск сервера...", "info")
    fastapi_process = run_command(
        [python_cmd, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        FASTAPI_DIR,
        "FastAPI"
    )
    if fastapi_process:
        processes["fastapi"] = fastapi_process
        time.sleep(2)
    
    # 2. Запуск CV сервиса
    print_status("CV Service", "Запуск обработки камеры...", "info")
    cv_process = run_command(
        [python_cmd, "main.py"],
        CV_DIR,
        "CV Service"
    )
    if cv_process:
        processes["cv"] = cv_process
        time.sleep(2)
    
    # 3. Запуск Frontend
    print_status("Frontend", "Запуск Vite сервера...", "info")
    frontend_process = run_command(
        ["npm", "run", "dev"],
        FRONTEND_DIR,
        "Frontend"
    )
    if frontend_process:
        processes["frontend"] = frontend_process
        time.sleep(3)
    
    print("\n" + "="*60)
    print(Colors.GREEN + "ВСЕ СЕРВИСЫ ЗАПУЩЕНЫ!" + Colors.RESET)
    print("="*60)
    print(f"{Colors.CYAN}📍 FastAPI:    http://localhost:8000{Colors.RESET}")
    print(f"{Colors.CYAN}📍 Frontend:   http://localhost:5173 (или другой порт){Colors.RESET}")
    print(f"{Colors.CYAN}📍 CV Service: запущен на камере{Colors.RESET}")
    print("="*60)
    print(Colors.YELLOW + "Для остановки всех сервисов нажмите Ctrl+C" + Colors.RESET)
    print("="*60)
    
    # Ждем завершения
    try:
        # Ждем завершения любого процесса
        while True:
            time.sleep(1)
            # Проверяем, не упали ли процессы
            for name, proc in list(processes.items()):
                if proc.poll() is not None:
                    print_status(name, f"Процесс завершился с кодом {proc.returncode}", "error")
                    # Перезапускаем упавший сервис
                    if name == "fastapi":
                        print_status("FastAPI", "Перезапуск...", "warning")
                        processes["fastapi"] = run_command(
                            [python_cmd, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                            FASTAPI_DIR,
                            "FastAPI"
                        )
                    elif name == "cv":
                        print_status("CV Service", "Перезапуск...", "warning")
                        processes["cv"] = run_command(
                            [python_cmd, "main.py"],
                            CV_DIR,
                            "CV Service"
                        )
                    elif name == "frontend":
                        print_status("Frontend", "Перезапуск...", "warning")
                        processes["frontend"] = run_command(
                            ["npm", "run", "dev"],
                            FRONTEND_DIR,
                            "Frontend"
                        )
    except KeyboardInterrupt:
        print("\n" + Colors.YELLOW + "⏹ Остановка сервисов..." + Colors.RESET)
        for name, proc in processes.items():
            if proc:
                print_status(name, "Остановка...", "warning")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        print(Colors.GREEN + "Все сервисы остановлены" + Colors.RESET)

if __name__ == "__main__":
    # Установка зависимостей (опционально)
    if "--install" in sys.argv:
        install_requirements()
        install_frontend_deps()
    
    # Запуск с автоматической установкой
    if "--auto-install" in sys.argv:
        print_status("System", "Автоматическая установка зависимостей...", "info")
        install_requirements()
        install_frontend_deps()
    
    start_all()