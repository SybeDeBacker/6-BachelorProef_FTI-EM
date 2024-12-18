from typing import Optional
import json
from threading import Thread
from flask import Flask, request, jsonify
import requests
from time import time, sleep
import math


class Point:
    def __init__(self, x:float, y:float, z:float, coordinate_system: str = "cartesian_absolute") -> None:
        self.x = x
        self.y = y
        self.z = z
        self.coordinate_system = coordinate_system
        self.coordinates = (x,y,z)
        self.current_index = 0

    def __repr__(self):
        return f"Point(x={self.x}, y={self.y}, z={self.z})"
    
    def __iter__(self):
        self.current_index = 0
        return self
    
    def __next__(self):
        if self.current_index == 3:
            raise StopIteration
        
        self.current_index += 1
        return self.coordinates[self.current_index-1]

class Coordinate_Range:
    def __init__(self, x_range: list[float], y_range: list[float], z_range: list[float], coordinate_system: str = "cartesian_absolute") -> None:
        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.ranges = [x_range, y_range, z_range]
        self.current_range_index = 0
        self.coordinate_system = coordinate_system

    def contains(self, Point: Point):
        x_safe = (min(self.x_range) <= Point.x <= max(self.x_range))
        y_safe = (min(self.y_range) <= Point.y <= max(self.y_range))
        z_safe = (min(self.z_range) <= Point.z <= max(self.z_range))
        return x_safe and y_safe and z_safe

    def __repr__(self):
        return f"{self.x_range}, {self.y_range}, {self.z_range}"
    
    def __iter__(self):
        self.current_range_index = 0
        return self

    def __next__(self):
        if self.current_range_index >= len(self.ranges):
            raise StopIteration
        self.current_range_index += 1
        return self.ranges[self.current_range_index-1]

class RobotObject:
    def __init__(self):
        self.current_position = Point(10,20,30)  # Initial position
        self.pipet_level = 0  # Initial pipet level
        self.safe_bounds = Coordinate_Range([0,100],[0,100],[0,50])

        self.x_homing_switch = True
        self.y_homing_switch = True
        self.z_homing_switch = True

        self.home_robot()

    def MoveMotor(self, x, y, z):
        # Motor control functions go here
        self.current_position = Point(x,y,z)
        print(f"Robot moved to position X={x}, Y={y}, Z={z}")

    def MovePipet(self, level):
        # Pipet control functions go here
        self.pipet_level = level
        print(f"Pipet level set to {level} ml")

    def get_current_position(self):
        #implement position logic
        return self.current_position
    
    def is_position_safe(self, x, y, z):
        return self.safe_bounds.contains(Point(x,y,z))
    
    def home_robot(self):
        #x_motor_run toward home
        #y_motor_run toward home
        #z_motor_run toward home
        while not (self.x_homing_switch and self.y_homing_switch and self.z_homing_switch):
            if self.x_homing_switch:
                #x_motor_stop
                pass
            if self.y_homing_switch:
                #y_motor_stop
                pass
            if self.z_homing_switch:
                #z_motor_stop
                pass
        self.current_position = Point(0,0,0)

class RobotServer:
    Robot_Control_Server = Flask(__name__)
    def __init__(self, Robot : RobotObject):
        self.Robot : RobotObject = Robot
        
    @Robot_Control_Server.route('/move', methods=['POST'])
    def handle_move_command(self):
        """
        Handles the /move endpoint to move the robot.
        """
        try:
            command = request.get_json()
            coord_system = command.get("coordinate_system")
            data = command.get("data")

            if not coord_system or not data:
                return jsonify({"status": "Error", "message": "Invalid command format"}), 400

            if coord_system == "cartesian_abs":
                x, y, z = float(data["x"]), float(data["y"]), float(data["z"])

            elif coord_system == "cartesian_rel":
                dx, dy, dz = float(data["x"]), float(data["y"]), float(data["z"])
                current_pos = self.Robot.get_current_position()
                x, y, z = current_pos.x + dx, current_pos.y + dy, current_pos.z + dz

            elif coord_system == "polar":
                r, theta, z = float(data["r"]), float(data["theta"]), float(data["z"])
                theta_rad = math.radians(theta)
                x, y = r * math.cos(theta_rad), r * math.sin(theta_rad)

            else:
                return jsonify({"status": "Error", "message": "Invalid coordinate system"}), 400

            if not self.Robot.is_position_safe(x, y, z):
                return jsonify({"status": "Error", "message": "Position out of safe bounds"}), 400

            self.Robot.MoveMotor(x, y, z)
            return jsonify({"status": "Success", "message": f"Moved to position X={x} Y={y} Z={z}"})

        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing move command: {e}"}), 500

    @Robot_Control_Server.route('/pipet_control', methods=['POST'])
    def handle_pipet_control(self):
        """
        Handles the /pipet_control endpoint to set the pipet level.
        """
        try:
            command = request.get_json()
            pipet_level = command["data"].get("pipet_level")

            if pipet_level is None:
                return jsonify({"status": "Error", "message": "Missing pipet_level in command"}), 400

            self.Robot.MovePipet(pipet_level)
            return jsonify({"status": "Success", "message": f"Pipet level set to {pipet_level}"})

        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing pipet control command: {e}"}), 500

    @Robot_Control_Server.route('/ping', methods=['GET'])
    def handle_ping():
        """
        Handles the /ping endpoint to confirm connectivity.
        """
        print("Ping received")
        return jsonify({"status": "Success", "message": "pong"})

    @Robot_Control_Server.route('/', methods=['GET'])
    def sample():
        """
        Handles the /ping endpoint to confirm connectivity.
        """
        print("Ping received")
        return jsonify({"status": "Success", "message": "This is the default path, use /ping instead"})

    @Robot_Control_Server.route('/request', methods=['GET'])
    def handle_request(self):
        """
        Handles the /request endpoint to retrieve robot information.
        """
        try:
            current_pos = self.Robot.get_current_position()
            return jsonify({"status": "Success", "message": f"Current position: X={current_pos.x} Y={current_pos.y} Z={current_pos.z}"})

        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing request: {e}"}), 500

    @Robot_Control_Server.route('/home_robot', methods=['GET'])
    def home_robot(self):
        try:
            self.Robot.home_robot()
            return jsonify({"status": "Success", "message": f"Robot homed.\\n Current position: X=0 Y=0 Z=0"})
        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing request: {e}"}), 500

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

    def set_coordinate_system(self, system):
        """Sets the coordinate system for movement commands."""
        if system in self.coord_systems:
            self.current_coord_system = system
            print(f"Coordinate system set to {system}")
            return {"status": "success", "message": f"Coordinate system set to {system}"}
        print("Invalid coordinate system")
        return {"status": "error", "message": "Invalid coordinate system"}

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

    def move(self, c:Point = Point(0,0,0), x:float = 0, y:float = 0, z:float = 0, coordinate_system:str=""):
        """Sends a movement command with the current coordinate system."""
        if not self.connected:
            print("Move command not sent: Not connected to server")
            return{"status": "error", "message": "Not connected to server"}
        
        if not c and (x and y and z):
            c = Point(x,y,z)
        elif not c:
            print("Given point is invalid: Error")


        if coordinate_system=="":
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

    def home_robot(self):
        if not self.connected:
            print("Move command not sent: Not connected to server")
            return{"status": "error", "message": "Not connected to server"}

        command = {
            "type": "home_robot",
        }

        command_str = json.dumps(command)
        self.send_message(command_str,"home_robot")
        return{"status": "success", "message": f"Home command sent"}
    
def main():
    # Example usage
    x_range = [0.0, 10.0]
    y_range = [0.0, 10.0]
    z_range = [0.0, 10.0]
    range_obj = Coordinate_Range(x_range, y_range, z_range)

    point = Point(5, 15, 5)
    print(range_obj.contains(point))

if __name__ == "__main__":
    main()