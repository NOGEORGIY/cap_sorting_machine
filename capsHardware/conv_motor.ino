
const uint8_t PIN_1A = 3; // скорость
const uint8_t PIN_1B = 1; // направление

const uint8_t MOTOR_SPEED = 80; 
bool flag_moving = true;

void setup() {
  Serial.begin(115200);
  
  pinMode(PIN_1A, OUTPUT);
  pinMode(PIN_1B, OUTPUT);

  digitalWrite(PIN_1B, LOW);      
  analogWrite(PIN_1A, MOTOR_SPEED); 
}

void loop() {
 //В разработке :D
}