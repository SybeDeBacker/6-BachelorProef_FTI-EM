#ifndef MYWIFISERVER_H
#define MYWIFISERVER_H

#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// Define the function pointer type for motor control
typedef void (*MotorControlFunction)(float x, float y, float z);

class MyWiFiServer {
public:
    MyWiFiServer(const char* ssid, const char* password, MotorControlFunction moveFunction);
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
    MotorControlFunction moveFunction; // Store the function pointer

    void handleClient(int index);
    String readMessage(WiFiClient& client);
    void sendResponse(WiFiClient& client, String message);
    String handleCommand(String command, int clientIndex);
    bool isPositionSafe(float x, float y, float z);
    int getCurrent(char dimension);
};

#endif // MYWIFISERVER_H
