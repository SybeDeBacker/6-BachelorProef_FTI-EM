from controlapi import RobotControlAPI

# Example: Send a "MOVE" command
if __name__ == "__main__":
    # Set the IP and port of the Arduino robot
    ROBOT_IP = '10.0.1.250'  # Arduino's IP address (set in your Arduino sketch)
    # Connect to the robot server
    
    Robot = RobotControlAPI("http://10.0.1.250")

    # Start a loop to send commands and pings
    Robot.aspirate(10, 5)
    Robot.aspirate(20, 10)
    Robot.dispense(10, 5)
    Robot.dispense(30, 10)
    Robot.set_lead(10)
    Robot.set_microstep_size(10)
    Robot.eject_pipette()
    Robot.zero_robot()