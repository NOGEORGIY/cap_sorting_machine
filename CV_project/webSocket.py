import asyncio
import websockets
import json


class WebSocketClient:
    def __init__(self, url, token, state_manager):
        self.url = url
        self.token = token
        self.state = state_manager
        self.ws = None
        self.connected = False

    async def connect(self):
        try:
            self.ws = await websockets.connect(
                self.url,
                additional_headers={"X-CV-Token": self.token},
                ping_interval=20,
                ping_timeout=10
            )
            self.connected = True
            print("✅ Подключено к бэкенду через WebSocket", flush=True)
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения WebSocket: {e}", flush=True)
            self.connected = False
            return False

    async def listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("type")

                # 1. Обработка конфигурации цвета с бэкенда/фронтенда
                if msg_type == "config":
                    target_color = data.get("target_color")
                    is_enabled = data.get("is_enabled")
                    self.state.update_config(target_color=target_color, is_enabled=is_enabled)
                    print(f"🎯 Новый таргет: {target_color}, Статус: {'ON' if is_enabled else 'OFF'}", flush=True)

                # 2. Мгновенная обработка сигнала физического датчика
                elif msg_type == "sensor":
                    proximity = data.get("proximity", False)
                    self.state.update_sensor(proximity)
                    print(f"🚨 Сигнал датчика изменен -> Препятствие: {proximity}", flush=True)

        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket connection closed", flush=True)
            self.connected = False
        except Exception as e:
            print(f"❌ Ошибка во время прослушивания WebSocket: {e}", flush=True)
            self.connected = False


def run_websocket_loop(client):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def main():
        while True:
            if not client.connected:
                await client.connect()
            if client.connected:
                await client.listen()
            await asyncio.sleep(3)

    loop.run_until_complete(main())
    loop.close()
