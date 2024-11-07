import socket
import json
from threading import Thread, Lock
import queue
from time import time, sleep
from icmplib import ping
import math

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

class RobotServer:
    HEADERSIZE = 10
    KeepAliveInterval = 30

    def __init__(self, ip=None, port=None):
        self.server_ip = ip
        self.server_port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(5)
        self.lastKeepAlive = time()
        self.connected = False
        print(f"Server is listening on {self.server_ip}:{self.server_port}")

    def run(self):
        """Main server loop to accept and handle client connections."""
        while True:
            client_socket, client_address = self.server_socket.accept()
            client_handler = Thread(target=self.handle_client, args=(client_socket, client_address))
            client_handler.daemon = True
            client_handler.start()

    def handle_client(self, client_socket, client_address):
        """Handle individual client connection."""
        print(f"Connected by {client_address}")
        self.lastKeepAlive = time()
        self.send_message("Connection established", client_socket)

        # Start heartbeat monitor thread
        heartbeat_thread = Thread(target=self.heartbeat_monitor, args=(client_socket,))
        heartbeat_thread.daemon = True
        heartbeat_thread.start()

        with client_socket:
            self.connected = True
            while True:
                try:
                    data = self.receive_message(client_socket)
                    if not data:
                        break
                    response = self.handle_command(data.strip())
                    self.send_message(response, client_socket)
                    print(f"Response sent: {response}")
                except Exception as e:
                    if "[WinError 10054]" not in str(e) and "[WinError 10053]" not in str(e):
                        print(f"Error in exception: {e}")
                        continue
                    else:
                        break
        self.connected = False
        print(f"{client_address} has disconnected.")

    def handle_command(self, command):
        """Process the received command from the client."""
        print(f"Command received: {command}")
        command_dict = json.loads(command)
        command_type = command_dict.get("type")

        if command_type == "move":
            return self.process_move_command(command_dict)
        elif command_type == "ping":
            self.lastKeepAlive = time()
            print("pong")
            return "pong"
        elif command_type == "request":
            return self.process_request_command(command_dict)
        else:
            return "Unknown command"

    def process_move_command(self, command_dict):
        """Processes movement commands based on the specified coordinate system."""
        try:
            coord_system = command_dict.get("coordinate_system")
            data = command_dict["data"]
            if coord_system == "cartesian_abs":
                x, y, z = float(data["x"]), float(data["y"]), float(data["z"])
            elif coord_system == "cartesian_rel":
                current_pos = self.get_current_position()
                x = current_pos.x + float(data["x"])
                y = current_pos.y + float(data["y"])
                z = current_pos.z + float(data["z"])
            elif coord_system == "polar":
                r, theta, z = float(data["r"]), float(data["theta"]), float(data["z"])
                theta_rad = math.radians(theta)
                x = r * math.cos(theta_rad)
                y = r * math.sin(theta_rad)
            else:
                return "Error: Invalid coordinate system"

            if not self.is_position_safe(Point(x, y, z)):
                return "Error: Position out of safe bounds"

            self.move_to_position(Point(x, y, z))
            return f"Moved to position X={x:.2f} Y={y:.2f} Z={z:.2f}"
        except (ValueError, KeyError) as e:
            print(f"Error processing move command: {e}")
            return "Error: Invalid MOVE command format"

    def process_request_command(self, command_dict):
        """Processes request commands like 'current position'."""
        try:
            subject = command_dict.get("subject", "current_pos")
            if subject == "current_pos":
                p = self.get_current_position()
                return f"Current position: X={p.x} Y={p.y} Z={p.z}"
        except Exception as e:
            print(f"Error processing request: {e}")
            return "Error: Invalid request format"

    def is_position_safe(self, point):
        """Check if the target position is within safe operating bounds."""
        MAX_X, MIN_X = 300, -300
        MAX_Y, MIN_Y = 300, -300
        MAX_Z, MIN_Z = 200, 0
        return (MIN_X <= point.x <= MAX_X and MIN_Y <= point.y <= MAX_Y and MIN_Z <= point.z <= MAX_Z)

    def get_current_position(self):
        """Returns the current position of the robot."""
        return Point(10, 10, 10)  # Replace with actual position data

    def move_to_position(self, point):
        """Executes the actual movement to the target position."""
        print(f"Moving to position: X={point.x:.2f}, Y={point.y:.2f}, Z={point.z:.2f}")
        # Implement actual movement based on hardware

    def heartbeat_monitor(self, client_socket):
        """Monitors heartbeat and closes client connection on timeout."""
        while client_socket:
            sleep(1.5)
            if self.connected == False:
                return
            if time() - self.lastKeepAlive > RobotServer.KeepAliveInterval:
                print("Timeout: Closing connection due to inactivity.")
                client_socket.close()
                break

    def send_message(self, data, client_socket):
        """Send a JSON-encoded message with a header to the client."""
        data = f"{len(data):<{RobotServer.HEADERSIZE}}" + data
        client_socket.send(data.encode('utf-8'))

    def receive_message(self, client_socket):
        """Receive a JSON-encoded message with a header from the client."""
        full_msg = ''
        new_msg = True
        while True:
            msg = client_socket.recv(1024)
            if not msg:
                return ""
            if new_msg:
                msglen = int(msg[:RobotServer.HEADERSIZE])
                new_msg = False
            full_msg += msg.decode("utf-8")
            if len(full_msg) - RobotServer.HEADERSIZE == msglen:
                return full_msg[RobotServer.HEADERSIZE:]

class RobotControlAPI:
    def __init__(self, server_ip="10.0.1.221", server_port=65432, loopback=True):
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