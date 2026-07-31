#include "SoftServo.h"

SoftServo myservo;

void setup() {
  Serial.begin(115200);
  myservo.attach(5);
  pinMode(16, INPUT_PULLUP);
  
  // asyncMode - вызов tick не блокирует код на величину импульса (0.7-2.5 мс)
  // но работа будет нестабильной при наличии задержек в коде
  // в этом режиме tick вернёт true на период импульса, можно запрещать
  // тяжёлые функции на этот период 
  //myservo.asyncMode();
  
  //delayMode - вызов tick блокирует код на величину импульса (0.7-2.5 мс) - по умолчанию  
  myservo.delayMode();  
  myservo.write(180);
}

int val = 0;
bool flag_moving = false;
// Глобальные переменные (добавить в начало скетча):
bool waiting_for_delay = false; // Флаг ожидания 2 секунд
uint32_t tmr = 0;               // Таймер для задержки

void loop() {
  myservo.tick();
  static uint32_t tmr_press;
  bool signal = !digitalRead(16); 
  bool flag_pressed = signal;  

  // --- Логика нажатия кнопки ---
  if (flag_pressed) {
    if (millis() - tmr_press >= 1000 && !flag_moving){
      tmr_press = millis();
      Serial.print("tmr_press: ");
      Serial.println(tmr_press);
    }
    if (millis() - tmr_press >= 250 && !flag_moving){
      flag_moving = true;
      Serial.println("moving");
    }
  }

  // --- Логика отпускания кнопки ---
  if (!flag_pressed && flag_moving){
    Serial.println("Push!");
    flag_moving = false;
    myservo.write(0);
    
    // Запускаем режим ожидания
    waiting_for_delay = true;
    tmr = millis(); 
  }

  // --- Логика отложенного действия (выполняется в каждом цикле) ---
  if (waiting_for_delay) {
    if (millis() - tmr >= 1000) {
      Serial.println("LOL");
      myservo.write(170);
      waiting_for_delay = false; // Завершаем ожидание
    }
  }
}