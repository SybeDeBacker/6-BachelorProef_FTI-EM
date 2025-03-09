import serial # Module needed for serial communication
import logging
import colorlog
import re
from json import loads as dictify, JSONDecodeError
from time import time
import os

class RobotObject:
    def __init__(self, serial_port: str = 'COM3', baud_rate: int = 9600, timeout: int = 5) -> None:        
        self.serial_port = serial_port
        self.baud_rate = baud_rate

        self.current_volume = 0
        self.safe_bounds = [0, 1000]
        self.stepper_pipet_microsteps = 16
        self.pipet_lead = 1
        self.volume_to_travel_ratio = 100
        self.timeout = timeout

        self.serial_connected = False

    def setup_logging(self, log_files_path: str)-> None:
        log_file_path_object = os.path.abspath(f"{log_files_path}/object.log")  # Relative path
        log_file_path_common = os.path.abspath(f"{log_files_path}/common_log.log")  # Relative path

        # Ensure the logs directory exists
        os.makedirs(os.path.dirname(log_file_path_object), exist_ok=True)
        os.makedirs(os.path.dirname(log_file_path_common), exist_ok=True)

        log_formatter_robot = colorlog.ColoredFormatter(
            f"%(log_color)s%(asctime)s %(levelname)-12s{"RobotObject":<13}%(reset)s%(message)s", 
            log_colors={
                'DEBUG': 'green',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Set up the logging handler with the color formatter
        console_handler_robot = logging.StreamHandler()
        console_handler_robot.setFormatter(log_formatter_robot)

        file_formatter_object = logging.Formatter(
            f"%(asctime)s %(levelname)-12s{"RobotObject":<13}%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler_object = logging.FileHandler(log_file_path_object, mode="a")
        file_handler_object.setFormatter(file_formatter_object)

        file_handler_common_object = logging.FileHandler(log_file_path_common, mode="a")
        file_handler_common_object.setFormatter(file_formatter_object)

        # Set up the logger for RobotObject
        self.logger_robot = logging.getLogger("RobotObject")
        self.logger_robot.setLevel(logging.INFO)  # Adjust log level as needed
        self.logger_robot.addHandler(console_handler_robot)
        self.logger_robot.addHandler(file_handler_object)
        self.logger_robot.addHandler(file_handler_common_object)
        self.logger_robot.propagate = False
        self.logger_robot.info("Robot logging set up")

    def connect_serial(self, serial_port: str = "", baud_rate:int = 0) -> None:
        # Open serial port
        self.logger_robot.info("Setting up serial connection")
        if serial_port == "":
            serial_port = self.serial_port
        if baud_rate == 0:
            baud_rate = self.baud_rate
        
        try:
            self.ser = serial.Serial(serial_port, baud_rate, timeout=1)
        except Exception as e:
            self.logger_robot.critical(f"Error opening serial port: {e}")
            width = len(str(e)) + 10
            print(f"""\033[31m
{"-"*width}
{"Error opening serial port" : ^{width}}
{str(e): ^{width}}
{"-"*width}\033[0m""")
            raise Exception("Serial not connected")

        self.ser.flush()  
        if False:
            if self.ser.in_waiting:    
                self.receive_response(print_confirmation=False, startup = False)
        
        response = self.send_command("Ping",print_confirmation=False)

        if len(response)>0:
            self.serial_connected = True
            self.logger_robot.info("Serial responding")
        else:
            self.serial_connected = False
            self.ser.close()
            self.logger_robot.error("Serial not responding")
            raise Exception("Serial not responding")
        
        self.set_parameters(self.stepper_pipet_microsteps, self.pipet_lead, self.volume_to_travel_ratio, print_confirmation=False)

    def send_command(self, command: str, print_confirmation: bool = True) -> dict:
        try:
            self.ser.flush()
        except Exception as e:
            try:
                self.ser.open()
                self.ser.flush()
            except Exception as e:
                self.ser.close()
                self.logger_robot.error(f"Error flushing serial port: {e}")
                self.serial_connected = False
                raise Exception("Serial not connected")

        if print_confirmation:
            self.logger_robot.info(f"Sent command over Serial: {command}")
        
        try:
            self.ser.write(command.encode('utf-8'))
        except Exception as e:
            self.logger_robot.error(f"Error writing to serial port: {e}")
            self.serial_connected = False
            raise Exception("Serial not connected")

        return self.receive_response(print_confirmation=print_confirmation)

    def pipette_action(self, action: str, volume: int, rate: int, print_confirmation: bool = True)-> None:
        if not self.serial_connected:
            self.serial_connected = self.send_command("Ping")["status"] == "success"
            if not self.serial_connected:
                raise Exception("Serial not connected")
            
        if not self.is_action_safe(volume if action == 'aspirate' else -volume):
            self.logger_robot.warning(f"Action unsafe: Volume {self.current_volume + volume} is out of bounds!")
            raise Exception("Position out of safe bounds")
        
        if volume < 0 or rate < 0:
            raise Exception("Volume and rate must be positive")
        
        if print_confirmation:
            self.logger_robot.info(f"{action.capitalize()[:-1]}ing {volume} ul at a rate of {rate} ul/s")

        command = f"{action[0].upper()}{volume} R{rate}"
        success = self.send_command(command, print_confirmation=print_confirmation)["status"] == "success"
        if not success:
            raise Exception("Arduino failed to actuate pipette")
        
        self.current_volume += volume if action == 'aspirate' else -volume

        if print_confirmation:
            self.logger_robot.info(f"{action.capitalize()}d by {volume} ul. Current volume: {self.current_volume} ul")

    def aspirate_pipette(self, volume: int, rate: int, print_confirmation: bool = True)-> None:
        self.pipette_action('aspirate', volume, rate, print_confirmation)

    def dispense_pipette(self, volume: int, rate: int, print_confirmation: bool = True)-> None:
        self.pipette_action('dispense', volume, rate, print_confirmation)

    def eject_tip(self, print_confirmation: bool = True)-> None:
        eject_tip_command = "E"
        self.send_command(eject_tip_command, print_confirmation=print_confirmation)

    def set_parameters(self, stepper_pipet_microsteps: int = 0, pipet_lead: int = 0, volume_to_travel_ratio: int = 0, print_confirmation: bool = True) -> dict:
        if stepper_pipet_microsteps == 0 and pipet_lead == 0 and volume_to_travel_ratio == 0:
            return {"status": "error", "message": "No parameters provided"}
        if stepper_pipet_microsteps < 0 or pipet_lead < 0 or volume_to_travel_ratio < 0:
            return {"status": "error", "message": "Parameters must be positive"}

        self.stepper_pipet_microsteps = stepper_pipet_microsteps if stepper_pipet_microsteps > 0 else self.stepper_pipet_microsteps
        self.pipet_lead = pipet_lead if pipet_lead > 0 else self.pipet_lead
        self.volume_to_travel_ratio = volume_to_travel_ratio if volume_to_travel_ratio > 0 else self.volume_to_travel_ratio

        parameter_command = f"S{self.stepper_pipet_microsteps} L{self.pipet_lead} V{self.volume_to_travel_ratio}"
        self.send_command(parameter_command, print_confirmation=print_confirmation)

        confirmation_string = ""
        confirmation_string += f"Microsteps: {self.stepper_pipet_microsteps} " * (stepper_pipet_microsteps != 0)
        confirmation_string += f"Lead: {self.pipet_lead} " * (pipet_lead != 0)
        confirmation_string += f"VolumeToTravel ratio: {self.volume_to_travel_ratio} " * (volume_to_travel_ratio != 0)

        if False: #print_confirmation:
            self.logger_robot.info(f"Setting Parameters: {confirmation_string}")

        return {"status": "success", "message": f"Parameters set: Microsteps: {self.stepper_pipet_microsteps}, Lead: {self.pipet_lead}, VolumeToTravel ratio: {self.volume_to_travel_ratio}"}

    def get_current_volume(self):
        self.logger_robot.info(f"Received volume request. Current volume = {self.current_volume}")
        return self.current_volume

    def is_action_safe(self, volume: int):
        return self.safe_bounds[0] <= self.current_volume + volume <= self.safe_bounds[1]

    def zero_robot(self, print_confirmation: bool = True):
        response: dict = self.send_command("Z", print_confirmation=print_confirmation)
        status = response["status"] == "success"
        self.current_volume = 0 if status else self.current_volume
        if not status:
            raise Exception("Arduino failed to zero robot")

    def sanitize_json(self, json_string: str) -> str:
        json_string = json_string.strip()
        if json_string.find("Serial started")!=-1:
            return '{"status":"successs"}'
        if not json_string.startswith("{") or not json_string.endswith("}"):
            self.logger_robot.warning(f"Invalid JSON received: {json_string}")
            return "{}"  # Return empty JSON instead of crashing
        return json_string

    def receive_response(self, print_confirmation: bool = True, startup: bool = False) -> dict:
        try:
            start_time = time()
            while True:
                if time() - start_time > self.timeout:
                    raise TimeoutError("No response from Arduino")
                while not self.ser.in_waiting:
                    pass
                while self.ser.in_waiting:
                    # Receive data from the Arduino
                    receive_string = self.ser.readline()
                    try:
                        received:str = receive_string.decode('utf-8', 'ignore').rstrip()
                    except:
                        raise Exception("Invalid serial input")
                    # Print the data received from Arduino to the terminal
                    if print_confirmation:
                        self.logger_robot.info("Received over Serial: "+received)
                    if startup:
                        return dictify("status:success")
                try:
                    sanitized_string = self.sanitize_json(received)
                    response = dictify(sanitized_string)
                    if not sanitized_string.startswith("{") or not sanitized_string.endswith("}"):
                        self.logger_robot.warning(f"Invalid JSON received: {sanitized_string}")
                        raise Exception("Invalid JSON response from Arduino")
                    if response["status"]=="error":
                        self.logger_robot.warning("Error in answer")
                        raise Exception(response["message"])
                    else:
                        return response
                except Exception as e:
                    print(e)
                    self.logger_robot.info("Received over Serial: "+received)
                    self.logger_robot.error(f"JSON decode error: {e}")
                    raise Exception(e)
        except Exception as e:
            self.logger_robot.error(f"Exception in receive_response: {e}")
            raise Exception(e)

    def set_safe_bounds(self, safe_bounds: list[int]):
        self.safe_bounds = safe_bounds