from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import requests
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List

import uvicorn
from database import engine, get_db, Base, SessionLocal
import models as models
import crud as crud
import schemas as schemas
from cv_client import cv_client

from collections import deque
import time
from schemas import LogCreate

APP_TITLE = "API для сортировки крышек"
APP_VERSION = "1.1.1"
CV_SECRET_TOKEN = "123qweasdzxc"  # Токен для авторизации CV-сервиса
ARDUINO_URL = "http://192.168.4.1"

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CV_COLORS = [
    'white', 'black', 'red', 'orange', 'yellow', 
    'green', 'sky_blue', 'blue', 'purple', 'pink', 'brown'
]

ALLOWED_COLORS = CV_COLORS + ['unknown']

# === СТЕК В ПАМЯТИ ===
LID_STACK = deque(maxlen=20)  # храним последние 20 крышек
STACK_TIMEOUT = 30.0  # секунд

def normalize_color(color: str) -> str:
    """Преобразует цвет из CV в формат для БД"""
    if not color:
        return "unknown"
    
    color = color.lower().strip()
    
    # Если цвет есть в списке - возвращаем его
    if color in ALLOWED_COLORS:
        return color
    
    # Если нет - логируем и возвращаем unknown
    print(f"Неизвестный цвет: {color}")
    return "unknown"

def send_to_arduino(do_push):
    """Отправить команду в Arduino используя существующие эндпоинты"""
    try:
        action = "push" if do_push else "ignore"
        add_url = f"{ARDUINO_URL}/add?action={action}"
        response = requests.get(add_url, timeout=2.0)
        
        if response.status_code != 200:
            print(f"Ошибка добавления шага: {response.status_code}")
            return False
        
        execute_url = f"{ARDUINO_URL}/execute"
        response = requests.get(execute_url, timeout=5.0)
        
        if response.status_code == 200:
            print(f"Arduino выполнил команду: {action}")
            return True
        else:
            print(f"Ошибка выполнения: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Arduino не отвечает (проверь подключение)")
        return False
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

def add_to_arduino_queue(do_push):
    """Только добавить задачу в очередь Arduino, НЕ выполнять"""
    try:
        action = "push" if do_push else "ignore"
        add_url = f"{ARDUINO_URL}/add?action={action}"
        response = requests.get(add_url, timeout=2.0)
        
        if response.status_code == 200:
            print(f"Добавлено в очередь Arduino: {action}")
            return True
        else:
            print(f"Ошибка добавления в очередь: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Arduino не отвечает (проверь подключение)")
        return False
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
    
@app.get("/test-arduino")
async def test_arduino():
    """Тест связи с Arduino"""
    try:
        # Добавляем шаг "Толкать"
        r1 = requests.get("http://192.168.4.1/add?action=push", timeout=2.0)
        # Выполняем
        r2 = requests.get("http://192.168.4.1/execute", timeout=5.0)
        return {
            "add_status": r1.status_code,
            "execute_status": r2.status_code,
            "arduino_ok": r1.status_code == 200 and r2.status_code == 200
        }
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/api/sensor/trigger")
async def on_sensor_trigger():
    print("ЭНДПОИНТ /api/sensor/trigger вызван")
    now = time.time()
    
    # Очищаем устаревшие записи
    while LID_STACK and (now - LID_STACK[0]["timestamp"]) > STACK_TIMEOUT:
        LID_STACK.popleft()
    
    if not LID_STACK:
        print("Стек пуст, игнорируем сигнал датчика")
        return {"action": "ignore", "reason": "stack empty"}
    
    # Достаем последнюю крышку
    last_lid = LID_STACK.pop()
    

    # Если цвет совпадает с целевым (успех) → НЕ ТОЛКАЕМ (ignore)
    # Если цвет НЕ совпадает (брак) → ТОЛКАЕМ (push)
    do_push = not last_lid["is_success"]
    
    print(f"📦 Переброс в Arduino: цвет {last_lid['detected_color']}, целевой {last_lid['target_color']}, толкать: {do_push}")
    
    # Добавляем в очередь Arduino (без выполнения)
    success = add_to_arduino_queue(do_push)
    
    return {
        "action": "added_to_queue" if success else "failed",
        "color": last_lid["detected_color"],
        "target": last_lid["target_color"],
        "is_success": last_lid["is_success"],
        "do_push": do_push,
        "arduino_status": "ok" if success else "failed"
    }

@app.post("/cv/stack")
async def add_to_stack(
    report: dict,
    x_cv_token: Optional[str] = Header(None)
):
    """CV отправляет сюда ВСЕ обнаруженные крышки для стека"""
    if x_cv_token != CV_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    # Извлекаем данные из словаря
    detected_color = report.get("detected_color", "unknown")
    target_color = report.get("target_color", "unknown")
    is_success = report.get("is_success", False)
    
    # Добавляем в стек с временем
    LID_STACK.append({
        "detected_color": detected_color,
        "target_color": target_color,
        "is_success": is_success,
        "timestamp": time.time()
    })
    
    # Сохраняем в БД (логирование)
    db = SessionLocal()
    try:
        log = crud.create_log(
            db,
            detected_color=detected_color,
            target_color=target_color,
            is_success=is_success
        )
    finally:
        db.close()
    
    print(f"Добавлено в стек: {detected_color} -> {target_color} (успех: {is_success})")
    
    try:
        # Вызываем эндпоинт триггера (GET)
        response = requests.get("http://localhost:8000/api/sensor/trigger", timeout=1.0)
    except Exception as e:
        print(f"Ошибка вызова триггера: {e}")
    
    return {"status": "stored", "stack_size": len(LID_STACK)}

# === НОВЫЙ ЭНДПОИНТ: Получить текущий стек (для фронта) ===
@app.get("/api/stack")
async def get_stack():
    """Вернуть текущее содержимое стека (для отображения на фронте)"""
    # Очищаем устаревшие записи
    now = time.time()
    while LID_STACK and (now - LID_STACK[0]["timestamp"]) > STACK_TIMEOUT:
        LID_STACK.popleft()
    
    return {
        "stack": list(LID_STACK),
        "size": len(LID_STACK)
    }

# === ДОБАВИТЬ WebSocket для стриминга стека на фронт ===
@app.websocket("/ws/stack")
async def stack_websocket(websocket: WebSocket):
    """WebSocket для отправки обновлений стека на фронт"""
    await websocket.accept()
    try:
        while True:
            # Отправляем текущий стек каждые 500ms
            now = time.time()
            while LID_STACK and (now - LID_STACK[0]["timestamp"]) > STACK_TIMEOUT:
                LID_STACK.popleft()
            
            await websocket.send_json({
                "type": "stack_update",
                "stack": list(LID_STACK),
                "size": len(LID_STACK)
            })
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print("Клиент стека отключился")



class SensorToggleRequest(BaseModel):
    proximity: bool

@app.post("/api/sensor/toggle")
async def toggle_sensor_simulation(payload: SensorToggleRequest):
    """
    Эндпоинт для переключения режима угадайки (симуляция датчика).
    Принимает JSON: {"proximity": true} или {"proximity": false}
    """
    # Мгновенно отправляем пакет {"type": "sensor", "proximity": ...} во все CV-скрипты
    await manager.send_sensor_signal(proximity=payload.proximity)
    
    status_str = "АКТИВИРОВАН (Режим Mean)" if payload.proximity else "ДЕАКТИВИРОВАН (Режим YOLO)"
    print(f"Сигнал датчика отправлен через сокет -> Режим {status_str}")
    return {"status": "success", "proximity_active": payload.proximity}


# Хранилище активных WebSocket подключений
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"CV подключился. Всего подключений: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"CV отключился. Всего подключений: {len(self.active_connections)}")
    
    async def send_to_cv(self, message: dict):
        """Отправить сообщение всем подключенным CV"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

    # СТРОГО ДЛЯ CV: Метод для отправки сигнала симуляции датчика
    async def send_sensor_signal(self, proximity: bool):
        """Отправить сигнал с датчика обнаружения препятствий (True/False) через WebSocket"""
        await self.send_to_cv({
            "type": "sensor",
            "proximity": proximity
        })


manager = ConnectionManager()

# Создание таблиц БД при старте
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
async def startup_event():
    """Инициализация системы при запуске"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        crud.initialize_settings(db)
        print("Настройки системы инициализированы")
    finally:
        db.close()


@app.put("/settings", response_model=schemas.SettingsResponse)
async def update_settings(settings_data: schemas.SettingsUpdate, db: Session = Depends(get_db)):
    """Обновить настройки (смена цвета) + мгновенно отправить их в CV через WebSocket"""
    
    if settings_data.target_color is None:
        raise HTTPException(status_code=400, detail="Цвет не указан")
    
    # Извлекаем значение цвета
    color_value = settings_data.target_color.value if hasattr(settings_data.target_color, 'value') else settings_data.target_color
    
    # Проверяем, что color_value не None
    if color_value is None:
        raise HTTPException(status_code=400, detail="Цвет не может быть пустым")
    
    color_value = color_value.lower()
    
    # 1. Обновляем настройки в базе данных бэка
    settings = crud.update_settings(db, target_color=color_value)
    if not settings:
        raise HTTPException(status_code=500, detail="Не удалось обновить настройки в БД")
    
    # 2. Отправляем конфигурацию в WebSocket
    await manager.send_to_cv({
        "type": "config",
        "target_color": settings.target_color,
        "is_enabled": settings.is_enabled
    })
    
    print(f"[БЭКЕНД] Настройки успешно обновлены. Новый целевой цвет: {settings.target_color.upper()}")
    return settings


@app.websocket("/ws/cv")
async def websocket_endpoint(websocket: WebSocket, x_cv_token: str = Header(None)):
    """WebSocket для связи с CV сервисом"""
    if x_cv_token != CV_SECRET_TOKEN:
        await websocket.close(code=4001)
        return
    
    await manager.connect(websocket)
    try:
        # Отправляем текущие настройки при подключении
        db = SessionLocal()
        settings = crud.get_settings(db)
        db.close()
        
        if settings:
            await websocket.send_json({
                "type": "config",
                "target_color": settings.target_color,
                "is_enabled": settings.is_enabled
            })
        
        # Ждем сообщения от CV (отчеты)
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "report":
                # Обрабатываем отчет через существующий эндпоинт
                db = SessionLocal()
                try:
                    log = crud.create_log(
                        db,
                        detected_color=data.get("detected_color", "unknown"),
                        target_color=data.get("target_color", "unknown"),
                        is_success=data.get("is_success", False)
                    )
                finally:
                    db.close()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Ошибка WebSocket: {e}")
        manager.disconnect(websocket)

@app.post("/start", response_model=schemas.SettingsResponse)
async def start_sorting(db: Session = Depends(get_db)):
    """Запуск процесса сортировки"""
    settings = crud.get_settings(db)
    if not settings:
        raise HTTPException(status_code=500, detail="Настройки не найдены")
    if settings.is_enabled:
        raise HTTPException(status_code=400, detail="Система уже запущена")

    crud.update_settings(db, is_enabled=True)
    current_settings = crud.get_settings(db)

    await manager.send_to_cv({
        "type": "config",
        "target_color": current_settings.target_color,
        "is_enabled": True
    })

    print("Фронтенд запустил сканирование YOLO по WebSocket")
    return current_settings

@app.post("/stop", response_model=schemas.SettingsResponse)
async def stop_sorting(db: Session = Depends(get_db)):
    """Остановка процесса сортировки"""
    settings = crud.get_settings(db)
    if not settings:
        raise HTTPException(status_code=500, detail="Настройки не найдены")
    if not settings.is_enabled:
        raise HTTPException(status_code=400, detail="Система уже остановлена")

    crud.update_settings(db, is_enabled=False)
    current_settings = crud.get_settings(db)

    await manager.send_to_cv({
        "type": "config",
        "target_color": current_settings.target_color,
        "is_enabled": False
    })

    print("Фронтенд остановил сканирование YOLO по WebSocket")
    return current_settings

@app.post("/cv/report", response_model=schemas.LogResponse)
async def receive_vision_report(report: schemas.LogCreate, db: Session = Depends(get_db), x_cv_token: Optional[str] = Header(None)):
    """Принять отчет от CV сервиса о распознанной крышке"""
    if x_cv_token != CV_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Неверный токен CV сервиса")

    settings = crud.get_settings(db)
    if not settings:
        raise HTTPException(status_code=500, detail="Настройки не найдены")

    # Создаем запись в журнале на основе POST-отчета из скрипта CV
    log = crud.create_log(
        db,
        detected_color=report.detected_color.value,
        target_color=settings.target_color,
        is_success=report.is_success
    )
    return log

@app.get("/stats", response_model=dict)
async def get_statistics(hours: int = 24, db: Session = Depends(get_db)):
    """Получить статистику за N часов"""
    return crud.get_statistics(db, hours=hours)

@app.get("/logs", response_model=List[schemas.LogResponse])
async def get_logs(limit: int = 100, hours: int = 24, db: Session = Depends(get_db)):
    """Получить последние логи событий"""
    return crud.get_logs(db, limit=limit, hours=hours)

# В main.py FastAPI добавьте:
@app.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """Получить текущий статус системы"""
    settings = crud.get_settings(db)
    if not settings:
        raise HTTPException(status_code=404, detail="Настройки не найдены")
    
    return {
        "is_enabled": settings.is_enabled,
        "target_color": settings.target_color,
        "proximity_active": getattr(settings, 'proximity_active', False)
    }

@app.get("/")
async def root():
    """Информация о сервисе и доступных эндпоинтах"""
    return {
        "message": f"{APP_TITLE} v{APP_VERSION}",
        "status": "online",
        "database": "postgresql",
        "endpoints": {
            "settings": {"url": "/settings", "methods": ["GET", "PUT"]},
            "start": {"url": "/start", "method": "POST"},
            "stop": {"url": "/stop", "method": "POST"},
            "cv_report": {"url": "/cv/report", "method": "POST", "auth": "X-CV-Token required"},
            "stats": {"url": "/stats", "method": "GET"},
            "logs": {"url": "/logs", "method": "GET"},
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)