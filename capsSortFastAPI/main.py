from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from enum import Enum
import uvicorn
from typing import Optional

app = FastAPI(
    title="API для сортировки крышек",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Color(str, Enum):
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    LBLUE = "lightblue"
    BLUE = "blue"
    WHITE = "white"
    BLACK = "black"

# Модели для запросов и ответов
class ColorChangeRequest(BaseModel):
    color: Color

class StatusResponse(BaseModel):
    status: str
    message: str
    current_color: Optional[Color] = None


class AppState:
    def __init__(self):
        self.is_running = False
        self.current_color = Color.BLUE

state = AppState()

# Эндпоинт для смены цвета
@app.post("/change-color", response_model=StatusResponse)
async def change_color(request: ColorChangeRequest):
    state.current_color = request.color
    return StatusResponse(
        status="OK",
        message=f"Цвет изменен на {request.color.value}",
        current_color=state.current_color
    )

# Эндпоинт для запуска процесса сортировки
@app.post("/start", response_model=StatusResponse)
async def start_sorting():
    if state.is_running:
        raise HTTPException(status_code=400, detail="Процесс уже запущен")

    state.is_running = True
    return StatusResponse(
        status="OK",
        message="Сортировка запущена",
        current_color=state.current_color
    )

# Эндпоинт для остановки процесса сортировки
@app.post("/stop", response_model=StatusResponse)
async def stop_sorting():
    if not state.is_running:
        raise HTTPException(status_code=400, detail="Процесс не запущен")

    state.is_running = False
    return StatusResponse(
        status="OK",
        message="Сортировка остановлена",
        current_color=state.current_color
    )

# Эндпоинт для получения текущего состояния
@app.get("/status", response_model=StatusResponse)
async def get_status():
    return StatusResponse(
        status="OK" if state.is_running else "STOPPED",
        message="Система работает" if state.is_running else "Система остановлена",
        current_color=state.current_color
    )

# Корневой эндпоинт для проверки
@app.get("/")
async def root():
    return {
        "message": "API для сортировки крышек",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "change_color": {
                "url": "/change-color",
                "method": "POST",
                "description": "Смена цвета сортировки",
                "body": {
                    "color": "синий | красный | зеленый | желтый | черный"
                }
            },
            "start": {
                "url": "/start",
                "method": "POST",
                "description": "Запуск процесса сортировки"
            },
            "stop": {
                "url": "/stop",
                "method": "POST",
                "description": "Остановка процесса сортировки"
            },
            "status": {
                "url": "/status",
                "method": "GET",
                "description": "Получение текущего статуса"
            }
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

# Точка входа для запуска приложения
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )