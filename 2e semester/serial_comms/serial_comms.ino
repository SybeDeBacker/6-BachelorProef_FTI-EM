#include <ESP_FlexyStepper.h>
#include "config.h"

const int dirPin = 1;
const int stepPin = 2;
const int enablePin = 7;
const int limitSwitchMin = 8;  // Minimum limit switch pin
const int limitSwitchMax = 9;  // Maximum limit switch pin

ESP_FlexyStepper stepper;

int STEPPER_PIPET_MICROSTEPS = STEPPER_PIPET_MICROSTEPS_CONFIG; // Microsteps
float LEAD = LEAD_CONFIG;               // mm/rev
float VOLUME_TO_TRAVEL_RATIO = VOLUME_TO_TRAVEL_RATIO_CONFIG; // ul/mm

String DEBUG_INFO = "";

// Volatile flags for limit switches, set by their interrupt routines
volatile bool limitSwitchMinTriggered = false;
volatile bool limitSwitchMaxTriggered = false;

// Interrupt Service Routines for limit switches
void IRAM_ATTR limitSwitchMinISR() {
  limitSwitchMinTriggered = true;
}

void IRAM_ATTR limitSwitchMaxISR() {
  limitSwitchMaxTriggered = true;
}

void setup() {
  // Disable the watchdog timer at the start
  Serial.begin(9600);
  Serial.println("Serial started");
  
  // Configure limit switch pins with internal pullup
  pinMode(limitSwitchMin, INPUT_PULLUP);
  pinMode(limitSwitchMax, INPUT_PULLUP);

  // Attach interrupts to the limit switches (assuming a FALLING edge when activated)
  attachInterrupt(digitalPinToInterrupt(limitSwitchMin), limitSwitchMinISR, FALLING);
  attachInterrupt(digitalPinToInterrupt(limitSwitchMax), limitSwitchMaxISR, FALLING);

  if (USE_STEPPER_MOTOR) {
    stepper.connectToPins(stepPin, dirPin);
    stepper.setStepsPerRevolution(200 * STEPPER_PIPET_MICROSTEPS);
    stepper.setSpeedInStepsPerSecond(2000);  // Default speed (steps per second)
    stepper.setAccelerationInStepsPerSecondPerSecond(5000);
  }
}

void loop() {
  if (Serial.available() > 0) {
    String command_str = Serial.readStringUntil('\n');
    String response = execute_command(command_str);
    if (ENABLE_DEBUG) {
      response = response.substring(0, response.length() - 1);
      response += ", \"debug_info\":\"" + DEBUG_INFO + "\"}";
    }
    Serial.println(response);
  }
  
  // Continuously update the stepper movement
  stepper.processMovement();
}

String execute_command(String data) {
  if (data.indexOf("A") == 0) {
    float aspiration_volume = data.substring(1, data.indexOf("R") - 1).toFloat();
    float aspiration_rate = data.substring(data.indexOf("R") + 1, data.length()).toFloat();
    return aspirate(aspiration_volume, aspiration_rate);
  } 
  else if (data.indexOf("D") == 0) {
    float dispense_volume = data.substring(1, data.indexOf("R") - 1).toFloat();
    float dispense_rate = data.substring(data.indexOf("R") + 1, data.length()).toFloat();
    return dispense(dispense_volume, dispense_rate);
  } 
  else if (data == "E") {
    return eject();
  } 
  else if (data.indexOf("S") == 0) {
    int microsteps = data.substring(1, data.indexOf("L") - 1).toInt();
    float lead = data.substring(data.indexOf("L") + 1, data.indexOf("V") - 1).toFloat();
    float volume_tt_ratio = data.substring(data.indexOf("V") + 1, data.length()).toFloat();

    if (microsteps > 0) STEPPER_PIPET_MICROSTEPS = microsteps;
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
    return "{\"status\":\"success\"}";
  } 
  else {
    return "{\"status\":\"error\",\"message\":\"No valid parameters given " + String(data) + "\"}";
  }
}

String aspirate(float aspiration_volume, float aspiration_rate) {
  float travel = aspiration_volume / VOLUME_TO_TRAVEL_RATIO;
  float rotations = travel / LEAD;
  int steps = round(rotations * 200 * STEPPER_PIPET_MICROSTEPS);
  // Calculate speed in revolutions per second (rps) by removing the factor of 60
  float rps = (aspiration_rate / VOLUME_TO_TRAVEL_RATIO) / LEAD;

  if (moveStepper(steps, rps)) {
    return "{\"status\":\"success\", \"message\": \"Aspirated " + String(steps) + " steps at " + String(rps) + " rps\"}";
  } else {
    return "{\"status\":\"error\", \"message\": \"Failed to aspirate " + String(steps) + " steps at " + String(rps) + " rps\"}";
  }
}

String dispense(float dispense_volume, float dispense_rate) {
  float travel = -dispense_volume / VOLUME_TO_TRAVEL_RATIO;
  float rotations = travel / LEAD;
  int steps = round(rotations * 200 * STEPPER_PIPET_MICROSTEPS);
  // Calculate speed in revolutions per second (rps)
  float rps = (dispense_rate / VOLUME_TO_TRAVEL_RATIO) / LEAD;

  if (moveStepper(steps, rps)) {
    return "{\"status\":\"success\", \"message\": \"Dispensed " + String(steps) + " steps at " + String(rps) + " rps\"}";
  } else {
    return "{\"status\":\"error\", \"message\": \"Failed to dispense " + String(steps) + " steps at " + String(rps) + " rps\"}";
  }
}

String eject() {
  return "{\"status\":\"success\"}";
}

bool moveStepper(int steps, float rps) {
  if (PRETEND_FALSE) return false;
  if (!USE_STEPPER_MOTOR) return true;

  stepper.setSpeedInRevolutionsPerSecond(rps);
  stepper.setTargetPositionRelativeInSteps(steps);

  // Wait until movement is completed or a limit switch interrupt triggers
  while (!stepper.motionComplete()) {
    stepper.processMovement();

    // Check if a limit switch has been triggered via its interrupt
    if (limitSwitchMinTriggered || limitSwitchMaxTriggered) {
      stepper.emergencyStop();
      // Clear the flags after stopping the motor
      limitSwitchMinTriggered = false;
      limitSwitchMaxTriggered = false;
      return false; // Movement stopped due to limit switch
    }
  }

  return true;
}