import os
import time
import threading
import queue
import logging
import requests
import cv2
from ultralytics import YOLO
from dotenv import load_dotenv

# Импортируем модули режимов и вебсокета
from webSocket import WebSocketClient, run_websocket_loop
from basicMode import run_yolo_mode
from emergencyMode import run_emergency_mode

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

load_dotenv()

script_dir = os.path.dirname(os.path.abspath(__file__))

# Теперь ищем модель в папке со скриптом
MODEL_PATH = os.path.join(script_dir, "best.pt")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "ws://localhost:8000/ws/cv")
CV_TOKEN = os.getenv("WS_TOKEN", "")
HTTP_REPORT_URL = os.getenv("HTTP_REPORT_URL", "http://localhost:8000/cv/report")

BACKUP_RADIUS = 70
REPORT_COOLDOWN = 3.0

COLOR_MAP = {
    "white": (255, 255, 255), "black": (30, 30, 30), "red": (0, 0, 255),
    "orange": (0, 128, 255), "yellow": (0, 255, 255), "green": (0, 255, 0),
    "sky_blue": (255, 255, 0), "blue": (255, 0, 0), "purple": (211, 0, 148),
    "pink": (180, 105, 255), "brown": (19, 69, 139)
}

RU_COLOR_NAMES = {
    "white": "БЕЛЫЙ", "black": "ЧЕРНЫЙ", "red": "КРАСНЫЙ",
    "orange": "ОРАНЖЕВЫЙ", "yellow": "ЖЕЛТЫЙ", "green": "ЗЕЛЕНЫЙ",
    "sky_blue": "ГОЛУБОЙ", "blue": "СИНИЙ", "purple": "ФИОЛЕТОВЫЙ",
    "pink": "РОЗОВЫЙ", "brown": "КОРИЧНЕВЫЙ", "unknown": "НЕИЗВЕСТНО"
}

COLOR_RANGES_HSV = {
    # БЕЛЫЙ: Строго зажат по насыщенности, чтобы не забирать цветной пластик
    "white": ((0, 0, 85), (180, 50, 255)),

    # ЧЕРНЫЙ: Глубокие тени и темный пластик
    "black": ((0, 0, 0), (180, 255, 45)),

    # КРАСНЫЙ: Забирает исходный красный, а также розовые и малиновые оттенки
    "red_1": ((0, 65, 40), (10, 255, 255)),
    "red_2": ((165, 65, 40), (180, 255, 255)),

    # ОРАНЖЕВЫЙ: Расширен вниз по яркости и насыщенности, чтобы поглотить КОРИЧНЕВЫЙ
    "orange": ((10, 50, 25), (22, 255, 255)),

    # ЖЕЛТЫЙ: Начинается сразу после оранжевого спектра
    "yellow": ((23, 55, 45), (38, 255, 255)),

    # ЗЕЛЕНЫЙ: Оптимальный диапазон для всех оттенков зеленого
    "green": ((39, 50, 40), (85, 255, 255)),

    # ГОЛУБОЙ: Светло-синие и бирюзовые объекты
    "sky_blue": ((86, 50, 60), (102, 255, 255)),

    # СИНИЙ: Темно-синий пластик, а также поглощает ФИОЛЕТОВЫЕ крышки
    "blue": ((103, 50, 35), (164, 255, 255))
}


class StateManager:
    def __init__(self):
        self.target_color = "yellow"
        self.is_enabled = False
        self.proximity_active = False
        self._lock = threading.Lock()

    def update_config(self, target_color, is_enabled):
        with self._lock:
            if target_color is not None:
                self.target_color = target_color
            if is_enabled is not None:
                self.is_enabled = is_enabled

    def update_sensor(self, proximity):
        with self._lock:
            self.proximity_active = proximity

    def get_full_state(self):
        with self._lock:
            return self.target_color, self.is_enabled, self.proximity_active


state_manager = StateManager()
report_queue = queue.Queue()


# CV_project/main.py - добавить после импортов

def send_stack_report(color, mode, target):
    """Отправляет ВСЕ найденные крышки в стек бекенда"""
    try:
        payload = {
            "detected_color": color,
            "target_color": target,
            "is_success": bool(color == target)
        }
        headers = {"X-CV-Token": CV_TOKEN}
        response = requests.post(
            "http://localhost:8000/cv/stack",
            json=payload,
            headers=headers,
            timeout=0.5
        )
        if response.status_code == 200:
            print(f"✅ Отправлено в стек: {color} -> {target}")
        else:
            print(f"⚠️ Ошибка отправки в стек: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Ошибка отправки в стек: {e}")


def draw_text_with_bg(img, text, position, font_scale, text_color, thickness=2, bg_color=(0, 0, 0), alpha=0.6):
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = position

    offset = 8
    xmin, ymin = max(0, x - offset), max(0, y - text_h - offset)
    xmax, ymax = min(img.shape[1], x + text_w + offset), min(img.shape[0], y + offset)

    # Оптимизация: берем только нужный регион (ROI) вместо копирования всего кадра
    roi = img[ymin:ymax, xmin:xmax]
    overlay = roi.copy()
    cv2.rectangle(overlay, (0, 0), (xmax - xmin, ymax - ymin), bg_color, -1)
    cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0, roi)

    cv2.putText(img, text, (x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)


# CV_project/main.py - замени функцию

def http_report_worker():
    """Фоновый поток для отправки HTTP-отчетов без просадки FPS основного цикла."""
    last_report_time = 0.0
    
    while True:
        item = report_queue.get()
        if item is None:
            break

        color, mode, target = item
        current_time = time.time()

        if current_time - last_report_time < REPORT_COOLDOWN:
            report_queue.task_done()
            continue

        last_report_time = current_time

        try:
            is_success = bool(color == target)
            payload = {
                "detected_color": color,
                "target_color": target,
                "is_success": is_success,
                "mode": mode,
                "type": "report"
            }
            
            # ===== ДОБАВЛЯЕМ ТОКЕН =====
            headers = {"X-CV-Token": CV_TOKEN}
            # ============================
            
            response = requests.post(
                HTTP_REPORT_URL, 
                json=payload, 
                headers=headers,  # ← добавляем заголовки
                timeout=1.0
            )
            
            if response.status_code == 200:
                logging.info(f"📡 Отчет отправлен -> Обнаружен: {color.upper()}, Успех: {is_success} ({mode})")
            else:
                logging.warning(f"⚠️ Ошибка отправки отчета: {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            logging.error(f"❌ Ошибка отправки HTTP отчета: {e}")

        finally:
            report_queue.task_done()


# CV_project/main.py - замени существующую функцию

def send_http_report(color, mode, target):
    """Отправляет отчет в стек и в старый эндпоинт"""
    # 1. Отправляем в НОВЫЙ стек
    send_stack_report(color, mode, target)
    
    # 2. Отправляем в старый эндпоинт (для логирования)
    try:
        report_queue.put_nowait((color, mode, target))
    except queue.Full:
        pass


def main_cv_loop():
    logging.info(f"📦 Загрузка кастомной модели YOLO: {MODEL_PATH}...")
    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Не удалось открыть камеру!")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    window_name = "Smart Split-System: YOLO + Fallback Mean"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Счетчик ошибок подряд, чтобы перезапустить камеру при полном зависании
    error_streak = 0

    try:
        while True:
            ret, frame = cap.read()

            # 1. Жесткая валидация кадра. Не просто 'not ret', а проверка содержимого
            if not ret or frame is None or frame.size == 0 or len(frame.shape) != 3:
                logging.warning("⚠️ Получен невалидный или пустой кадр. Пропуск...")
                error_streak += 1
                time.sleep(0.1)  # Даем камере и сети 100 мс на восстановление
                continue

            # Сбрасываем счетчик ошибок, если кадр валидный
            error_streak = 0

            # 2. Если камера "умерла" полностью (например, 10 ошибок подряд), пробуем переподключить
            if error_streak > 10:
                logging.error("🔄 Слишком много ошибок подряд. Попытка переподключения к камере...")
                cap.release()
                time.sleep(1.0)
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                error_streak = 0
                continue

            current_target, monitoring_active, sensor_active = state_manager.get_full_state()
            height, width, _ = frame.shape
            cx, cy = width // 2, height // 2

            # 3. Оборачиваем инференс в try-except, чтобы падение внутри YOLO/OpenCV не убило приложение
            try:
                if sensor_active:
                    detected_color, box_color = run_emergency_mode(
                        frame, cx, cy, BACKUP_RADIUS, COLOR_MAP, COLOR_RANGES_HSV,
                        current_target, send_http_report, draw_text_with_bg
                    )
                else:
                    detected_color, box_color = run_yolo_mode(
                        frame, model, current_target, COLOR_MAP, send_http_report
                    )
            except Exception as e:
                # Ловим ошибку F.interpolate или любые другие сбои обработки
                logging.error(f"❌ Ошибка обработки кадра моделью: {e}. Пропуск кадра.")
                continue  # Просто пропускаем этот "битый" кадр и идем дальше

            # Динамические координаты текста
            text_x = int(width * 0.04)
            text_y = int(height * 0.09)

            target_text_color = COLOR_MAP.get(current_target, (0, 215, 255))
            ru_target = RU_COLOR_NAMES.get(current_target, current_target.upper())

            # Проверка, что кадр все еще валиден после обработки (на всякий случай)
            if frame is not None and frame.size > 0:
                draw_text_with_bg(frame, f"Цель: {ru_target}", (text_x, text_y), 0.75, target_text_color)
                cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

    except KeyboardInterrupt:
        logging.info("Получен сигнал прерывания (Ctrl+C)")
    finally:
        logging.info("Завершение работы приложения...")
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # Запуск воркера для отчетов
    worker_thread = threading.Thread(target=http_report_worker, daemon=True)
    worker_thread.start()

    # Запуск WebSocket
    ws_client = WebSocketClient(WEBSOCKET_URL, CV_TOKEN, state_manager)
    ws_thread = threading.Thread(target=run_websocket_loop, args=(ws_client,), daemon=True)
    ws_thread.start()

    try:
        main_cv_loop()
    finally:
        # Корректное завершение при выходе
        logging.info("Завершение работы приложения...")
        report_queue.put(None)  # Останавливаем http-воркер
        if hasattr(ws_client, 'close'):
            try:
                ws_client.close()  # Закрываем вебсокет по протоколу, если метод доступен
            except Exception:
                pass
