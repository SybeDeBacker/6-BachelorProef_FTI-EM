#include "RobotControlServer.h"

RobotControlServer::RobotControlServer(RobotObject* robot)
  : server(65432), robot(robot) {}

void RobotControlServer::begin() {
  Serial.begin(115200);

  server.begin(); // Start the server
  Serial.print("\nServer started. Waiting for clients at: ");
  Serial.println((WiFi.localIP()).toString()+":"+String(server.port()));
  Serial.println("Is er? | Connected? | Available?");
}

void RobotControlServer::loop() {
  // Check for incoming clients and add them to the client array
  WiFiClient newClient = server.available();
  if (newClient) {
    bool added = false;
    for (int i = 0; i < MAX_CLIENTS; i++) {
      if (!clients[i]) {  // Find an empty slot
        clients[i] = newClient;
        lastKeepAlive[i] = millis();
        Serial.println("New client connected");
        sendResponse(clients[i], "Connection established: " + String(i+1));
        added = true;
        break;
      }
    }
    if (!added) {
      Serial.println("Max clients reached. Connection refused.");
      newClient.println("Max clients reached. Connection refused.");
      delay(500);
      newClient.stop(); // Refuse connection if the array is full
    }
  }
    
  // Handle each connected client
  for (int i = 0; i < MAX_CLIENTS; i++) {
    connected_old[i] = connected[i];
    connected[i] = clients[i].connected();

    if (connected_old[i] != connected[i]) {
      for (int j = 0; j < MAX_CLIENTS; j++) {
        Serial.print("Client " + String(j) + ":");
        Serial.println(String(clients[j]) + "|" + String(clients[j].connected()) + "|" + String(connected[j]));
      }
      if (!clients[i].connected()) {
        Serial.println("Connection " + String(i) + " ended by user.");
      }
    }

    if (!clients[i].connected()) {
      clients[i].stop();
      clients[i] = WiFiClient(); // Reset the client slot
    }
    
    handleClient(i);
  }
}

void RobotControlServer::handleClient(int i) {
  if (clients[i]) {
    if (clients[i].connected()) {
      // Process client messages if available
      if (clients[i].available()) {
        String command = readMessage(clients[i]); // Read incoming message
        Serial.println("Command received: " + command);
                
        String response = handleCommand(command, i); // Handle command
        sendResponse(clients[i], response); // Send response to client
        Serial.println("Response sent: " + response);
      }
            
      // Check for inactivity and disconnect inactive clients
      if (millis() - lastKeepAlive[i] > KeepAliveInterval * 1000) {
        Serial.println("Timeout: Closing connection due to inactivity.");
        clients[i].stop();
        clients[i] = WiFiClient(); // Reset client slot
      }
    }
    if (!clients[i].connected()) {
      // Clean up disconnected clients
      clients[i].stop();
      clients[i] = WiFiClient();
      Serial.print("Client " + String(i) + ":");
      Serial.println(String(clients[i]) + "|" + String(clients[i].connected()) + "|" + String(clients[i].available()));
      Serial.println("Client disconnected.");
    }
  }
}

// Function to read a message from the client
String RobotControlServer::readMessage(WiFiClient& client) {
  String message;
  while (client.available()) {
    char c = client.read(); // Read characters one by one
    message += c;
  }
  message = message.substring(HEADERSIZE);
  return message;
}

// Function to send a response to the client
void RobotControlServer::sendResponse(WiFiClient& client, String message) {
  int messageLength = message.length();
  String header = String(messageLength) + String("                   ").substring(0 + String(messageLength).length(), HEADERSIZE); // Create header
  client.print(header + message); // Send header and message
}

// Function to handle incoming commands and return a response
String RobotControlServer::handleCommand(String command, int clientIndex) {
    StaticJsonDocument<200> doc; // Adjust size as needed
    DeserializationError error = deserializeJson(doc, command);

    if (error) {
        return "Error: Invalid command format"; // Error handling for JSON parsing
    }

    const char* type = doc["type"];

    if (strcmp(type, "move") == 0) {
        const char* coordSystem = doc["coordinate_system"];

        if (!coordSystem) {
            return "Error: No coordinate system specified";
        }

        // Variables to store final cartesian coordinates
        float finalX, finalY, finalZ;

        if (strcmp(coordSystem, "cartesian_abs") == 0) {
            finalX = doc["data"]["x"];
            finalY = doc["data"]["y"];
            finalZ = doc["data"]["z"];
        } else if (strcmp(coordSystem, "cartesian_rel") == 0) {
            float deltaX = doc["data"]["x"];
            float deltaY = doc["data"]["y"];
            float deltaZ = doc["data"]["z"];
            
            finalX = getCurrent('x') + deltaX;
            finalY = getCurrent('y') + deltaY;
            finalZ = getCurrent('z') + deltaZ;
        } else if (strcmp(coordSystem, "polar") == 0) {
            float r = doc["data"]["r"];
            float theta = doc["data"]["theta"];
            float z = doc["data"]["z"];
            
            float thetaRad = theta * PI / 180.0;
            finalX = r * cos(thetaRad);
            finalY = r * sin(thetaRad);
            finalZ = z;
        } else {
            return "Error: Invalid coordinate system";
        }

        if (!robot->isPositionSafe(finalX, finalY, finalZ)) {
            return "Error: Position out of safe bounds";
        }

        robot-> MoveMotor(finalX, finalY, finalZ);  // Call the motor control function on RobotObject

        return String("Moved to position X=") + finalX + " Y=" + finalY + " Z=" + finalZ;

    } else if (strcmp(type, "pipet_control") == 0) {
        float pipetLevel = doc["data"]["pipet_level"];
        if (String(doc["data"]).indexOf("pipet_level") < 0){
          return String("Error, incorrect command structure: \n"+command);
        }
        Serial.println(pipetLevel);
        robot-> MovePipet(pipetLevel);  // Call the pipet control function on RobotObject
        return String("Pipet level set to ") + pipetLevel;

    } else if (strcmp(type, "ping") == 0) {
        lastKeepAlive[clientIndex] = millis();
        return "pong";

    } else if (strcmp(type, "request") == 0) {
        const char* subject = doc["subject"];
        if (!subject) {
            return "Error: No request subject specified";
        }
        if (strcmp(subject, "current_pos") == 0) {
            float X = getCurrent('x');
            float Y = getCurrent('y');
            float Z = getCurrent('z');
            return String("Current position: X=") + X + " Y=" + Y + " Z=" + Z;
        }
    }

    return "Error: Unknown command";
}

// Example implementation of getCurrent functions
int RobotControlServer::getCurrent(char dimension) {
  // Replace with actual logic to get the current position for each dimension
  switch (dimension) {
    case 'x':
      return 10; // Replace with actual logic to get current X position
    case 'y':
      return 10; // Replace with actual logic to get current Y position
    case 'z':
      return 10; // Replace with actual logic to get current Z position
    default:
      return 10;
  }
}
