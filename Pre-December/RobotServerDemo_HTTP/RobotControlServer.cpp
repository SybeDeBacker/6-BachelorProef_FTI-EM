#include "RobotControlServer.h"

RobotControlServer::RobotControlServer(RobotObject* robot)
  : server(80), robot(robot) {}  // Constructor: only takes RobotObject pointer

void RobotControlServer::begin() {
  // Initialize the server routes
  server.on("/move", HTTP_POST, std::bind(&RobotControlServer::handleMoveCommand, this));
  server.on("/pipet_control", HTTP_POST, std::bind(&RobotControlServer::handlePipetControl, this));
  server.on("/ping", HTTP_GET, std::bind(&RobotControlServer::handlePing, this));
  server.on("/request", HTTP_GET, std::bind(&RobotControlServer::handleRequest, this));

  // Start the HTTP server
  server.begin();
  Serial.println("HTTP server started.");
}

void RobotControlServer::loop() {
  server.handleClient();  // Handle incoming HTTP requests
}

void RobotControlServer::handleMoveCommand() {
  String command = server.arg("plain");  // Get the raw JSON command from the body
  String response = handleCommand(command);  // Handle the command and get the response
  server.send(200, "application/json", response);  // Send response as JSON
}

void RobotControlServer::handlePipetControl() {
    String command = server.arg("plain");  // Get the raw JSON command from the body
    Serial.println("Received pipet control command: " + command);  // Debug log
    String response = handleCommand(command);  // Handle the command and get the response
    server.send(200, "application/json", response);  // Send response as JSON
}


void RobotControlServer::handlePing() {
  Serial.println("Received Ping");
  // Respond to ping with a simple JSON response
  server.send(200, "application/json", "{\"status\":\"Success\",\"message\":\"pong\"}");
}

void RobotControlServer::handleRequest() {
  Serial.println("ReceivedRequest");
    float X = getCurrent('x');
    float Y = getCurrent('y');
    float Z = getCurrent('z');
    String response = String("{\"status\":\"Success\",\"message\":\"Current position: X=") +
                      X + " Y=" + Y + " Z=" + Z + "\"}";
    server.send(200, "application/json", response);
}

String RobotControlServer::handleCommand(String command) {
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, command);

  if (error) {
    return "{\"status\": \"Error\", \"message\": \"Invalid command format\"}";  // Error handling
  }

  const char* type = doc["type"];

  if (strcmp(type, "move") == 0) {
    const char* coordSystem = doc["coordinate_system"];
    if (!coordSystem) {
      return "{\"status\": \"Error\", \"message\": \"No coordinate system specified\"}";
    }

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
      return "{\"status\": \"Error\", \"message\": \"Invalid coordinate system\"}";
    }

    if (!isPositionSafe(finalX, finalY, finalZ)) {
      return "{\"status\": \"Error\", \"message\": \"Position out of safe bounds\"}";
    }

    robot->MoveMotor(finalX, finalY, finalZ);  // Call the robot's motor control function
    return String("{\"status\": \"Success\", \"message\": \"Moved to position X=") + finalX + " Y=" + finalY + " Z=" + finalZ + "\"}";
  } else if (strcmp(type, "pipet_control") == 0) {
    float pipetLevel = doc["data"]["pipet_level"];
    robot->MovePipet(pipetLevel);  // Call pipet control function on RobotObject
    return String("{\"status\": \"Success\", \"message\": \"Pipet level set to ") + pipetLevel + "\"}";
  }

  return "{\"status\": \"Error\", \"message\": \"Unknown command\"}";
}

bool RobotControlServer::isPositionSafe(float x, float y, float z) {
  // Implement safety checks (e.g., robot limits or other constraints)
  // Here is just a placeholder logic
  return (x >= 0 && y >= 0 && z >= 0 && x <= 100 && y <= 100 && z <= 100);  // Safe position check
}

int RobotControlServer::getCurrent(char dimension) {
  // Example: Get the current position of each axis. Replace with actual logic to read robot's position.
  switch (dimension) {
    case 'x': return 10; // Example current position for X
    case 'y': return 20; // Example current position for Y
    case 'z': return 30; // Example current position for Z
    default: return 0;
  }
}
