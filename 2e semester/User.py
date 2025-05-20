from Control_API import HTTPRobotControlAPI as RobotControlAPI
from time import sleep

# Example: Send a "MOVE" command
if __name__ == "__main__":
    pause = input() 
    # Connect to the robot server
    Robot = RobotControlAPI(server_url="http://127.0.0.1")
    # Start a loop to send commands and pings
    Robot.zero_robot()
    Robot.aspirate(volume_in_ul=300, rate_in_ul_per_s=70)
    sleep(1)
    Robot.dispense(volume_in_ul=300, rate_in_ul_per_s=70)
    pause = input() 
