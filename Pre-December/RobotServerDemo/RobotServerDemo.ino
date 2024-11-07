#include "MyWiFiServer.h"
#include "RobotObject.h"
#include "utilities.h"

// Example motor control function
void myMotorControlFunction(float x, float y, float z) {
    Serial.print("Moving to position: ");
    Serial.print("X="); Serial.print(x);
    Serial.print(", Y="); Serial.print(y);
    Serial.print(", Z="); Serial.println(z);
    // Add motor control logic here
}

// Custom pipet control function
void myPipetControlFunction(float pipetLevel) {
    Serial.print("Setting pipet level to: ");
    Serial.println(pipetLevel);
    // Add pipet control logic here
}

RobotObject robot(myMotorControlFunction, myPipetControlFunction);
MyWiFiServer server(ssid, password, &robot);

void setup() {
    Serial.begin(115200);
    server.begin();
}

void loop() {
    server.loop();
}
