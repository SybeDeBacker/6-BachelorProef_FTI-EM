from Control_API import HTTPRobotControlAPI as RobotControlAPI

# Example: Send a "MOVE" command
if __name__ == "__main__":
    # Set the IP and port of the Arduino robot
    ROBOT_IP:str = '10.0.1.250'  # Arduino's IP address (set in your Arduino sketch)
    ROBOT_URL:str = f"http://{ROBOT_IP}"
    # Connect to the robot server
    Robot = RobotControlAPI(server_url=ROBOT_URL)
    # Start a loop to send commands and pings
    Robot.set_calibration_offset(offset=0)
    
    pause = input() 