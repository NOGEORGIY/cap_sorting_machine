from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List

import uvicorn
from database import engine, get_db, Base
import models
import crud
import schemas
from cv_client import cv_client

APP_TITLE = "API для сортировки крышек"
APP_VERSION = "1.1.0"
CV_SECRET_TOKEN = "123qweasdzxc"  # Токен для авторизации CV-сервиса

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/settings", response_model=schemas.SettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """Получить текущие настройки системы"""
    settings = crud.get_settings(db)
    if not settings:
        raise HTTPException(status_code=500, detail="Настройки не инициализированы")
    return settings

@app.put("/settings", response_model=schemas.SettingsResponse)
async def update_settings(settings_data: schemas.SettingsUpdate, db: Session = Depends(get_db)):
    """Обновить целевой цвет сортировки"""
    # Извлекаем строковое значение цвета
    color_value = settings_data.target_color.value

    # Обновляем в БД
    settings = crud.update_settings(db, target_color=color_value)
    if not settings:
        raise HTTPException(status_code=500, detail="Не удалось обновить настройки")

    # Отправляем новый цвет в CV сервис
    await cv_client.send_target_color(
        color=settings.target_color,
        is_enabled=settings.is_enabled
    )

    return settings

# ==========================================
# === УПРАВЛЕНИЕ ПРОЦЕССОМ ===
# ==========================================

@app.post("/start", response_model=schemas.SettingsResponse)
async def start_sorting(db: Session = Depends(get_db)):
    """Запуск процесса сортировки"""
    settings = crud.get_settings(db)
    if not settings:
        raise HTTPException(status_code=500, detail="Настройки не найдены")
    if settings.is_enabled:
        raise HTTPException(status_code=400, detail="Система уже запущена")

    crud.update_settings(db, is_enabled=True)

    if not await cv_client.send_start_command():
        crud.update_settings(db, is_enabled=False)
        raise HTTPException(status_code=503, detail="Не удалось связаться с CV сервисом")

    return crud.get_settings(db)

@app.post("/stop", response_model=schemas.SettingsResponse)
async def stop_sorting(db: Session = Depends(get_db)):
    """Остановка процесса сортировки"""
    settings = crud.get_settings(db)
    if not settings:
        raise HTTPException(status_code=500, detail="Настройки не найдены")
    if not settings.is_enabled:
        raise HTTPException(status_code=400, detail="Система уже остановлена")

    crud.update_settings(db, is_enabled=False)
    await cv_client.send_stop_command()

    return crud.get_settings(db)

# ==========================================
# =========== интеграция с cv ==============
# ==========================================

@app.post("/cv/report", response_model=schemas.LogResponse)
async def receive_vision_report(report: schemas.LogCreate,db: Session = Depends(get_db),x_cv_token: Optional[str] = Header(None)):
    """Принять отчет от CV сервиса о распознанной крышке"""
    if x_cv_token != CV_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Неверный токен CV сервиса")

    settings = crud.get_settings(db)
    if not settings:
        raise HTTPException(status_code=500, detail="Настройки не найдены")

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