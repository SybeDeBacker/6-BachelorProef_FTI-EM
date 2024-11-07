#ifndef ROBOTOBJECT_H
#define ROBOTOBJECT_H

typedef void (*MotorControlFunction)(float x, float y, float z);
typedef void (*PipetControlFunction)(float pipetLevel);

class RobotObject {
public:
    // Constructor to set custom functions
    RobotObject(MotorControlFunction motorFunc = nullptr, PipetControlFunction pipetFunc = nullptr);

    // Setters to allow updating functions after creation
    void setMotorControlFunction(MotorControlFunction motorFunc);
    void setPipetControlFunction(PipetControlFunction pipetFunc);

    // Methods to invoke the control functions
    void customMotorControl(float x, float y, float z);
    void customPipetControl(float pipetLevel);

private:
    MotorControlFunction motorControlFunc;
    PipetControlFunction pipetControlFunc;
};

#endif
