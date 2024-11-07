#include "RobotObject.h"

// Constructor to initialize with optional custom functions
RobotObject::RobotObject(CustomMotorControlFunction motorFunc, CustomPipetControlFunction pipetFunc)
    : motorControlFunc(motorFunc), pipetControlFunc(pipetFunc) {}

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
