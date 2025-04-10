//Ports used in the Arduino 
const int buzzerPin = 3;
const int greenLedPin = 8;
const int redLedPin = 9;

char lastPosture = 'x';
bool buzzerOn = false;

void setup() {
  pinMode(buzzerPin, OUTPUT);
  pinMode(greenLedPin, OUTPUT);
  pinMode(redLedPin, OUTPUT);
  Serial.begin(9600);
}

void playMelody() {
  tone(buzzerPin, 880);  delay(150);
  tone(buzzerPin, 988);  delay(150);
  tone(buzzerPin, 1047); delay(300);
  noTone(buzzerPin);
}

void loop() {
  if (Serial.available()) {
    char input = Serial.read();

    // From bad posture to good posture --> play music
    if (input == '0' && lastPosture == '1') {
      playMelody();
    }
    //Bad posture
    if (input == '1') {
      if (!buzzerOn) {
        tone(buzzerPin, 1000);
        buzzerOn = true;
      }
      digitalWrite(redLedPin, HIGH);
      digitalWrite(greenLedPin, LOW);
    } 
    //Good posture
    else if (input == '0') {
      noTone(buzzerPin);
      buzzerOn = false;
      digitalWrite(redLedPin, LOW);
      digitalWrite(greenLedPin, HIGH);
    } 
    else if (input == 'x') {
      // Shut down everything
      noTone(buzzerPin);
      buzzerOn = false;
      digitalWrite(redLedPin, LOW);
      digitalWrite(greenLedPin, LOW);
    }

    lastPosture = input;
  }
}
