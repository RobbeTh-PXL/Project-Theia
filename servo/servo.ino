#include <Arduino.h>
#include <Servo.h>

#define YAW_START_POS 70
#define YAW_MIN_POS 0
#define YAW_MAX_POS 180

#define PITCH_START_POS 70
#define PITCH_MIN_POS 0
#define PITCH_MAX_POS 130

Servo yawServo;
Servo pitchServo;

int yawPos = YAW_START_POS;
int pitchPos = PITCH_START_POS;

void setup() {
  Serial.begin(115200);

  yawServo.attach(10, 850, 2150);
  pitchServo.attach(6, 850, 2150);

  yawServo.write(yawPos);
  pitchServo.write(pitchPos);
}

void loop() {
  while(Serial.available() > 0)
  {
    int newYawPos = Serial.parseInt();
    int newPitchPos = Serial.parseInt();

    if (Serial.read() == '\n')
    {
      yawPos = constrain(yawPos + newYawPos, YAW_MIN_POS, YAW_MAX_POS);
      pitchPos = constrain(pitchPos + newPitchPos, PITCH_MIN_POS, PITCH_MAX_POS);

      yawServo.write(yawPos);
      pitchServo.write(pitchPos);

      Serial.print(yawPos);
      Serial.print(" ");
      Serial.println(pitchPos);
    }
  }
}
