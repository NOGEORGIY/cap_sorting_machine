const BASE_URL = "http://localhost:8000";

export async function startMachine() {
  const response = await fetch(`${BASE_URL}/start`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Ошибка запуска системы");
  }

  return response;
}

export async function stopMachine() {
  const response = await fetch(`${BASE_URL}/stop`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Ошибка остановки системы");
  }

  return response;
}

export async function getMachineStatus() {
  const response = await fetch(`${BASE_URL}/status`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Ошибка получения статуса");
  }

  return response;
}
export async function setMachineColor(color) {
  const response = await fetch(`${BASE_URL}/change-color`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ color }),
  })

  if (!response.ok) {
    throw new Error('Ошибка отправки цвета')
  }

  return response.json()
}
