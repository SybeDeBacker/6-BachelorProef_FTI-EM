from SocketsObjects import RobotServer

# Example: Send a "MOVE" command
if __name__ == "__main__":
    # Set the IP and port of the Arduino robot
    SERVER_IP = '10.0.1.221'  # Arduino's IP address (set in your Arduino sketch)
    SERVER_PORT = 65432        # The same port you used in the Arduino sketch

    Server = RobotServer(ip=SERVER_IP,port=SERVER_PORT)
    Server.run()
    # Connect to the robot server
