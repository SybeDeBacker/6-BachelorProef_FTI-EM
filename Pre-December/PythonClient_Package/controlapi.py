import json
import requests
from time import sleep
from .point import Point

class RobotControlAPI:
    def __init__(self, server_url = "http://10.0.1.250", loopback=True):
        self.server_url = server_url
        self.loopback = loopback
        self.connected = False
        self.HEADERSIZE = 10

        # Define coordinate systems
        self.coord_systems = {
            "cartesian_absolute": ["X", "Y", "Z"],
            "cartesian_relative": ["ΔX", "ΔY", "ΔZ"],
            "polar": ["R", "θ", "Z"]
        }
        self.current_coord_system = "cartesian_absolute"  # Default to cartesian absolute

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

    def move(self, point:Point = Point(0,0,0), x = None, y=None, z=None, coordinate_system=None):
        """Sends a movement command with the current coordinate system."""
        if not self.connected:
            print("Move command not sent: Not connected to server")
            return{"status": "error", "message": "Not connected to server"}
        
        if (x and y and z):
            try:
                (x,y,z) = (float(x),float(y),float(z))
            except ValueError as e:
                print(f"Given point is invalid: {e}")
        elif point == Point(0,0,0):
            print("Returning to home")
            return self.send_home()


        if not coordinate_system:
            coordinate_system = self.current_coord_system

        command = {
            "type": "move",
            "coordinate_system": self.current_coord_system,
            "data": {
                "x" if coordinate_system.startswith("cartesian") else "r": point.x,
                "y" if coordinate_system.startswith("cartesian") else "theta": point.y,
                "z": point.z
            }
        }

        command_str = json.dumps(command)
        self.send_message(command_str,"move")
        return{"status": "success", "message": f"Move command sent: {point.x}, {point.y}, {point.z}"}

    def send_home(self):
        self.send_message(json.dumps({"type": "home_robot"}),"home_robot")
        return{"status": "success", "message": "Home command sent"}

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
