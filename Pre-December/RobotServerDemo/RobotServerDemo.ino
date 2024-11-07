#include "MyWiFiServer.h"
#include "utilities.h"

// Example motor control function
void moveMotors(float x, float y, float z) {
    // Your motor control logic goes here
    Serial.print("In ino script: Moving motors to X: ");
    Serial.print(x);
    Serial.print(" Y: ");
    Serial.print(y);
    Serial.print(" Z: ");
    Serial.println(z);
}

MyWiFiServer myServer(ssid, password, *moveMotors); // Create an instance of MyWiFiServer

void setup() {
    myServer.begin(); // Start the server
}

void loop() {
    myServer.loop(); // Handle server logic
}
