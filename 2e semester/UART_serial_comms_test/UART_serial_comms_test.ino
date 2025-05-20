#include <TMCStepper.h>
#include <ESP_FlexyStepper.h>
#include "config.h"

// UART Pins
#define RX_PIN 17  // ESP32 GPIO receiving from TMC2209 TX
#define TX_PIN 16  // ESP32 GPIO sending to TMC2209 RX
#define LimitSwitch 19
const int dirPin = 22;
const int stepPin = 23;
#define DRIVER_ADDRESS 0b00 // Only 1 driver on UART

float CALIBRATION_OFFSET = 13.5;
int STEPPER_PIPET_MICROSTEPS = STEPPER_PIPET_MICROSTEPS_CONFIG;
float LEAD = LEAD_CONFIG;
float VOLUME_TO_TRAVEL_RATIO = VOLUME_TO_TRAVEL_RATIO_CONFIG;

HardwareSerial TMCSerial(1);

ESP_FlexyStepper stepper;
TMC2209Stepper driver(&TMCSerial, 0.11, DRIVER_ADDRESS);

void setup() {
  Serial.begin(115200);
  while (!Serial);

  stepper.connectToPins(stepPin, dirPin);
  stepper.setStepsPerRevolution(200 * STEPPER_PIPET_MICROSTEPS);
  stepper.setSpeedInStepsPerSecond(200 * STEPPER_PIPET_MICROSTEPS);
  stepper.setAccelerationInStepsPerSecondPerSecond(200 * STEPPER_PIPET_MICROSTEPS);
  stepper.setDecelerationInStepsPerSecondPerSecond(200 * STEPPER_PIPET_MICROSTEPS);

  TMCSerial.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);

  driver.begin();
  driver.toff(5);
  driver.rms_current(150);
  driver.microsteps(STEPPER_PIPET_MICROSTEPS);
  driver.pdn_disable(true);
  driver.I_scale_analog(false);

  // Enable StallGuard (sensorless stall detection)
  /*
  driver.TCOOLTHRS(0xFFFFF);
  driver.semin(5);
  driver.semax(2);
  driver.sedn(0b01);
  */

  pinMode(LimitSwitch, INPUT_PULLUP);
}

void loop() {
  if (Serial.available() > 0) {
    String command_str = Serial.readStringUntil('\n');
    String response = execute_command(command_str);
    Serial.println(response);
  }
  stepper.processMovement();
}

String execute_command(String data) {
  if (data.indexOf("A") == 0) {
    float aspiration_volume = data.substring(1, data.indexOf("R")).toFloat();
    float aspiration_rate = data.substring(data.indexOf("R") + 1, data.length()).toFloat();
    return aspirate(aspiration_volume, aspiration_rate);
  } 
  else if (data.indexOf("D") == 0) {
    float dispense_volume = data.substring(1, data.indexOf("R")).toFloat();
    float dispense_rate = data.substring(data.indexOf("R") + 1, data.length()).toFloat();
    return dispense(dispense_volume, dispense_rate);
  } 
  else if (data == "E") {
    return eject();
  } 
  else if (data.indexOf("S") == 0) {
    int microsteps = data.substring(1, data.indexOf("L")).toInt();
    float lead = data.substring(data.indexOf("L") + 1, data.indexOf("V")).toFloat();
    float volume_tt_ratio = data.substring(data.indexOf("V") + 1, data.length()).toFloat();

    if (microsteps > 0) {
      STEPPER_PIPET_MICROSTEPS = microsteps;
      driver.microsteps(microsteps);
      stepper.setStepsPerRevolution(200 * STEPPER_PIPET_MICROSTEPS);
      stepper.setSpeedInStepsPerSecond(200 * STEPPER_PIPET_MICROSTEPS);
      stepper.setAccelerationInStepsPerSecondPerSecond(200 * STEPPER_PIPET_MICROSTEPS);
      stepper.setDecelerationInStepsPerSecondPerSecond(200 * STEPPER_PIPET_MICROSTEPS);
    }
    if (lead > 0) LEAD = lead;
    if (volume_tt_ratio > 0) VOLUME_TO_TRAVEL_RATIO = volume_tt_ratio;

    return "{\"status\":\"success\",\"message\":\"Microsteps " + String(STEPPER_PIPET_MICROSTEPS) +
           " Lead " + String(LEAD, 2) + "mm/rev Volume to travel ratio " + 
           String(VOLUME_TO_TRAVEL_RATIO, 2) + " ul/mm\"}";
  } 
  else if (data == "Ping") {
    return "{\"status\":\"success\",\"message\":\"pong\"}";
  } 
  else if (data == "Z") {
    return zero_robot();
  } 
  else if (data.indexOf("O") == 0) {
    CALIBRATION_OFFSET = data.substring(1, data.length()).toFloat();
    return "{\"status\":\"success\",\"message\":\"Volume offset set to " + String(CALIBRATION_OFFSET) +" ul\"}";
  }
  else {
    return "{\"status\":\"error\",\"message\":\"No valid parameters given " + String(data) + "\"}";
  }
}

String aspirate(float aspiration_volume, float aspiration_rate) {
  float travel = -(aspiration_volume + CALIBRATION_OFFSET) / VOLUME_TO_TRAVEL_RATIO;
  float rotations = travel / LEAD;
  int steps = round(rotations * 200 * STEPPER_PIPET_MICROSTEPS);
  float rps = (aspiration_rate / VOLUME_TO_TRAVEL_RATIO) / LEAD;

  if (moveStepper(steps, rps)) {
    return "{\"status\":\"success\", \"message\": \"Aspirated " + String(steps) + " steps at " + String(rps) + " rps\"}";
  } else {
    return "{\"status\":\"error\", \"message\": \"Failed to aspirate " + String(steps) + " steps at " + String(rps) + " rps\"}";
  }
}

String dispense(float dispense_volume, float dispense_rate) {
  float travel = (dispense_volume + CALIBRATION_OFFSET) / VOLUME_TO_TRAVEL_RATIO;
  float rotations = travel / LEAD;
  int steps = round(rotations * 200 * STEPPER_PIPET_MICROSTEPS);
  float rps = (dispense_rate / VOLUME_TO_TRAVEL_RATIO) / LEAD;

  if (moveStepper(steps, rps)) {
    return "{\"status\":\"success\", \"message\": \"Dispensed " + String(steps) + " steps at " + String(rps) + " rps\"}";
  } else {
    return "{\"status\":\"error\", \"message\": \"Failed to dispense " + String(steps) + " steps at " + String(rps) + " rps\"}";
  }
}

String eject() {
  return "{\"status\":\"success\",\"message\":\"Tip Ejected\"}";
}

bool moveStepper(int steps, float rps) {
  stepper.setSpeedInRevolutionsPerSecond(rps);
  stepper.setTargetPositionRelativeInSteps(steps);

  while (!stepper.motionComplete()) {
    // Limit switch check
    if ((!digitalRead(LimitSwitch) == 1) && (steps > 0)) {
      stepper.emergencyStop();
      return false;
    }

    /*
    // Stall detection check
    uint16_t sg_result = driver.SG_RESULT();
    if (sg_result < 500) {  // Adjust threshold as needed
      stepper.emergencyStop();
      Serial.println("Stall detected!");
      return false;
    }
    */
    stepper.processMovement();
  }

  return true;
}

String zero_robot() {
  stepper.setSpeedInRevolutionsPerSecond(2);
  stepper.setTargetPositionRelativeInSteps(100000 * (STEPPER_PIPET_MICROSTEPS / 8));

  while (!stepper.motionComplete()) {
    if (!digitalRead(LimitSwitch) == 1) {
      stepper.setCurrentPositionAsHomeAndStop();
      break;
    }
    stepper.processMovement();
  }

  if (digitalRead(LimitSwitch) == 1) {
    return "{\"status\":\"error\",\"message\":\"Failed to zero robot\"}";
  }

  stepper.setSpeedInRevolutionsPerSecond(0.5);
  stepper.setTargetPositionRelativeInSteps(-2000 * STEPPER_PIPET_MICROSTEPS);
  delay(10);
  while (!stepper.motionComplete()) {
    if (digitalRead(LimitSwitch) == 1) {
      stepper.setCurrentPositionAsHomeAndStop();
      return "{\"status\":\"success\",\"message\":\"Robot zeroed\"}";
    }
    stepper.processMovement();
  }
  return "{\"status\":\"error\",\"message\":\"Failed to zero robot\"}";
}
