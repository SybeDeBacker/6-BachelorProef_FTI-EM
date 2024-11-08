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
    bool isPositionSafe(float x, float y, float z);
    void setBounds(float x_min, float x_max, float y_min, float y_max, float z_min, float z_max);

private:
    CustomMotorControlFunction motorControlFunc;
    CustomPipetControlFunction pipetControlFunc;

    float MIN_X = -100.0;
    float MAX_X = 100.0;
    float MIN_Y = -100.0;
    float MAX_Y = 100.0;
    float MIN_Z = 0.0;
    float MAX_Z = 100.0;
};

#endif
