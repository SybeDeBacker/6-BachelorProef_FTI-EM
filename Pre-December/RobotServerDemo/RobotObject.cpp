#include "RobotObject.h"

// Constructor to initialize with optional custom functions
RobotObject::RobotObject(CustomMotorControlFunction motorFunc, CustomPipetControlFunction pipetFunc)
    : motorControlFunc(motorFunc), pipetControlFunc(pipetFunc), MIN_X(MIN_X), MAX_X(MAX_X), MIN_Y(MIN_Y), MAX_Y(MAX_Y), MIN_Z(MIN_Z), MAX_Z(MAX_Z) {}

// Set or update the motor control function
void RobotObject::setMotorControlFunction(CustomMotorControlFunction motorFunc) {
  motorControlFunc = motorFunc;
}

// Set or update the pipet control function
void RobotObject::setPipetControlFunction(CustomPipetControlFunction pipetFunc) {
  pipetControlFunc = pipetFunc;
}

// Call the motor control function if it’s set
void RobotObject::MoveMotor(float x, float y, float z) {
    if (motorControlFunc) {
        motorControlFunc(x, y, z);
    }
}

// Call the pipet control function if it’s set
void RobotObject::MovePipet(float pipetLevel) {
    if (pipetControlFunc) {
        pipetControlFunc(pipetLevel);
    }
}

// Function to check if a position is within safe limits
bool RobotObject::isPositionSafe(float x, float y, float z) {
    return (x >= MIN_X && x <= MAX_X && y >= MIN_Y && y <= MAX_Y && z >= MIN_Z && z <= MAX_Z);
}

void RobotObject::setBounds(float x_min, float x_max, float y_min, float y_max, float z_min, float z_max) {
    MIN_X = x_min;
    MAX_X = x_max;
    MIN_Y = y_min;
    MAX_Y = y_max;
    MIN_Z = z_min;
    MAX_Z = z_max;
}