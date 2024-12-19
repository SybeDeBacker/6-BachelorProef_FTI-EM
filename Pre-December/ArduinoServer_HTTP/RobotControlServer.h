#ifndef ROBOTCONTROLSERVER_H
#define ROBOTCONTROLSERVER_H

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>  // For handling HTTP requests
#include <ArduinoJson.h>
#include "RobotObject.h"  // Include the RobotObject header

class RobotControlServer {
public:
  RobotControlServer(RobotObject* robot);  // Constructor with only robot pointer
  void begin();  // Start the server
  void loop();   // Handle the HTTP requests in the loop

private:
  ESP8266WebServer server;  // HTTP server object

  RobotObject* robot;  // Pointer to the RobotObject

  // Routes for the HTTP server
  void handleMoveCommand();
  void handlePipetControl();
  void handlePing();
  void handleRequest();

  // Handle incoming commands as JSON and return a response
  String handleCommand(String command);

  // Position safety check (keeping this function for logic)
  bool isPositionSafe(float x, float y, float z);
  int getCurrent(char dimension);
};

#endif
