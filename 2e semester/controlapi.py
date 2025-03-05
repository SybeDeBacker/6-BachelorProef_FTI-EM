import json
import requests
from time import sleep
import logging

class RobotControlAPI:
    def __init__(self, server_url = "http://10.0.1.250", loopback=True):
        self.server_url = server_url
        self.loopback = loopback
        self.connected = False
        self.HEADERSIZE = 10

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

    def aspirate(self, volume: int, rate:int):
        """Sends an aspirate command."""
        if not self.connected:
            print("Move command not sent: Not connected to server")
            return{"status": "error", "message": "Not connected to server"}

        command = {
            "volume": volume,
            "rate": rate
        }

        command_str = json.dumps(command)
        self.send_message(command_str,"aspirate")
        return{"status": "success", "message": f"Aspirate command sent: {volume} ml at {rate} ml/s"}

    def dispense(self, volume: int, rate:int):
        """Sends an aspirate command."""
        if not self.connected:
            print("Move command not sent: Not connected to server")
            return{"status": "error", "message": "Not connected to server"}

        command = {
            "volume": volume,
            "rate": rate
        }

        command_str = json.dumps(command)
        self.send_message(command_str,"dispense")
        return{"status": "success", "message": f"Dispense command sent: {volume} ml at {rate} ml/s"}

    def eject_tip(self):
        """Sends an eject tip command."""
        if not self.connected:
            print("Move command not sent: Not connected to server")
            return{"status": "error", "message": "Not connected to server"}

        self.send_message(json.dumps({"type": "eject_tip"}),"eject_tip")
        return{"status": "success", "message": "Eject tip command sent"}

    def zero_robot(self):
        self.send_message(json.dumps({"type": "zero_robot"}),"zero_robot")
        return{"status": "success", "message": "Zero command sent"}

    def request_position(self):
        """Requests the robot's current position."""
        if not self.connected:
            print("Request failed: Not connected to server")
            return {"status": "error", "message": "Not connected to server"}
        
        self.send_message(json.dumps({"type": "volume_request"}),"request")
        return {"status": "success", "message": "Position request sent"}

    def set_microstep_size(self, microstep: int):
        if not self.connected:
            print("Request failed: Not connected to server")
            return {"status": "error", "message": "Not connected to server"}
        
        self.send_message(json.dumps({
            "stepper_pipet_microsteps": microstep,
            "pipet_lead": 0,
            "volume_to_travel_ratio": 0
            }),"set_parameters")
        
        return {"status": "success", "message": f"Microstep size set to {microstep}"}
    
    def set_lead(self, lead: int):
        if not self.connected:
            print("Request failed: Not connected to server")
            return {"status": "error", "message": "Not connected to server"}
        
        self.send_message(json.dumps({
            "stepper_pipet_microsteps": 0,
            "pipet_lead": lead,
            "volume_to_travel_ratio": 0
            }),"set_parameters")
        
        return {"status": "success", "message": f"Lead set to {lead}"}
    
    def set_volume_to_travel_ratio(self, ratio: int):
        if not self.connected:
            print("Request failed: Not connected to server")
            return {"status": "error", "message": "Not connected to server"}
        
        self.send_message(json.dumps({
            "stepper_pipet_microsteps": 0,
            "pipet_lead": 0,
            "volume_to_travel_ratio": ratio
            }),"set_parameters")
        
        print(f"Changing ratio to {ratio}")
        return {"status": "success", "message": f"Ratio set to {ratio}"}

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
                print(f"Sending message: {message}")
                # Send the HTTP POST request to the server with the message
                # Change this line in your Python client:
                if endpoint == "aspirate" or endpoint == "dispense" or endpoint == "set_parameters":
                    response = requests.post(f"{self.server_url}/{endpoint}", json=json.loads(message))
                else:
                    response = requests.get(f"{self.server_url}/{endpoint}")
                status_code = response.status_code
                response = response.json()
                if status_code == 200:
                    print(response["message"],"\n")
                    return response
                else:
                    print(response["message"],"\n")
                    return response
            except requests.exceptions.RequestException as e:
                self.check_server_availability()
                if (not self.connected):
                    print(f"Server has disconnected")
                else:
                    print(f"Error sending message: {e}")