import json
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect

class CVClient:
    """Класс-клиент (WebSocket-менеджер) для отправки команд в CV-сервис"""

    def __init__(self, base_url: str = None):
        self.active_connection: Optional[WebSocket] = None

    async def connect(self, websocket: WebSocket, token: str, expected_token: str) -> bool:
        """Метод для авторизации и сохранения подключения скрипта CV"""
        if token != expected_token:
            print("Отклонено подключение к CV: неверный токен безопасности")
            return False
        
        await websocket.accept()
        self.active_connection = websocket
        print("Скрипт Компьютерного Зрения успешно подключился")
        return True

    def disconnect(self):
        """Очистка при отключении скрипта"""
        self.active_connection = None
        print("Скрипт Компьютерного Зрения отключился")

    async def _send_json(self, data: dict) -> bool:
        """Внутренний метод для безопасной и быстрой отправки JSON через WS"""
        if not self.active_connection:
            print("Ошибка связи с CV сервисом: скрипт сейчас не подключен")
            return False
        try:
            await self.active_connection.send_text(json.dumps(data))
            return True
        except Exception as e:
            print(f"Ошибка связи с CV сервисом: {e}")
            self.active_connection = None
            return False

    # ===== ОРИГИНАЛЬНЫЕ НАЗВАНИЯ МЕТОДОВ =====
    async def send_target_color(self, color: str, is_enabled: bool) -> bool:
        """Отправить команду на смену целевого цвета"""
        payload = {
            "type": "config",
            "target_color": color.lower(),
            "is_enabled": is_enabled
        }
        return await self._send_json(payload)

    async def send_start_command(self) -> bool:
        """Отправить команду запуска обработки"""
        payload = {
            "type": "config",
            "is_enabled": True
        }
        return await self._send_json(payload)

    async def send_stop_command(self) -> bool:
        """Отправить команду остановки обработки"""
        payload = {
            "type": "config",
            "is_enabled": False
        }
        return await self._send_json(payload)

    # ===== МЕТОД ДЛЯ ДАТЧИКА ПРЕПЯТСТВИЙ =====
    async def send_sensor_signal(self, proximity: bool) -> bool:
        """Отправить сигнал с датчика обнаружения препятствий (True/False)"""
        payload = {
            "type": "sensor",
            "proximity": proximity
        }
        return await self._send_json(payload)

cv_client = CVClient()
