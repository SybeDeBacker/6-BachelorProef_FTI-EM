import tkinter as tk
from tkinter import scrolledtext, ttk
from threading import Thread
import queue
import json
import requests
from time import sleep

class HTTPClientApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Robot Control Client")
        self.master.geometry("500x600")
        
        # Connection settings
        self.server_url = "http://10.0.1.250"  # Server URL (should match the server's address)
        self.connected = False
        self.message_queue = queue.Queue()
        
        # Coordinate system options
        self.coord_systems = {
            "Cartesian Absolute": "cartesian_abs",
            "Cartesian Relative": "cartesian_rel",
            "Polar": "polar"
        }
        
        # GUI Elements
        self.setup_gui()
        
        # Attempt to connect
        Thread(target=self.start_connection).start()
        
        self.update_status("Connecting...","black")
        # Start GUI update loop
        self.update_gui()
    
    def start_connection(self):
        # Attempts to connect to the server after the GUI is initialized.
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
            
            self.display_message(f"Sending move command ({coord_system}): {val1}, {val2}, {val3}")
            self.send_message(command_str,'move')

            
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
            self.display_message(f"Sending pipet command: level={pipet_level}")
            self.send_message(command_str,'pipet_control')

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
        self.send_message(message,'request')

    def connect_to_server(self):
        try:
            # Attempting to ping the server to check availability
            response = requests.get(f"{self.server_url}/ping")
            if response.status_code == 200:
                self.connected = True
                self.update_status(f"Connected to {self.server_url}", "green")
            else:
                self.connected = False
                self.update_status("Connection failed", "red")
            return self.connected
        except requests.exceptions.RequestException as e:
            self.connected = False
            self.update_status(f"Connection failed: {e}", "red")
            return False
    
    def reconnect(self):
        # Update status to indicate reconnection is in progress
        self.update_status("Reconnecting...", "black")
        sleep(2)
        self.connect_to_server()
    
    def close_connection(self):
        self.connected = False
        self.update_status("Disconnected", "red")
    
    def update_gui(self):
        self.master.after(100, self.update_gui)

    def display_message(self, msg):
        self.message_area.insert(tk.END, f"{msg}\n")
        self.message_area.yview(tk.END)

    def update_status(self, status, color):
        self.status_label.config(text=status, foreground=color)

    def send_message(self, message, endpoint):
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
                    self.display_message(f"Server: {responsejson["message"]}")
                else:
                    self.display_message(f"Failed to send: {message} \n\n {response.status_code} | {response.text}")
            except requests.exceptions.RequestException as e:
                self.display_message(f"Error sending message: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HTTPClientApp(root)
    root.mainloop()
