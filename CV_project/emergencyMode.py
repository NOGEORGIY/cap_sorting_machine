import threading
import cv2
import numpy as np


def get_backup_color(roi_hsv, color_ranges_hsv):
    """
    Поиск доминантного цвета через гистограмму.
    Игнорирует QR-коды, мелкие надписи и точечные шумы.
    """
    # Создаем маску для отсечения глубоких теней фона, оставляя сам объект
    lower_bound = np.array([0, 0, 40])
    upper_bound = np.array([180, 255, 255])
    mask = cv2.inRange(roi_hsv, lower_bound, upper_bound)

    if cv2.countNonZero(mask) < 200:
        return "unknown", np.array([0, 0, 0], dtype=np.uint8)

    # Вырезаем пиксели объекта
    valid_pixels = roi_hsv[mask > 0]

    # Считаем, сколько пикселей попало в каждый цветовой диапазон
    color_counts = {}
    color_sums = {}

    for color_name, (lower, upper) in color_ranges_hsv.items():
        base_name = color_name.split('_')[0]
        if base_name not in color_counts:
            color_counts[base_name] = 0
            color_sums[base_name] = np.array([0.0, 0.0, 0.0])

        # Проверяем попадание всех пикселей в текущий диапазон
        in_range = (valid_pixels >= np.array(lower)) & (valid_pixels <= np.array(upper))
        match_mask = np.all(in_range, axis=1)
        matching_pixels = valid_pixels[match_mask]

        count = len(matching_pixels)
        if count > 0:
            color_counts[base_name] += count
            color_sums[base_name] += np.sum(matching_pixels, axis=0)

    # Находим цвет, у которого больше всего пикселей (доминанта)
    best_color = "unknown"
    max_pixels = 0
    for name, count in color_counts.items():
        if count > max_pixels and count > 100:  # Минимум 100 пикселей для уверенности
            max_pixels = count
            best_color = name

    # Если цвет найден, считаем среднее только по его пикселям
    if best_color != "unknown" and color_counts[best_color] > 0:
        avg_hsv = (color_sums[best_color] / color_counts[best_color]).astype(np.uint8)
        return best_color, avg_hsv

    # Фаллбэк на общее среднее, если доминанта не определилась
    avg_hsv = cv2.mean(roi_hsv, mask=mask)[:3]
    return "unknown", np.array(avg_hsv, dtype=np.uint8)


def run_emergency_mode(frame, cx, cy, radius, color_map, color_ranges_hsv, current_target, send_report_func,
                       draw_text_func):
    """
    Обработка кадра методом адаптивной угадайки по центральной зоне.
    """
    # Словарь перевода названий для вывода под рамкой
    ru_names_local = {
        "white": "БЕЛЫЙ", "black": "ЧЕРНЫЙ", "red": "КРАСНЫЙ",
        "orange": "ОРАНЖЕВЫЙ", "yellow": "ЖЕЛТЫЙ", "green": "ЗЕЛЕНЫЙ",
        "sky_blue": "ГОЛУБОЙ", "blue": "СИНИЙ", "purple": "ФИОЛЕТОВЫЙ",
        "pink": "РОЗОВЫЙ", "brown": "КОРИЧНЕВЫЙ", "unknown": "НЕИЗВЕСТНО"
    }

    y_start, y_end = cy - radius, cy + radius
    x_start, x_end = cx - radius, cx + radius

    # Размываем для стабилизации и переводим в HSV
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    roi_hsv = hsv[y_start:y_end, x_start:x_end]

    # Вычисляем чистый цвет без учета фона
    detected_color, avg_hsv = get_backup_color(roi_hsv, color_ranges_hsv)

    # ЛОГИКА ЦВЕТА РАМКИ: Зеленая — если угадали таргет, Красная — если брак
    if detected_color == current_target.lower():
        system_box_color = (0, 255, 0)  # Зеленый

        # Отправляем HTTP-отчет бэкенду
        threading.Thread(
            target=send_report_func,
            args=(detected_color, "MEAN_FALLBACK", current_target)
        ).start()
    else:
        system_box_color = (0, 0, 255)  # Красный

    # Рисуем центральную зону замера (цвет рамки зависит от успешности сортировки: зеленый/красный)
    cv2.rectangle(frame, (x_start, y_start), (x_end, y_end), system_box_color, 2)
    cv2.circle(frame, (cx, cy), 3, system_box_color, -1)

    # Получаем русское название распознанного цвета
    ru_detected_name = ru_names_local.get(detected_color, "НЕИЗВЕСТНО")

    # ИСПРАВЛЕНО: Динамически берем BGR оттенок для текста из карты цветов проекта
    # Если цвет неизвестен, ставим дефолтный серый (128, 128, 128)
    text_color_dynamic = color_map.get(detected_color, (128, 128, 128))

    # ВЫВОД ДВУХ СТРОК НА ТЕМНЫХ ПЛАШКАХ НАД РАМКОЙ:
    # 1 строка: Значения HSV (оставляем белым для технической четкости)
    draw_text_func(frame, f"HSV: {avg_hsv}", (x_start, y_start - 35), 0.5, (255, 255, 255), thickness=1)

    # 2 строка: Название цвета (теперь горит СВОИМ собственным динамическим цветом!)
    draw_text_func(frame, f"Цвет: {ru_detected_name}", (x_start, y_start - 10), 0.5, text_color_dynamic, thickness=2)

    return detected_color, system_box_color
