import cv2
import numpy as np
from collections import Counter

# Хранилище истории цветов для каждой крышки по её ID
_track_history = {}
_reported_ids = set()

# Интерактивный FIFO стек для отображения на экране (максимум 7 элементов)
_display_stack = []


def run_yolo_mode(frame, model, current_target, color_map, send_report_func):
    """
    Конвейерный трекинг с интерактивным FIFO-стеком внизу экрана.
    """
    global _track_history, _reported_ids, _display_stack

    detected_colors = []
    box_colors = []
    height, width, _ = frame.shape

    # Инференс с трекером
    device_type = "mps" if cv2.ocl.haveOpenCL() else "cpu"
    results = model.track(frame, imgsz=320, conf=0.35, verbose=False, persist=True, device=device_type)

    current_ids = set()
    if results and len(results) > 0 and results[0].boxes is not None:
        boxes = results[0].boxes

        if boxes.id is not None:
            track_ids = boxes.id.cpu().numpy().astype(int).tolist()
        else:
            track_ids = [None] * len(boxes)

        for i, box in enumerate(boxes):
            # ИСПРАВЛЕНО: Добавлен индекс, чтобы убрать вложенность списков
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

            class_id = int(box.cls.item())
            raw_class_name = model.names.get(class_id, "unknown").lower()

            # Маппинг цвета
            det_color = raw_class_name.split('_')[0]
            if det_color == "brown":
                det_color = "orange"
            elif det_color == "pink":
                det_color = "red"
            elif det_color == "purple":
                det_color = "blue"

            obj_id = track_ids[i]

            if obj_id is not None:
                current_ids.add(obj_id)
                if obj_id not in _track_history:
                    _track_history[obj_id] = []

                _track_history[obj_id].append(det_color)
                if len(_track_history[obj_id]) > 7:
                    _track_history[obj_id].pop(0)

                # Голосование за стабильный цвет
                votes = Counter(_track_history[obj_id])
                stable_color = votes.most_common(1)[0][0]
            else:
                stable_color = det_color

            # Добавление в FIFO стек при подтверждении (минимум 4 кадра трека)
            if obj_id is not None and obj_id not in _reported_ids:
                if len(_track_history[obj_id]) >= 4:
                    send_report_func(stable_color, "YOLO_TRACK", current_target)
                    _reported_ids.add(obj_id)

                    # Добавляем в интерактивный стек отображения
                    _display_stack.append((obj_id, stable_color))
                    if len(_display_stack) > 7:
                        _display_stack.pop(0)  # Выталкиваем старую крышку слева

            # Отрисовка рамки объекта
            box_color = (0, 255, 0) if stable_color == current_target.lower() else (0, 0, 255)
            detected_colors.append(stable_color)
            box_colors.append(box_color)

            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
            label = f"ID:{obj_id} {stable_color.upper()}" if obj_id else stable_color.upper()
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2, cv2.LINE_AA)

    # Отрисовка интерактивного FIFO стека внизу экрана
    if _display_stack:
        panel_height = 60
        cv2.rectangle(frame, (0, height - panel_height), (width, height), (30, 30, 30), -1)
        cv2.putText(frame, "STACK FIFO:", (15, height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1,
                    cv2.LINE_AA)

        start_x = 130
        radius = 18
        spacing = 50

        for idx, (idx_id, idx_color) in enumerate(_display_stack):
            cx = start_x + idx * spacing
            cy = height - 30

            circle_color = color_map.get(idx_color, (128, 128, 128))

            if idx_color == "white":
                cv2.circle(frame, (cx, cy), radius, circle_color, -1)
                cv2.circle(frame, (cx, cy), radius, (100, 100, 100), 1)
                text_color = (0, 0, 0)
            else:
                cv2.circle(frame, (cx, cy), radius, circle_color, -1)
                text_color = (255, 255, 255) if idx_color in ["black", "blue", "purple"] else (0, 0, 0)

            id_text = str(idx_id)
            (t_w, t_h), _ = cv2.getTextSize(id_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            tx = cx - t_w // 2
            ty = cy + t_h // 2
            cv2.putText(frame, id_text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1, cv2.LINE_AA)

    # Чистка старых треков
    for old_id in list(_track_history.keys()):
        if old_id not in current_ids:
            _track_history.pop(old_id, None)

    if not detected_colors:
        return "unknown", (128, 128, 128)

    return detected_colors[-1], box_colors[-1]
