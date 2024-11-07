#include <ESP8266WiFi.h>
#include "utilities.h"

const char* serverIP = "10.0.1.221"; // Your server's IP address
const int serverPort = 65432;

const int HEADERSIZE = 10;
int i=0;

ssid = utilities.ssid();
password = utilities.password();

int lastCommand = 0;

int lastKeepAlive = 0;
int KeepAliveInterval = 1 * 1000;

WiFiClient client;

void setup() {
  Serial.begin(115200);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED){
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
    }
    Serial.println("Connected to WiFi.");
  }

  if (client.connected() != 1) {
    Serial.println("Disconnected from server. Reconnecting...");
    connectToServer();
    String response = getData();  // Read the response
    if (response.length() > 0) {
      Serial.println("Response: " + response);
    } else {
      Serial.println("No response from server.");
    }
  }

  if ((1 == client.connected()) & ((millis() - lastKeepAlive)>KeepAliveInterval)){
    Serial.println("Keeping Alive");
    lastKeepAlive = millis();
    sendJSONCommand(createKeepAlive());
    String response = getData();  // Read the response
    if (response.length() > 0) {
      Serial.println("Response: " + response);
    } else {
      Serial.println("No response from server.");
    }
  }

  if ((1 == client.connected()) & ((millis() - lastCommand)>5000)) {
    lastCommand = millis();
    Serial.println("heyyyy");
    String command = createCommand(i*5,i*10,i*20);
    sendJSONCommand(command);  // Send command to server
    i++;
    String response = getData();  // Read the response
    if (response.length() > 0) {
      Serial.println("Response: " + response);
    } else {
      Serial.println("No response from server.");
    }
  }

  if (i>2){
    Serial.println("Stopping client");
    client.stop();
    i=0;
  }

  return;
}

void connectToServer() {
  if (client.connect(serverIP, serverPort)) {
    Serial.println("Connected to server");
  } else {
    Serial.println("Connection to server failed");
  }
}

String getData() {
  String fullMsg = "";
  bool newMsg = true;
  int msgLen = 0;

  while (client.connected()) {
    // Check if data is available
    if (client.available()) {
      // Read incoming data byte-by-byte
      char c = client.read();
      fullMsg += c;

      // Parse header on first message part
      if (newMsg && fullMsg.length() >= HEADERSIZE) {
        String header = fullMsg.substring(0, HEADERSIZE);

        // Try to convert header to integer (message length)
        msgLen = header.toInt();
        if (msgLen <= 0) {
          Serial.println("Invalid header length");
          return "";  // Return empty string on error
        }
        newMsg = false;
      }

      // Check if the entire message is received
      if (fullMsg.length() - HEADERSIZE == msgLen) {
          return fullMsg.substring(HEADERSIZE);  // Return message without header
      }
    }
  }
  // If the connection closes before full message is received
  Serial.println("Connection closed before complete message received");
  return "";  // Return empty string if incomplete
}

void sendJSONCommand(String command) {
    // Create the command string with JSON format
    int jsonLength = command.length();

    // Create a header string with fixed width of HEADERSIZE
    String header = String(jsonLength);
    while (header.length() < HEADERSIZE) {
        header += ' ';  // Pad header with spaces to reach HEADERSIZE
    }

    // Combine header and command into a single message
    String fullCommand = header + command;
    Serial.println(fullCommand);  // For debugging, print the full command

    // Send the full command (header + JSON)
    client.print(fullCommand);
}

String createCommand(int x, int y, int z) {
    // Construct the JSON command string
    String command = "{\"type\":\"move\",\"data\":{\"x\":";
    command += x;
    command += ",\"y\":";
    command += y;
    command += ",\"z\":";
    command += z;
    command += "}}";  // No newline in JSON itself; handled by header
    return command;
}

String createKeepAlive() {
  String message = "{\"type\":\"ping\"}";
  return message;
}