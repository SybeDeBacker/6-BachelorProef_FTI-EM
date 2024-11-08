#ifndef ROBOTOBJECT_H
#define ROBOTOBJECT_H

typedef void (*CustomMotorControlFunction)(float x, float y, float z);
typedef void (*CustomPipetControlFunction)(float pipetLevel);

class RobotObject {
public:
    // Constructor to set custom functions and optional bounds
    RobotObject(CustomMotorControlFunction motorFunc = nullptr, CustomPipetControlFunction pipetFunc = nullptr,
                float min_x = -100.0, float max_x = 100.0, 
                float min_y = -100.0, float max_y = 100.0, 
                float min_z = 0.0, float max_z = 100.0);

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

    float MIN_X;
    float MAX_X;
    float MIN_Y;
    float MAX_Y;
    float MIN_Z;
    float MAX_Z;
};

#endif
