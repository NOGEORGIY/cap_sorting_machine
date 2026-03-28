import httpx
from datetime import datetime

CV_SERVICE_URL = "http://127.0.0.1:5000"
CV_SERVICE_TIMEOUT = 5.0

class CVClient:
    """HTTP-клиент для отправки команд в CV-сервис"""

    def __init__(self, base_url: str = CV_SERVICE_URL):
        self.base_url = base_url
        self.timeout = httpx.Timeout(CV_SERVICE_TIMEOUT)

    async def send_target_color(self, color: str, is_enabled: bool) -> bool:
        """Отправить команду на смену целевого цвета"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/cv/config",
                    json={
                        "target_color": color,
                        "is_enabled": is_enabled,
                    }
                )
                response.raise_for_status()
                return True
            except (httpx.HTTPError, httpx.ConnectError) as e:
                print(f"⚠️ Ошибка связи с CV сервисом: {e}")
                return False

    async def send_start_command(self) -> bool:
        """Отправить команду запуска обработки"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(f"{self.base_url}/cv/start")
                response.raise_for_status()
                return True
            except (httpx.HTTPError, httpx.ConnectError):
                return False

    async def send_stop_command(self) -> bool:
        """Отправить команду остановки обработки"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(f"{self.base_url}/cv/stop")
                response.raise_for_status()
                return True
            except (httpx.HTTPError, httpx.ConnectError):
                return False

# Глобальный экземпляр клиента
cv_client = CVClient()