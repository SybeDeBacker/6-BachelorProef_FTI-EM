#include <TMCStepper.h>
#include <ESP_FlexyStepper.h>

// UART Pins (adjust if you use different ones)
#define RX_PIN 17  // ESP32 GPIO receiving from TMC2209 TX
#define TX_PIN 16  // ESP32 GPIO sending to TMC2209 RX
const int dirPin = 22;
const int stepPin = 23;
#define DRIVER_ADDRESS 0b00 // Use this if only 1 driver on UART

int STEPPER_PIPET_MICROSTEPS = 8; // Microsteps
float LEAD = 1;               // mm/rev
float VOLUME_TO_TRAVEL_RATIO = float(sq(2)*3.14159); // ul/mm

// Hardware Serial instance (Serial1 uses GPIO9 & GPIO10 by default; we override it)
HardwareSerial TMCSerial(1); // Use UART1

ESP_FlexyStepper stepper;
TMC2209Stepper driver(&TMCSerial, 0.11, DRIVER_ADDRESS);

void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println("Initializing UART with TMC2209...");
  stepper.connectToPins(stepPin, dirPin);
  stepper.setStepsPerRevolution(200 * STEPPER_PIPET_MICROSTEPS);
  stepper.setSpeedInStepsPerSecond(200*STEPPER_PIPET_MICROSTEPS);  // Default speed (steps per second)
  stepper.setAccelerationInStepsPerSecondPerSecond(200*STEPPER_PIPET_MICROSTEPS);
  stepper.setDecelerationInStepsPerSecondPerSecond(200*STEPPER_PIPET_MICROSTEPS);
  // Start serial port for TMC2209
  TMCSerial.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);

  // Initialize driver
  driver.begin();             // SPI: Init pins and register
  driver.toff(5);             // Enable driver (non-zero value)
  driver.rms_current(200);
  driver.microsteps(STEPPER_PIPET_MICROSTEPS);      // Set microsteps (e.g., 16, 32, etc.)
  driver.pdn_disable(true);   // Use UART
  driver.I_scale_analog(false); // Use internal voltage reference

  Serial.println("TMC2209 initialized.");
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
    return "{\"status\":\"success\",\"message\":\"Robot zeroed\"}";
  } 
  else {
    return "{\"status\":\"error\",\"message\":\"No valid parameters given " + String(data) + "\"}";
  }
}

String aspirate(float aspiration_volume, float aspiration_rate) {
  float travel = -aspiration_volume / VOLUME_TO_TRAVEL_RATIO;
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
  float travel = dispense_volume / VOLUME_TO_TRAVEL_RATIO;
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
  return "{\"status\":\"success\",\"message\":\"Tip Ejected\"}";
}

bool moveStepper(int steps, float rps) {
  stepper.setSpeedInRevolutionsPerSecond(rps);
  stepper.setTargetPositionRelativeInSteps(steps);

  // Wait until movement is completed or a limit switch interrupt triggers
  while (!stepper.motionComplete()) {
    stepper.processMovement();
  }

  return true;
}