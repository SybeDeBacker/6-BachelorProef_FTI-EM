import socket
import json
from threading import Thread, Lock
import requests
from time import sleep
from icmplib import ping



class Point:
    def __init__(self, x, y, z, coordinate_system = None) -> None:
        self.x = x
        self.y = y
        self.z = z
        if not coordinate_system:
            self.coordinate_system = "cartesian_absolute"
        else:
            self.coordinate_system = coordinate_system
        pass

class RobotControlAPI:
    def __init__(self, server_url = "http://10.0.1.250", loopback=True):
        self.server_url = server_url
        self.loopback = loopback
        self.connected = False
        self.HEADERSIZE = 10

        # Define coordinate systems
        self.coord_systems = {
            "cartesian_abs": ["X", "Y", "Z"],
            "cartesian_rel": ["ΔX", "ΔY", "ΔZ"],
            "polar": ["R", "θ", "Z"]
        }
        self.current_coord_system = "cartesian_abs"  # Default to cartesian absolute

        # Initialize client variables
        self.client_socket = None
        self.receive_thread = None
        self.ping_thread = None
        self.ping_interval = 5  # Ping every 5 seconds

        self.check_server_availability()
        
        sleep(0.1)

    def check_server_availability(self):
        try:
            # Attempting to ping the server to check availability
            response = requests.get(f"{self.server_url}/ping",timeout=3)
            print("connect")
            if response.status_code == 200:
                self.connected = True
            else:
                self.connected = False
            return self.connected
        except requests.exceptions.RequestException as e:
            if self.loopback:
                print("loopback")
                try:
                    response = requests.get("http://127.0.0.1/ping",timeout=3)
                    if response.status_code == 200:
                        self.server_url = "http://127.0.0.1"
                        self.connected = True
                        return self.connected
                except:
                    self.connected = False
                    return self.connected
            self.connected = False
            return False
    
    def set_coordinate_system(self, system):
        """Sets the coordinate system for movement commands."""
        if system in self.coord_systems:
            self.current_coord_system = system
            print(f"Coordinate system set to {system}")
            return {"status": "success", "message": f"Coordinate system set to {system}"}
        print("Invalid coordinate system")
        return {"status": "error", "message": "Invalid coordinate system"}

    def move(self, c:Point = Point(None,None,None), x = None, y=None, z=None, coordinate_system=None):
        """Sends a movement command with the current coordinate system."""
        if not self.connected:
            print("Move command not sent: Not connected to server")
            return{"status": "error", "message": "Not connected to server"}
        
        if not c and (x and y and z):
            c = Point(x,y,z)
        elif not c:
            print("Given point is invalid: Error")


        if not coordinate_system:
            coordinate_system = self.current_coord_system

        command = {
            "type": "move",
            "coordinate_system": self.current_coord_system,
            "data": {
                "x" if coordinate_system.startswith("cartesian") else "r": c.x,
                "y" if coordinate_system.startswith("cartesian") else "theta": c.y,
                "z": c.z
            }
        }

        command_str = json.dumps(command)
        self.send_message(command_str,"move")
        return{"status": "success", "message": f"Move command sent: {c.x}, {c.y}, {c.z}"}

    def request_position(self):
        """Requests the robot's current position."""
        if not self.connected:
            print("Request failed: Not connected to server")
            return {"status": "error", "message": "Not connected to server"}

        request = json.dumps({"type": "request", "subject": "current_pos"})
        self.send_message(request,"request")
        print("Position request sent")
        return {"status": "success", "message": "Position request sent"}

    def get_status(self):
        """Checks and returns the current connection status."""
        if self.connected:
            print(f"Connected to server at: {self.server_url}")
            return {"status": "connected", "message": "Connected to server"}
        else:
            print("Not connected to server")
            return {"status": "disconnected", "message": "Not connected to server"}

    def send_ping(self):
        """Sends a ping to keep the connection alive."""
        while self.connected:
            sleep(self.ping_interval)
            try:
                self.send_message(json.dumps({"type": "ping"}),"ping")
            except Exception:
                self.connected = False
                break

    def send_message(self, message:str, endpoint:str):
        if self.connected:
            try:
                # Send the HTTP POST request to the server with the message
                # Change this line in your Python client:
                print(message)
                print(f"{self.server_url}/{endpoint}")
                print(endpoint)
                if endpoint == "move" or endpoint == "pipet_control":
                    response = requests.post(f"{self.server_url}/{endpoint}", json=json.loads(message))
                else:
                    response = requests.get(f"{self.server_url}/{endpoint}")

                print(response)
                if response.status_code == 200:
                    print(response.text)
                    responsejson = json.loads(response.text)
                    return responsejson
                else:
                    print(response.text)
                    responsejson = json.loads(response.text)
                    return responsejson
            except requests.exceptions.RequestException as e:
                print(f"Error sending message: {e}")

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
            Robot.move(c = c)
        break  # Exit the loop after sending all commands