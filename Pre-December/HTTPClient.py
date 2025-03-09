from PythonClient_Package import RobotControlAPI, Point

# Example: Send a "MOVE" command
if __name__ == "__main__":
    # Set the IP and port of the Arduino robot
    ROBOT_IP = '10.0.1.250'  # Arduino's IP address (set in your Arduino sketch)
    # Connect to the robot server
    
    Robot = RobotControlAPI("http://10.0.1.250")

    # List of coordinates to send
    coordinates = [
        Point(1, 2, 3),
        Point(10, 11, 12),
        Point(58, 25, 10),
        Point(5, 10, 15),
        Point(150, 110, 120),
        Point(580, 250, 100)
    ]

    # Start a loop to send commands and pings
    while True:
        for c in coordinates:
            Robot.move(point = c)
        break  # Exit the loop after sending all commands