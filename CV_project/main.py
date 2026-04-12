from ultralytics import YOLO
import cv2
import asyncio
import websockets
import json
import threading
import requests
import os
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")
CV_TOKEN = os.getenv("WS_TOKEN")
HTTP_REPORT_URL = os.getenv("HTTP_REPORT_URL")

target_color = "yellow"
is_enabled = False

COLOR_MAP = {
    "white": (255, 255, 255),
    "blue": (255, 0, 0),
    "red": (0, 0, 255),
    "green": (0, 255, 0),
    "yellow": (0, 255, 255),
    "black": (0, 0, 0),
    "orange": (0, 165, 255),
    "pink": (147, 20, 255),
    "sky_blue": (235, 206, 135),
    "light_green": (144, 238, 144),
    "brown": (42, 42, 165)
}


class WebSocketClient:
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.ws = None
        self.connected = False

    async def connect(self):
        try:
            self.ws = await websockets.connect(
                self.url,
                additional_headers={"X-CV-Token": self.token}
            )
            self.connected = True
            print("✅ Подключено к бэкенду через WebSocket")
        except Exception as e:
            print(f"❌ Ошибка подключения WebSocket: {e}")
            self.connected = False

    async def listen(self):
        global target_color, is_enabled
        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "config":
                    target_color = data.get("target_color", target_color)
                    is_enabled = data.get("is_enabled", is_enabled)
                    print(f"🎯 Новый цвет: {target_color}, Включено: {is_enabled}")
        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket соединение закрыто")
            self.connected = False
        except Exception as e:
            print(f"❌ Ошибка WebSocket: {e}")
            self.connected = False

    async def send_report(self, detected_color, target, is_success):
        """Отправить отчет через WebSocket"""
        if self.connected and self.ws:
            try:
                await self.ws.send(json.dumps({
                    "type": "report",
                    "detected_color": detected_color,
                    "target_color": target,
                    "is_success": is_success
                }))
            except:
                pass

    def send_report_http(self, detected_color, target, is_success):
        """Отправить отчет через HTTP (резервный способ)"""
        try:
            requests.post(
                HTTP_REPORT_URL,
                json={
                    "detected_color": detected_color,
                    "target_color": target,
                    "is_success": is_success
                },
                headers={"X-CV-Token": self.token},
                timeout=1.0
            )
        except:
            pass


ws_client = WebSocketClient(WEBSOCKET_URL, CV_TOKEN)


def run_websocket_loop():
    """Запуск WebSocket в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def main():
        await ws_client.connect()
        if ws_client.connected:
            await ws_client.listen()

    loop.run_until_complete(main())


model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(0)

ws_thread = threading.Thread(target=run_websocket_loop, daemon=True)
ws_thread.start()

print(f"🎥 Камера запущена. Нажмите 'q' для выхода")
print(f"🎯 Целевой цвет: {target_color} (будет обновляться через WebSocket)")

report_counter = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.predict(frame, conf=0.5, verbose=False)
    target_found = False

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]

            parts = class_name.split('_')
            if len(parts) >= 2 and parts[-1] in ['up', 'down']:
                detected_color = '_'.join(parts[:-1])
            else:
                detected_color = class_name

            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            confidence = float(box.conf[0])

            is_match = detected_color.lower() == target_color.lower()
            is_success = is_match and is_enabled

            if is_match:
                target_found = True
                color_bgr = (0, 255, 0)
            else:
                color_bgr = (0, 0, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, 2)
            label = f"{class_name} {confidence:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)

            report_counter += 1
            if report_counter % 5 == 0:
                if ws_client.connected:
                    asyncio.new_event_loop().run_until_complete(
                        ws_client.send_report(detected_color, target_color, is_success)
                    )
                else:
                    ws_client.send_report_http(detected_color, target_color, is_success)

    text_color = COLOR_MAP.get(target_color.lower(), (255, 255, 255))
    status_text = "ON" if is_enabled else "OFF"
    status_color = (0, 255, 0) if is_enabled else (0, 0, 255)

    cv2.putText(frame, f"Target: {target_color}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3)
    cv2.putText(frame, f"Target: {target_color}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)

    cv2.putText(frame, f"Status: {status_text}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3)
    cv2.putText(frame, f"Status: {status_text}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

    cv2.putText(frame, f"WS: {'Connected' if ws_client.connected else 'Disconnected'}",
                (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (0, 255, 0) if ws_client.connected else (0, 0, 255), 2)

    cv2.imshow("Cap Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()