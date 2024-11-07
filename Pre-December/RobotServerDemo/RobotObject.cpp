#include "RobotObject.h"

// Constructor to initialize with optional custom functions
RobotObject::RobotObject(MotorControlFunction motorFunc, PipetControlFunction pipetFunc)
    : motorControlFunc(motorFunc), pipetControlFunc(pipetFunc) {}

// Set or update the motor control function
void RobotObject::setMotorControlFunction(MotorControlFunction motorFunc) {
    motorControlFunc = motorFunc;
}

// Set or update the pipet control function
void RobotObject::setPipetControlFunction(PipetControlFunction pipetFunc) {
    pipetControlFunc = pipetFunc;
}

// Call the motor control function if it’s set
void RobotObject::customMotorControl(float x, float y, float z) {
    if (motorControlFunc) {
        motorControlFunc(x, y, z);
    }
}

// Call the pipet control function if it’s set
void RobotObject::customPipetControl(float pipetLevel) {
    if (pipetControlFunc) {
        pipetControlFunc(pipetLevel);
    }
}
