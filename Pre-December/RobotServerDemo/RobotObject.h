#ifndef ROBOTOBJECT_H
#define ROBOTOBJECT_H

typedef void (*CustomMotorControlFunction)(float x, float y, float z);
typedef void (*CustomPipetControlFunction)(float pipetLevel);

class RobotObject {
public:
    // Constructor to set custom functions
    RobotObject(CustomMotorControlFunction motorFunc = nullptr, CustomPipetControlFunction pipetFunc = nullptr);

    // Setters to allow updating functions after creation
    void setMotorControlFunction(CustomMotorControlFunction motorFunc);
    void setPipetControlFunction(CustomPipetControlFunction pipetFunc);

    // Methods to invoke the control functions
    void MoveMotor(float x, float y, float z);
    void MovePipet(float pipetLevel);

private:
    CustomMotorControlFunction motorControlFunc;
    CustomPipetControlFunction pipetControlFunc;
};

#endif
