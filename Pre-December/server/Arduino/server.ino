#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include "utilities.h"

WiFiServer server(65432);                 // Create a TCP server on port 65432
const int MAX_CLIENTS = 5;                // Max number of clients to handle

WiFiClient clients[MAX_CLIENTS];          // Array to hold client connections
unsigned long lastKeepAlive[MAX_CLIENTS];  // Array to track keep-alive timestamps for each client

ssid = utilities.ssid();
password = utilities.password();

const int HEADERSIZE = 10;                 // Header size for message length
const int KeepAliveInterval = 30;          // Keep alive interval in seconds

bool connected[MAX_CLIENTS] = {false,false,false,false,false};
bool connected_old[MAX_CLIENTS];

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);
    
    // Wait for WiFi connection
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println("\nConnected to WiFi!");
    
    server.begin(); // Start the server
    Serial.println("Server started. Waiting for clients...");
    Serial.println("Is er? | Connected? | Available?");
}

void loop() {
  // Check for incoming clients and add them to the client array
  WiFiClient newClient = server.available();
  if (newClient) {
    bool added = false;
    
    for (int i = 0; i < MAX_CLIENTS; i++) {
      if (!clients[i]) {  // Find an empty slot
        clients[i] = newClient;
        lastKeepAlive[i] = millis();
        Serial.println("New client connected");
        sendResponse(clients[i], "Connection established: "+String(i));
        added = true;
        break;
      }
    }
    if (!added) {
      Serial.println("Max clients reached. Connection refused.");
      newClient.println("Max clients reached. Connection refused.");
      newClient.stop(); // Refuse connection if the array is full
    }
  }
  // Handle each connected client
  for (int i = 0; i < MAX_CLIENTS; i++) {
    connected_old[i] = connected[i];
    connected[i] = clients[i].connected();

    if (connected_old[i] != connected[i]){
      for (int j = 0; j < MAX_CLIENTS; j++) {
        Serial.print("Client " + String(j)+":");
        Serial.println(String(clients[j]) + "|" + String(clients[j].connected()) + "|" + String(connected[j]));
      }
      if (!(clients[i].connected())){
        Serial.println("Connection "+ String(i) + " ended by user.");
      }
    }

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
      if (!(clients[i].connected())) {
        // Clean up disconnected clients
        clients[i].stop();
        clients[i] = WiFiClient();
        Serial.print("Client " + String(i)+":");
        Serial.println(String(clients[i]) + "|" + String(clients[i].connected()) + "|" + String(clients[i].available()));
        Serial.println("Client disconnected.");
      }
    }
  }
}

// Function to read a message from the client
String readMessage(WiFiClient& client) {
    String message;
    while (client.available()) {
        char c = client.read(); // Read characters one by one
        message += c;
    }
    message = message.substring(HEADERSIZE);
    return message;
}

// Function to send a response to the client
void sendResponse(WiFiClient& client, String message) {
    int messageLength = message.length();
    String header = String(messageLength) + String("                   ").substring(0 + String(messageLength).length(), HEADERSIZE); // Create header
    client.print(header + message); // Send header and message
}

// Function to handle incoming commands and return a response
String handleCommand(String command, int clientIndex) {
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
          // Direct assignment for absolute cartesian
          finalX = doc["data"]["x"];
          finalY = doc["data"]["y"];
          finalZ = doc["data"]["z"];
            
        } else if (strcmp(coordSystem, "cartesian_rel") == 0) {
          // Add to current position for relative cartesian
          float deltaX = doc["data"]["x"];
          float deltaY = doc["data"]["y"];
          float deltaZ = doc["data"]["z"];
          
          finalX = getCurrent('x') + deltaX;  // You'll need to implement getCurrentX()
          finalY = getCurrent('y') + deltaY;  // You'll need to implement getCurrentY()
          finalZ = getCurrent('z') + deltaZ;  // You'll need to implement getCurrentZ()
            
        } else if (strcmp(coordSystem, "polar") == 0) {
          // Convert polar to cartesian
          float r = doc["data"]["r"];
          float theta = doc["data"]["theta"]; // theta should be in degrees
          float z = doc["data"]["z"];
          
          // Convert theta to radians for calculations
          float thetaRad = theta * PI / 180.0;
          
          // Convert polar to cartesian coordinates
          finalX = r * cos(thetaRad);
          finalY = r * sin(thetaRad);
          finalZ = z;
            
        } else {
          return "Error: Invalid coordinate system";
        }
        
        // Check if the calculated position is within safe bounds
        if (!isPositionSafe(finalX, finalY, finalZ)) {
            return "Error: Position out of safe bounds";
        }
        
        // Move to the calculated position
        moveToPosition(finalX, finalY, finalZ);  // You'll need to implement moveToPosition()
        
        // Return the final cartesian coordinates that were used
        return String("Moved to position X=") + finalX + " Y=" + finalY + " Z=" + finalZ;
        
    } else if (strcmp(type, "ping") == 0) {
        lastKeepAlive[clientIndex] = millis();
        return "pong"; // Respond to ping
    } else if (strcmp(type, "request") == 0){
      const char* subject = doc["subject"];
      if (!subject) {
        return "Error: No request subject specified";
      }
      if (strcmp(subject, "current_pos") == 0) {
        // Direct assignment for absolute cartesian
        float X = getCurrent('x');
        float Y = getCurrent('y');
        float Z = getCurrent('z');

        return String("Current position: X=") + X + " Y=" + Y + " Z=" + Z;
      }
    }
    
    return "Unknown command"; // Default unknown command response
}

int getCurrent(char dimension){
  return 10;
}

void moveToPosition(int x, int y, int z){
  delay(500);
  return;
}

// Helper function to check if a position is within safe bounds
bool isPositionSafe(float x, float y, float z) {
    // Define your safety bounds here
    const float MAX_X = 300; // Example values
    const float MIN_X = -300;
    const float MAX_Y = 300;
    const float MIN_Y = -300;
    const float MAX_Z = 200;
    const float MIN_Z = 0;
    
    return (x >= MIN_X && x <= MAX_X &&
            y >= MIN_Y && y <= MAX_Y &&
            z >= MIN_Z && z <= MAX_Z);
}
