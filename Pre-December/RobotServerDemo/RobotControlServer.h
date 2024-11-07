#ifndef ROBOTCONTROLSERVER_H
#define ROBOTCONTROLSERVER_H

#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include "RobotObject.h" // Include the RobotObject header

class RobotControlServer {
public:
  RobotControlServer(RobotObject* robot);
  void begin();
  void loop();

private:
  static const int MAX_CLIENTS = 5;
  const char* ssid;
  const char* password;
  WiFiServer server;
  WiFiClient clients[MAX_CLIENTS];
  unsigned long lastKeepAlive[MAX_CLIENTS];
  bool connected[MAX_CLIENTS] = {false, false, false, false, false};
  bool connected_old[MAX_CLIENTS];

  const int HEADERSIZE = 10;
  const int KeepAliveInterval = 30;

  RobotObject* robot; // Pointer to the RobotObject

  void handleClient(int index);
  String readMessage(WiFiClient& client);
  void sendResponse(WiFiClient& client, String message);
  String handleCommand(String command, int clientIndex);
  bool isPositionSafe(float x, float y, float z);
  int getCurrent(char dimension);
};

#endif
