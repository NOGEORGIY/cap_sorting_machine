# test_model.py
from ultralytics import YOLO

# Полный путь к файлу
model_path = r"C:\Users\bobyr\Desktop\cap_sorting_machine-dev\CV_project\best.pt"
print(f"🔍 Загружаю модель: {model_path}")

model = YOLO(model_path)
print("Классы модели:", model.names)