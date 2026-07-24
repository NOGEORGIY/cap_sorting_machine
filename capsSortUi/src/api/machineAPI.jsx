const BASE_URL = "http://localhost:8000";

// Вспомогательная функция для отправки обновлений в PUT /settings
async function updateMachineSettings(payload) {
  const response = await fetch(`${BASE_URL}/settings`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Ошибка обновления настроек системы");
  }

  return response.json();
}

// 1. ЗАПУСК СИСТЕМЫ (Передаем флаг активности)
export async function startMachine() {
  const response = await fetch(`${BASE_URL}/start`, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Ошибка запуска системы");
  }

  return response.json();
}

// 2. ОСТАНОВКА СИСТЕМЫ
export async function stopMachine() {
  const response = await fetch(`${BASE_URL}/stop`, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Ошибка остановки системы");
  }

  return response.json();
}

// 3. СМЕНА ЦВЕТА (Передаем ключ target_color, как требует ваша БД и Swagger)
export async function setMachineColor(color) {
  // Проверяем, что цвет передан
  if (!color) {
    throw new Error('Цвет не указан');
  }

  const response = await fetch(`${BASE_URL}/settings`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ target_color: color }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Ошибка отправки цвета');
  }

  return response.json();
}

// 4. СТАТУС СИСТЕМЫ (Остается без изменений)
export async function getMachineStatus() {
  const response = await fetch(`${BASE_URL}/status`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Ошибка получения статуса");
  }

  return response.json();
}

// ===== 5. ДОБАВЛЕНО: ТУМБЛЕР ДАТЧИКА ПРЕПЯТСТВИЙ (Новая фича для фронта) =====
export async function toggleProximitySensor(isActive) {
  const response = await fetch(`${BASE_URL}/api/sensor/toggle`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ proximity: isActive }),
  });

  if (!response.ok) {
    throw new Error("Ошибка отправки сигнала датчика");
  }

  return response.json();
}

// Добавьте эту функцию в существующий файл machineAPI.jsx

export async function toggleSensor(proximity) {
  const response = await fetch(`${BASE_URL}/api/sensor/toggle`, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ proximity }),
  });

  if (!response.ok) {
    throw new Error('Ошибка переключения режима датчика');
  }

  return response.json();
}