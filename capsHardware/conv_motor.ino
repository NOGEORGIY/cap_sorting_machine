
const uint8_t PIN_1A = 3; // скорость
const uint8_t PIN_1B = 1; // направление

const uint8_t MOTOR_SPEED = 80;
bool flag_moving = true;

void setup()
{
  Serial.begin(115200);

  pinMode(PIN_1A, OUTPUT);
  pinMode(PIN_1B, OUTPUT);

  digitalWrite(PIN_1B, LOW);
  analogWrite(PIN_1A, MOTOR_SPEED);
}

void loop()
{
  // В разработке :D
}
// --- Централизованная логика выполнения (защищена замком) ---
void attemptExecution()
{
  // ЖЕСТКИЙ ЗАМОК: если уже что-то выполняется или система выключена, игнорируем запрос
  if (isExecuting || !isSystemActive)
  {
    Serial.println("[SYS] Запрос отклонен: система занята или выключена");
    return;
  }

  if (currentTaskIndex >= queueCount)
  {
    Serial.println("[SYS] Очередь пуста или завершена");
    return;
  }

  // Блокируем новые запросы
  isExecuting = true;

  Task current = taskQueue[currentTaskIndex];
  Serial.print("[SYS] Обработка: Шаг ");
  Serial.print(current.stepNumber);

  if (current.doPush)
  {
    Serial.println(" -> ВЫПОЛНЯЮ ТОЛЧОК");
    waiting_for_return = true;
    tmr_push = millis();
    stepper.setSpeed(SLOW_SPEED);
    myservo.write(180);
    // Замок isExecuting снимется только после возврата сервопривода
  }
  else
  {
    Serial.println(" -> ИГНОР (без толчка)");
    // При игноре замок снимается мгновенно, шаг просто пропускается
    currentTaskIndex++;
    isExecuting = false;
  }
}

void setup()
{
  Serial.begin(115200);

  WiFi.mode(WIFI_AP);
  WiFi.softAP(ap_ssid, ap_password);
  IPAddress myIP = WiFi.softAPIP();
  Serial.println("Точка доступа создана!");
  Serial.print("IP-адрес: http://");
  Serial.println(myIP);

  stepper.setRunMode(KEEP_SPEED);
  stepper.setAcceleration(ACCELERATION);
  stepper.setSpeed(0);

  myservo.asyncMode();
  myservo.attach(0);
  myservo.write(0);

  pinMode(16, INPUT_PULLDOWN_16);

  server.on("/", handleRoot);
  server.on("/start", handleStart);
  server.on("/stop", handleStop);
  server.on("/add", handleAdd);
  server.on("/clear", handleClear);
  server.on("/execute", handleExecute);
  server.begin();
  Serial.println("Веб-сервер запущен");
}

void loop()
{
  server.handleClient();
  stepper.tick();
  myservo.tick();

  // --- Надежная обработка физической кнопки с защитой от помех (Debounce) ---
  int reading = digitalRead(16);

  if (reading != lastButtonState)
  {
    lastDebounceTime = millis(); // Сброс таймера при любом изменении сигнала
  }

  if ((millis() - lastDebounceTime) > debounceDelay)
  {
    if (reading != currentButtonState)
    {
      currentButtonState = reading;

      // Если кнопка была нажата (HIGH для INPUT_PULLDOWN_16)
      if (currentButtonState == HIGH)
      {
        Serial.println("[BTN] Физическое нажатие (подтвержденное)");
        attemptExecution(); // Используем ту же защищенную функцию
      }
    }
  }
  lastButtonState = reading;

  // --- Логика возврата толкателя ---
  if (waiting_for_return)
  {
    if (millis() - tmr_push >= 600)
    {
      myservo.write(0);

      if (isSystemActive)
      {
        stepper.setSpeed(NORMAL_SPEED);
      }
      else
      {
        stepper.setSpeed(0);
      }

      waiting_for_return = false;
      currentTaskIndex++;
      isExecuting = false; // СНИМАЕМ ЗАМОК только после полного завершения цикла
      Serial.println("[SYS] Толчок завершен, переход к следующему шагу");
    }
  }

  if (!isSystemActive && !waiting_for_return)
  {
    stepper.setSpeed(0);
  }
}