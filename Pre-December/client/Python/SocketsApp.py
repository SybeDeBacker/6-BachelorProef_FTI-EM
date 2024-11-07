import socket
import tkinter as tk
from tkinter import scrolledtext, ttk
from threading import Thread, Lock
import queue
from time import sleep
import json
from icmplib import ping

#github test
class TCPClientApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Robot Control Client")
        self.master.geometry("500x600")
        
        # Connection settings
        self.loopback = True
        self.server_ip = "127.0.0.1"
        self.server_port = 65432
        self.connected = False
        self.message_queue = queue.Queue()
        self.socket_lock = Lock()
        self.HEADERSIZE = 10
        
        # Coordinate system options
        self.coord_systems = {
            "Cartesian Absolute": "cartesian_abs",
            "Cartesian Relative": "cartesian_rel",
            "Polar": "polar"
        }
        
        # GUI Elements
        self.setup_gui()
        
        # Initialize socket
        self.client_socket = None
        self.receive_thread = None
        self.ping_thread = None
        self.ping_interval = 5  # Send a ping every 5 seconds
        
        # Attempt to connect
        Thread(target=self.start_connection).start()
        
        self.update_status("Connecting...","black")
        # Start GUI update loop
        self.update_gui()
    
    def start_connection(self):
        #Attempts to connect to the server after the GUI is initialized.
        self.connect_to_server()

    def setup_gui(self):
        # Coordinate system selection frame
        coord_frame = ttk.LabelFrame(self.master, text="Coordinate System", padding=10)
        coord_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # Coordinate system dropdown
        self.coord_system = tk.StringVar(value="Cartesian Absolute")
        coord_dropdown = ttk.Combobox(coord_frame, textvariable=self.coord_system, 
                                    values=list(self.coord_systems.keys()), 
                                    state="readonly")
        coord_dropdown.pack(fill=tk.X)
        coord_dropdown.bind('<<ComboboxSelected>>', self.on_coord_system_change)
        
        # Position control frame
        position_frame = ttk.LabelFrame(self.master, text="Position Control", padding=10)
        position_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # Create position entry fields
        self.position_labels = {
            "cartesian_abs": ["X:", "Y:", "Z:"],
            "cartesian_rel": ["ΔX:", "ΔY:", "ΔZ:"],
            "polar": ["R:", "θ:", "Z:"]
        }
        
        # Position entries
        self.entries_frame = ttk.Frame(position_frame)
        self.entries_frame.pack(fill=tk.X, pady=5)
        
        # Create entry variables
        self.coord_vars = {
            "x": tk.StringVar(value="0"),
            "y": tk.StringVar(value="0"),
            "z": tk.StringVar(value="0")
        }
        
        # Initial setup of position entries
        self.setup_position_entries()

        # Move button
        self.move_button = ttk.Button(position_frame, text="Move", command=self.send_move_command)
        self.move_button.pack(side='left', anchor='e', pady=10)

        #Position Request button
        self.request_button = ttk.Button(position_frame, text="Request Position", command=self.send_request)
        self.request_button.pack(side='right', anchor='w', pady=10)
        
        # Pipet control frame
        pipet_frame = ttk.LabelFrame(self.master, text="Pipet Control", padding=10)
        pipet_frame.pack(padx=10, pady=5, fill=tk.X)

        # Pipet level entry
        ttk.Label(pipet_frame, text="Pipet Level:").pack(side=tk.LEFT, padx=5)
        self.pipet_level_var = tk.StringVar(value="0")
        pipet_entry = ttk.Entry(pipet_frame, textvariable=self.pipet_level_var, width=10)
        pipet_entry.pack(side=tk.LEFT, padx=5)

        # Pipet control button
        self.pipet_button = ttk.Button(pipet_frame, text="Set Pipet", command=self.send_pipet_command)
        self.pipet_button.pack(side=tk.LEFT, padx=5)

        # Message display area
        self.message_area = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, height=15)
        self.message_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Connection status frame
        status_frame = ttk.Frame(self.master)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Reconnect button
        self.reconnect_button = ttk.Button(status_frame, text="Reconnect", command=self.reconnect)
        self.reconnect_button.pack(side=tk.LEFT, padx=5)
        
        # Disconnect button
        self.disconnect_button = ttk.Button(status_frame, text="Disconnect", command=self.close_connection)
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_label = ttk.Label(status_frame, text="Disconnected", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=5)

    def setup_position_entries(self):
        # Clear existing entries
        for widget in self.entries_frame.winfo_children():
            widget.destroy()
        
        # Get current coordinate system
        coord_system = self.coord_systems[self.coord_system.get()]
        labels = self.position_labels[coord_system]
        
        # Create new entries
        for i, label in enumerate(labels):
            ttk.Label(self.entries_frame, text=label).grid(row=0, column=i*2, padx=5)
            coord_key = "x" if i == 0 else "y" if i == 1 else "z"
            entry = ttk.Entry(self.entries_frame, textvariable=self.coord_vars[coord_key], width=10)
            entry.grid(row=0, column=i*2+1, padx=5)

    def on_coord_system_change(self, event=None):
        self.setup_position_entries()

    def send_move_command(self):
        if not self.connected:
            self.display_message("Error: Not connected to server")
            return
        
        try:
            # Get values from entries
            val1 = float(self.coord_vars["x"].get())
            val2 = float(self.coord_vars["y"].get())
            val3 = float(self.coord_vars["z"].get())
            
            # Get current coordinate system
            coord_system = self.coord_systems[self.coord_system.get()]
            
            # Create move command with coordinate system information
            command = {
                "type": "move",
                "coordinate_system": coord_system,
                "data": {
                    # Use appropriate key names based on coordinate system
                    "x" if coord_system.startswith("cartesian") else "r": val1,
                    "y" if coord_system.startswith("cartesian") else "theta": val2,
                    "z": val3
                }
            }
            
            # Convert to JSON string
            command_str = json.dumps(command)
            
            self.send_message(command_str)
            self.display_message(f"Sending move command ({coord_system}): {val1}, {val2}, {val3}")
            
        except ValueError:
            self.display_message("Error: Position values must be numbers")

    def send_pipet_command(self):
        if not self.connected:
            self.display_message("Error: Not connected to server")
            return

        try:
            # Get pipet level from entry
            pipet_level = float(self.pipet_level_var.get())

            # Create pipet command
            command = {
                "type": "pipet_control",
                "data": {
                    "pipet_level": pipet_level
                }
            }

            # Convert to JSON string
            command_str = json.dumps(command)

            # Send command
            self.send_message(command_str)
            self.display_message(f"Sending pipet command: level={pipet_level}")

        except ValueError:
            self.display_message("Error: Pipet level must be a number")

    def send_request(self, subject=None):
        self.display_message("Requesting current position.")
        if subject == None:
            subject = "current_pos"
        request = {
            "type": "request", 
            "subject": subject
            }
        message = json.dumps(request)
        self.send_message(message)

    def connect_to_server(self):
        try:
            self.server_ip = self.find_robotIP()

            if not self.is_device_online():
                if self.loopback:
                    self.server_ip = "127.0.0.1"
                else:
                    raise Exception(f"Device at {self.server_ip} is offline.")

            
            if self.client_socket:
                self.client_socket.close()
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try: 
                self.client_socket.connect((self.server_ip, self.server_port))
            except Exception as e:
                print(f"{e}")
                sleep(5)
            self.connected = True
            self.update_status(f"Connected to {self.server_ip}", "green")
            
            # Start receive thread
            if self.receive_thread is None or not self.receive_thread.is_alive():
                self.receive_thread = Thread(target=self.receive_messages)
                self.receive_thread.daemon = True
                self.receive_thread.start()
            
            # Start ping thread
            if self.ping_thread is None or not self.ping_thread.is_alive():
                self.ping_thread = Thread(target=self.send_ping)
                self.ping_thread.daemon = True
                self.ping_thread.start()
            
            return True
        except Exception as e: 
            self.connected = False
            if "[WinError 10061]" in str(e) or "[WinError 10057]" in str(e):
                self.update_status("Failed to connect to server. Try again later.","red")
            else:
                self.update_status(f"Connection failed: {e}", "red")
            return False
    
    def reconnect(self):
        # Update status to indicate reconnection is in progress
        self.update_status("Reconnecting...", "black")
        
        # Start reconnection in a separate thread to keep the GUI responsive
        Thread(target=self.perform_reconnect).start()

    def perform_reconnect(self):
        # Set connected to False and attempt to reconnect
        self.connected = False
        success = self.connect_to_server()  # Attempt to reconnect

        # Update the status based on whether the reconnection was successful
        if success:
            self.update_status(f"Connected to {self.server_ip}", "green")
        else:
            self.update_status("Disconnected", "red")

    def update_status(self, message, color):
        self.message_queue.put(("status", message, color))
    
    def display_message(self, message):
        self.message_queue.put(("message", message))
    
    def update_gui(self):
        try:
            while not self.message_queue.empty():
                msg_type, *data = self.message_queue.get_nowait()
                if msg_type == "status":
                    message, color = data
                    self.status_label.config(text=message, foreground=color)
                elif msg_type == "message":
                    message = data[0]
                    self.message_area.insert(tk.END, message + "\n")
                    self.message_area.yview(tk.END)
        except queue.Empty:
            pass
        finally:
            self.master.after(100, self.update_gui)
    
    def send_message(self, message):
        if not self.connected:
            return
            
        try:
            with self.socket_lock:
                # Format message with header
                msg = f"{len(message):<{self.HEADERSIZE}}" + message
                self.client_socket.sendall(msg.encode('utf-8'))
        except Exception as e:
            self.display_message(f"Error sending message: {e}")
            self.connected = False
            self.update_status("Disconnected", "red")
    
    def receive_messages(self):
        while self.connected:
            try:
                # First receive the header
                header = self.client_socket.recv(self.HEADERSIZE).decode('utf-8')
                if not header:
                    raise ConnectionError("Server disconnected")
                
                msg_length = int(header.strip())
                
                # Now receive the actual message
                full_msg = ""
                while len(full_msg) < msg_length:
                    chunk = self.client_socket.recv(1024).decode('utf-8')
                    if not chunk:
                        raise ConnectionError("Server disconnected")
                    full_msg += chunk
                
                if full_msg != "pong":#and not "Connection established" in full_msg:
                    self.display_message(f"-> Server: {full_msg} \n")
                
            except Exception as e:
                if self.connected:  # Only show error if we haven't intentionally disconnected
                    if "[WinError 10060]" in str(e) or "[WinError 10054]" in str(e) or "[WinError 10057]" in str(e):
                        self.display_message("The server is no longer available.")
                    elif "Max client" in str(e):
                        self.display_message("Connection refused: Server is full.")
                    else:
                        self.display_message(f"Connection lost: {e}")
                    self.connected = False
                    self.update_status("Disconnected", "red")
                break
    
    def send_ping(self):
        while self.connected:
            sleep(self.ping_interval)  # Wait before sending the next ping
            try:
                ping_command = json.dumps({"type": "ping"})
                self.send_message(ping_command)
            except Exception as e:
                self.display_message(f"Error sending ping: {e}")
                self.connected = False
                self.update_status("Disconnected", "red")

    def close_connection(self):
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
                self.connected = False
                self.update_status(f"Connection ended by user.", "red")
            except:
                pass

    def close_app(self):
        self.close_connection()
        self.master.destroy()

    def find_robotIP(self):
        try:
            # Step 1: Get a list of IP addresses associated with the hostname.
            ip_addresses = socket.gethostbyname_ex("MyESP8266")[2]
            # Step 2: Filter out loopback addresses (IPs starting with "127.").
            filtered_ips = [ip for ip in ip_addresses if not ip.startswith("127.")]

            # Step 3: Extract the first IP address (if available) from the filtered list.
            first_ip = filtered_ips[:1]

            # Step 4: Print the obtained IP address to the console.
            return first_ip[0]
            
        except Exception as e:
            print(f"Error: {e}")
            print("No external connection found, returning to default loopback: 10.0.1.221")
            return '10.0.1.221'

    def is_device_online(self):
        try:
            response = ping(self.server_ip, timeout=0.04, count=2)
            if (response.packets_received != 0):
                return True
            else:
                response = ping(self.server_ip, timeout=0.08, count=3)
                return (response.packets_received != 0)
        except OSError:
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = TCPClientApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()
