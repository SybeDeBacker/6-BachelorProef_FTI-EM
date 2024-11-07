import socket
from time import time, sleep
from collections import namedtuple
import json
import threading

#Robot -> Pommelien thijs "ik las het deze week op het internet"

HEADERSIZE = 10
# Server IP and Port Configuration
SERVER_IP = '10.0.1.221'
SERVER_PORT = 65432

KeepAliveInterval = 30
Point = namedtuple("Point", ["x", "y", "z"])

# Start the TCP server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen(5)  # Accept up to 5 connections

print(f"Server is listening on {SERVER_IP}:{SERVER_PORT}")

import json
from time import time
import math

def handle_command(command):
    """
    Process the received command from the client.
    Supports Cartesian (absolute/relative) and Polar coordinate systems.
    """
    print(f"Command received: {command}")
    command_dict = json.loads(command)

    if command_dict["type"] == "move":
        try:
            coord_system = command_dict.get("coordinate_system")
            if not coord_system:
                return "Error: No coordinate system specified"

            data = command_dict["data"]
            
            # Calculate final position based on coordinate system
            if coord_system == "cartesian_abs":
                # Direct absolute positioning
                x = float(data["x"])
                y = float(data["y"])
                z = float(data["z"])
                
            elif coord_system == "cartesian_rel":
                # Relative positioning from current position
                current_pos = get_current_position()  # You'll need to implement this
                dx = float(data["x"])
                dy = float(data["y"])
                dz = float(data["z"])
                x = current_pos.x + dx
                y = current_pos.y + dy
                z = current_pos.z + dz
                
            elif coord_system == "polar":
                # Convert polar to cartesian
                r = float(data["r"])
                theta = float(data["theta"])  # Expected in degrees
                z = float(data["z"])
                
                # Convert theta to radians for calculations
                theta_rad = math.radians(theta)
                
                # Convert polar to cartesian coordinates
                x = r * math.cos(theta_rad)
                y = r * math.sin(theta_rad)
                
            else:
                return "Error: Invalid coordinate system"

            # Check if position is within safe bounds
            if not is_position_safe(Point(x, y, z)):
                return "Error: Position out of safe bounds"

            # Create Point object with calculated position
            point = Point(x, y, z)
            
            # Move to position (implement actual movement logic here)
            move_to_position(point)
            
            print(f"Moving to position: X={point.x:.2f}, Y={point.y:.2f}, Z={point.z:.2f}")
            return f"Moved to position X={point.x:.2f} Y={point.y:.2f} Z={point.z:.2f}"
            
        except (ValueError, KeyError) as e:
            print(f"Error processing move command: {e}")
            return "Error: Invalid MOVE command format"
            
    elif command_dict["type"] == "ping":
        global lastKeepAlive
        lastKeepAlive = time()
        print("pong")
        return "pong"
    
    elif command_dict["type"] == "request":
        try:
            subject = command_dict.get("subject")
            if not subject:
                subject = "current_pos"

            p = get_current_position()

            if subject == "current_pos":
                return f"Current position: X={p.x} Y={p.y} Z={p.z}"
        except:
            print(f"Error processing request: {e}")
            return "Error: Invalid request format"
    return f"Unknown command: {command}"

def is_position_safe(point):
    """
    Check if the target position is within safe operating bounds.
    Adjust these values based on your robot's specifications.
    """
    MAX_X = 300  # Example values
    MIN_X = -300
    MAX_Y = 300
    MIN_Y = -300
    MAX_Z = 200
    MIN_Z = 0
    
    return (MIN_X <= point.x <= MAX_X and 
            MIN_Y <= point.y <= MAX_Y and 
            MIN_Z <= point.z <= MAX_Z)

# Helper functions that need to be implemented based on your setup:
def get_current_position():
    """
    Get the current position of the robot.
    Should return a Point object with current x, y, z coordinates.
    """
    # Implement based on your hardware setup
    return Point(10,10,10)

def move_to_position(point):
    """
    Execute the actual movement to the target position.
    """
    # Implement based on your hardware setup
    pass

class Point:
    """
    Represents a 3D point in space.
    """
    def __init__(self, x, y, z):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

def get_data(s):
    full_msg = ''
    new_msg = True
    while True:
        try:
            msg = s.recv(1024)
            if not msg:
                return ""
            if new_msg:
                try:
                    msglen = int(msg[:HEADERSIZE])
                except ValueError:
                    return None
                new_msg = False

            full_msg += msg.decode("utf-8")

            if len(full_msg) - HEADERSIZE == msglen:
                print(full_msg)
                return full_msg[HEADERSIZE:]
        except BlockingIOError:
            continue

def send(data, s):
    data = f"{len(data):<{HEADERSIZE}}" + data
    s.send(data.encode('utf-8'))

def heartbeat_monitor(client_socket):
    """
    Heartbeat monitor thread function to disconnect client if it exceeds the KeepAliveInterval.
    """
    global lastKeepAlive
    while client_socket:
        sleep(1.5)
        if time() - lastKeepAlive > KeepAliveInterval:
            print("Timeout: Closing connection due to inactivity.")
            client_socket.close()
            break

# Main loop to accept and handle connections
while True:
    client_socket, client_address = server_socket.accept()
    print(f"Connected by {client_address}")
    lastKeepAlive = time()
    response = "Connection established: "
    send(response, client_socket)

    # Start the heartbeat monitor thread
    heartbeat_thread = threading.Thread(target=heartbeat_monitor, args=(client_socket,))
    heartbeat_thread.daemon = True  # Daemonize thread to exit when main program exits
    heartbeat_thread.start()

    with client_socket:
        while True:
            try:
                data = get_data(client_socket)

                if not data:
                    break  # Exit the loop if no data is received (client disconnected)

                # Process "ping" or other command and get a response
                response = handle_command(data.strip())

                # Send the response back to the client
                send(response, client_socket)
                print(f"Response sent: {response}")
            except Exception as e:
                client_socket.close()
                if "[WinError 10054]" not in str(e) and "[WinError 10053]" not in str(e):
                    print(f"Error in exception: {e}")
                    continue
                else:
                    break
    print(f"{client_address} has disconnected.")
