import socket
import json
from threading import Thread, Lock
import queue
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
    def __init__(self, server_ip="127.0.0.1", server_port=65432, loopback=True):
        self.server_ip = server_ip
        self.server_port = server_port
        self.loopback = loopback
        self.connected = False
        self.message_queue = queue.Queue()
        self.socket_lock = Lock()
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

        self.connect()
        
        sleep(0.1)

    def connect(self):
        """Attempts to connect to the robot server."""
        print("Connecting to the server.")
        try:
            self.server_ip = self.find_robot_ip()

            if self.client_socket:
                self.client_socket.close()

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.server_port))
            self.connected = True

            # Start threads for receiving messages and pinging
            self.receive_thread = Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            self.ping_thread = Thread(target=self.send_ping)
            self.ping_thread.daemon = True
            self.ping_thread.start()

            print(f"Succesfully connected to {self.server_ip}")
            print(self.get_messages()[0])
            return{"status": "connected", "message": f"Connected to {self.server_ip}"}
        except Exception as e:
            if "[WinError 10060]" in str(e) or "[WinError 10061]" in str(e):
                print(f"The Server ({self.server_ip}) is not online at this moment")
            else:
                print(f"Connection failed: {str(e)}")
            self.connected = False
            return{"status": "error", "message": f"Connection failed: {str(e)}"}

    def disconnect(self):
        """Closes the connection to the server."""
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
                print("Connection closed by user.")
                return {"status": "disconnected", "message": "Connection closed by user."}
            except:
                print("Failed to close connection")
                return {"status": "error", "message": "Failed to close connection"}

    def set_coordinate_system(self, system):
        """Sets the coordinate system for movement commands."""
        if system in self.coord_systems:
            self.current_coord_system = system
            print(f"Coordinate system set to {system}")
            return {"status": "success", "message": f"Coordinate system set to {system}"}
        print("Invalid coordinate system")
        return {"status": "error", "message": "Invalid coordinate system"}

    def move(self, c:Point = None ,x = None, y=None, z=None, coordinate_system=None):
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
        self.send_message(command_str)
        print(self.get_messages()[0])
        return{"status": "success", "message": f"Move command sent: {c.x}, {c.y}, {c.z}"}

    def request_position(self):
        """Requests the robot's current position."""
        if not self.connected:
            print("Request failed: Not connected to server")
            return {"status": "error", "message": "Not connected to server"}

        request = json.dumps({"type": "request", "subject": "current_pos"})
        self.send_message(request)
        print("Position request sent")
        return {"status": "success", "message": "Position request sent"}

    def get_status(self):
        """Checks and returns the current connection status."""
        if self.connected:
            print(f"Connected to server at: {self.server_ip}")
            return {"status": "connected", "message": "Connected to server"}
        else:
            print("Not connected to server")
            return {"status": "disconnected", "message": "Not connected to server"}

    def receive_messages(self):
        """Receives messages from the server."""
        while self.connected:
            try:
                header = self.client_socket.recv(self.HEADERSIZE).decode('utf-8')
                if not header:
                    raise ConnectionError("Server disconnected")

                msg_length = int(header.strip())
                full_msg = ""
                while len(full_msg) < msg_length:
                    chunk = self.client_socket.recv(1024).decode('utf-8')
                    if not chunk:
                        raise ConnectionError("Server disconnected")
                    full_msg += chunk

                if full_msg != "pong":
                    self.message_queue.put(full_msg)
            except Exception:
                self.connected = False
                break

    def send_ping(self):
        """Sends a ping to keep the connection alive."""
        while self.connected:
            sleep(self.ping_interval)
            try:
                self.send_message(json.dumps({"type": "ping"}))
            except Exception:
                self.connected = False
                break

    def send_message(self, message):
        """Sends a JSON-encoded message to the server."""
        try:
            with self.socket_lock:
                msg = f"{len(message):<{self.HEADERSIZE}}" + message
                print(f"Message sent: {msg}")
                self.client_socket.sendall(msg.encode('utf-8'))
        except Exception as e:
            if "[WinError 10052]" in str(e):
                pass
            elif "[WinError 10054]" in str(e):
                print("The server has severed the connection or might be offline.")
            elif "[WinError 10061]" in str(e):
                print("Loopback address is not available for connection.")
            else:
                print(f"Failed to send message: {e}")
            self.connected = False

    def find_robot_ip(self):
        """Attempts to find the robot's IP address."""
        try:
            ip_addresses = socket.gethostbyname_ex("MyESP8266")[2]
            filtered_ips = [ip for ip in ip_addresses if not ip.startswith("127.")]
            if self.is_device_online(filtered_ips[0]):   
                return filtered_ips[0] 
            else:
                print(f"Server at ({filtered_ips[0]}) is not online. Returning to loopback address: 10.0.1.221")
                return "10.0.1.221"
        except:
            return "10.0.1.221"

    def is_device_online(self, ip = None):
        if not ip:
            ip = self.server_ip
        """Pings the device to check if it's online."""
        try:
            response = ping(ip, timeout=0.04, count=2)
            if response.packets_received > 0:
                return True
            else:
                response = ping(ip, timeout=0.1, count=4)
                return response.packets_received > 0
        except OSError:
            return False

    def get_messages(self):
        """Returns all messages in the queue."""
        messages = []
        while self.message_queue.empty():
            sleep(0.001)
        
        while not self.message_queue.empty():
            messages.append(self.message_queue.get())
        return messages


# Example: Send a "MOVE" command
if __name__ == "__main__":
    # Set the IP and port of the Arduino robot
    ROBOT_IP = '10.0.1.221'  # Arduino's IP address (set in your Arduino sketch)
    ROBOT_PORT = 65432        # The same port you used in the Arduino sketch
    # Connect to the robot server
    
    Robot = RobotControlAPI(ROBOT_PORT)

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
    Robot.disconnect()