#include "RobotControlServer.h"
#include "RobotObject.h"
#include "utilities.h"

// Example motor control function
void MotorControlFunction(float x, float y, float z) {
  Serial.print("Moving to position: ");
  Serial.print("X="); Serial.print(x);
  Serial.print(", Y="); Serial.print(y);
  Serial.print(", Z="); Serial.println(z);
  // Add motor control logic here
}

// Custom pipet control function
void PipetControlFunction(float pipetLevel) {
    Serial.print("Setting pipet level to: ");
    Serial.println(pipetLevel);
    // Add pipet control logic here
}

// Import ssid and password from external utilities class
utilities WiFiUtils;

const char* ssid = WiFiUtils.ssid();
const char* password = WiFiUtils.password();

// Set up the WiFi or Ethernet connection
void setup_connection(){
    WiFi.begin(ssid, password);

    // Wait for connection
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());  // Print the IP address assigned to the ESP8266
}

// Create robot object as a wrapper for the Control Functions
RobotObject robot(MotorControlFunction, PipetControlFunction);

// Create the server object and pass a pointer to the robot to it. This way the server can execute the commands it receives via the Control Functions (robot Specific)
RobotControlServer server(&robot);

void setup() {
    Serial.begin(115200);
    // Connect to WiFi network
    setup_connection();
    server.begin();
}

void loop() {
    server.loop();
}
