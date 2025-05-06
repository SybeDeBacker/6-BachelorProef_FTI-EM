import json
import requests
from time import sleep
import logging
import os
import colorlog

class RobotControlAPI:
    def __init__(self, server_url = "http://10.0.1.250", loopback:bool=True, log_files_path:str = "C:/Users/Sybe/Documents/!UAntwerpen/6e Semester/6 - Bachelorproef/Code/Github/6-BachelorProef_FTI-EM_CoSysLab/2e semester/PythonServer_Package/logs", loopback_adress:str = "http://127.0.0.1"):
        self.server_url = server_url
        self.loopback_adress = loopback_adress
        self.loopback = loopback
        self.connected = False
        self.HEADERSIZE = 10

        # Initialize client variables
        self.client_socket = None
        self.receive_thread = None
        self.ping_thread = None
        self.ping_interval = 5  # Ping every 5 seconds

        self.setup_logging(log_files_path=log_files_path)

        self.check_server_availability()
        
        sleep(0.1)

    def setup_logging(self,log_files_path:str):
        log_file_path_http_client = os.path.abspath(f"{log_files_path}/http_client.log")  # Relative path
        log_file_path_common = os.path.abspath(f"{log_files_path}/common_log.log")  # Relative path
        
        os.makedirs(os.path.dirname(log_file_path_http_client), exist_ok=True)
        os.makedirs(os.path.dirname(log_file_path_common), exist_ok=True)

        log_formatter_http_client = colorlog.ColoredFormatter(
            f"%(log_color)s%(asctime)s %(levelname)-12s{'HTTP Client':<13}%(reset)s%(message)s",
            log_colors={
                'DEBUG': 'light_purple',
                'INFO': 'light_purple',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler_http_client = logging.StreamHandler()
        console_handler_http_client.setFormatter(log_formatter_http_client)

        file_formatter_http_client = logging.Formatter(
            f"%(asctime)s %(levelname)-12s{'HTTP Client':<13}%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler_http_client = logging.FileHandler(log_file_path_http_client, mode="a")
        file_handler_http_client.setFormatter(file_formatter_http_client)

        file_handler_common_http_client = logging.FileHandler(log_file_path_common, mode="a")
        file_handler_common_http_client.setFormatter(file_formatter_http_client)

        self.logger_http_client = logging.getLogger("HTTP Client")
        self.logger_http_client.setLevel(logging.INFO)
        self.logger_http_client.addHandler(console_handler_http_client)
        self.logger_http_client.addHandler(file_handler_http_client)
        self.logger_http_client.addHandler(file_handler_common_http_client)
        self.logger_http_client.propagate = False

        self.logger_http_client.warning("Operating on HTTP Control API")
        self.logger_http_client.info(f"HTTP Client logging initialized. Logs are saved at: {log_files_path}")
 
    def check_server_availability(self):
        try:
            # Attempting to ping the server to check availability
            response = requests.get(f"{self.server_url}/ping",timeout=3)
            if response.status_code == 200:
                self.connected = True
                self.logger_http_client.info(f"Client has connected to {self.server_url}")
            else:
                self.connected = False
                self.logger_http_client.warning(f"Client failed to connect to {self.server_url}.")
            return self.connected
        
        except requests.exceptions.RequestException as e:
            if self.loopback:
                self.logger_http_client.warning(f"Looping back to {self.loopback_adress} because {self.server_url} did not respond")
                try:
                    response = requests.get(f"{self.loopback_adress}/ping",timeout=3)
                    if response.status_code == 200:
                        self.server_url = self.loopback_adress
                        self.connected = True
                        self.logger_http_client.info(f"Client has connected to {self.server_url}")
                        return self.connected
                except:
                    self.connected = False
                    self.logger_http_client.warning("Client failed to connect.")
                    return False
            self.connected = False
            self.logger_http_client.warning("Client failed to connect.")
            return False

    def aspirate(self, volume_in_ul: int, rate_in_ul_per_s:int) -> dict[str,str]:
        """Sends an aspirate command."""
        self.logger_http_client.info(f"Sending aspirate command: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s")
        if not self.connected:
            self.logger_http_client.error("Move command not sent: Not connected to server")
            return{"status": "error", "message": "Not connected to server"}

        command = {
            "volume": volume_in_ul,
            "rate": rate_in_ul_per_s
        }

        command_str = json.dumps(command)
        
        return self.send_message(command_str,"aspirate")

    def dispense(self, volume_in_ul: int, rate_in_ul_per_s:int):
        """Sends an aspirate command."""
        self.logger_http_client.info(f"Sending dispense command: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s")
        if not self.connected:
            self.logger_http_client.error("Dispense command not sent: Not connected to server")
            return{"status": "error", "message": "Not connected to server"}

        command = {
            "volume": volume_in_ul,
            "rate": rate_in_ul_per_s
        }

        command_str = json.dumps(command)
        self.send_message(command_str,"dispense")
        return{"status": "success", "message": f"Dispense command sent: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s"}

    def eject_tip(self):
        """Sends an eject tip command."""
        self.logger_http_client.info("Ejecting tip")
        if not self.connected:
            self.logger_http_client.error("Eject command not sent: Not connected to server")
            return{"status": "error", "message": "Not connected to server"}

        self.send_message(json.dumps({"type": "eject_tip"}),"eject_tip")
        return{"status": "success", "message": "Eject tip command sent"}

    def zero_robot(self):
        self.logger_http_client.info("Zeroing robot volume")
        self.send_message(json.dumps({"type": "zero_robot"}),"zero_robot")
        return{"status": "success", "message": "Zero command sent"}

    def request_position(self):
        """Requests the robot's current position."""
        self.logger_http_client.info("Sending volume request")
        if not self.connected:
            self.logger_http_client.error("Request failed: Not connected to server")
            return {"status": "error", "message": "Not connected to server"}
        
        self.send_message(json.dumps({"type": "volume_request"}),"request")
        return {"status": "success", "message": "Position request sent"}

    def set_microstep_size(self, microstep: int):
        if not self.connected:
            self.logger_http_client.error("Request failed: Not connected to server")
            return {"status": "error", "message": "Not connected to server"}
        
        self.logger_http_client.info(f"Changing microstep size to {microstep}")

        self.send_message(json.dumps({
            "stepper_pipet_microsteps": microstep,
            "pipet_lead": 0,
            "volume_to_travel_ratio": 0
            }),"set_parameters")
        
        return {"status": "success", "message": f"Microstep size set to {microstep}"}
    
    def set_lead(self, lead_in_mm_per_rotation: int):
        if not self.connected:
            self.logger_http_client.error("Request failed: Not connected to server")
            return {"status": "error", "message": "Not connected to server"}
        
        self.logger_http_client.info(f"Changing lead to {lead_in_mm_per_rotation}mm/rev")

        self.send_message(json.dumps({
            "stepper_pipet_microsteps": 0,
            "pipet_lead": lead_in_mm_per_rotation,
            "volume_to_travel_ratio": 0
            }),"set_parameters")
        
        return {"status": "success", "message": f"Lead set to {lead_in_mm_per_rotation} mm/rev"}
    
    def set_volume_to_travel_ratio(self, ratio_in_ul_per_mm: int):
        if not self.connected:
            self.logger_http_client.error("Request failed: Not connected to server")
            return {"status": "error", "message": "Not connected to server"}
        
        self.logger_http_client.info(f"Changing volume to travel ratio to {ratio_in_ul_per_mm}ul/mm")

        self.send_message(json.dumps({
            "stepper_pipet_microsteps": 0,
            "pipet_lead": 0,
            "volume_to_travel_ratio": ratio_in_ul_per_mm
            }),"set_parameters")
        
        return {"status": "success", "message": f"Ratio set to {ratio_in_ul_per_mm} ul/mm"}

    def set_calibration_offset(self, offset: float):
        if not self.connected:
            self.logger_http_client.error("Request failed: Not connected to server")
            return {"status": "error", "message": "Not connected to server"}
        
        self.logger_http_client.info(f"Changing calibration offset to {offset}ul")

        self.send_message(json.dumps({
            "offset": offset
            }),"set_calibration_offset")
        
        return {"status": "success", "message": f"Offset set to {offset} ul"}


    def get_status(self):
        """Checks and returns the current connection status."""
        self.logger_http_client.info("Sending status request")
        if self.connected:
            self.logger_http_client.info(f"Connected to server at: {self.server_url}")
            return {"status": "connected", "message": f"Connected to server at {self.server_url}"}
        else:
            self.logger_http_client.info("Not connected to server")
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

    def set_safe_bounds(self,bounds: list[int]):
        self.logger_http_client.info(f"Setting bounds to {bounds}")
        if not self.connected:
            self.logger_http_client.error("Bounds command not sent: Not connected to server")
            return{"status": "error", "message": "Not connected to server"}

        bounds = sorted(bounds)
        command = {
            "lower": bounds[0],
            "upper": bounds[1]
        }

        command_str = json.dumps(command)
        self.send_message(command_str, "set_safe_bounds")
        return{"status": "success", "message": f"Set bounds command sent: {bounds}"}
        
    def send_message(self, message:str, endpoint:str) -> dict[str,str]:
        if self.connected:
            try:
                self.logger_http_client.info(f"Sending message: {message}")
                # Send the HTTP POST request to the server with the message
                # Change this line in your Python client:
                post_endpoints = ["aspirate","dispense","set_parameters","set_safe_bounds","set_calibration_offset"]
                if endpoint in post_endpoints:
                    response = requests.post(f"{self.server_url}/{endpoint}", json=json.loads(message))
                else:
                    response = requests.get(f"{self.server_url}/{endpoint}")
                status_code = response.status_code
                response = response.json()
                match status_code:
                    case 200:   self.logger_http_client.info(response["message"])
                    case 400:   self.logger_http_client.warning(response["message"])
                    case 504:   self.logger_http_client.critical(response["message"])
                    case _:     self.logger_http_client.error(response["message"])
                return response
            except requests.exceptions.RequestException as e:
                if (not self.check_server_availability()):
                    error = "Server has disconnected"
                else:
                    error = f"Error sending message: {e}"
                self.logger_http_client.error("Server has disconnected")
                return {"status":"error","message":error}
        else:
            error = "Server has disconnected"
            return {"status":"error","message":error}