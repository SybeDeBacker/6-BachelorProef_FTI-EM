from Control_API import HTTPRobotControlAPI as RobotControlAPI

# Example: Send a "MOVE" command
if __name__ == "__main__":
    # Set the IP and port of the Arduino robot
    ROBOT_IP = '10.0.1.250'  # Arduino's IP address (set in your Arduino sketch)
    ROBOT_URL = f"http://{ROBOT_IP}"
    # Connect to the robot server
    Robot = RobotControlAPI(server_url=ROBOT_URL)

    # Start a loop to send commands and pings
    Robot.zero_robot()
    Robot.set_safe_bounds([10000,10])
    Robot.aspirate(5000, 200)
    Robot.dispense(800, 200)
    Robot.eject_tip()
    
    pause = input()