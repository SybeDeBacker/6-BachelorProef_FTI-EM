from flask import Flask, request, jsonify
from .robot_object import RobotObject
import logging
import colorlog
import os

class RobotServer:
    def __init__(self, robot: RobotObject,log_files_path: str = "C:/Users/Sybe/Documents/!UAntwerpen/6e Semester/6 - Bachelorproef/Code/Github/6-BachelorProef_FTI-EM_CoSysLab/2e semester/PythonServer_Package/logs"):
        self.app = Flask(__name__)

        # Set up logging
        self.setup_logging(log_files_path)

        try:
            self.robot = robot
            robot.setup_logging(log_files_path)
            self.robot.connect_serial()
        except Exception as e:
            self.logger_server.critical(f"Error initializing robot: {e}")
            pause = input("Press Enter to continue...")
            self.logger_server.warning("Exiting server")
            exit(0)

        # Define routes
        self.app.add_url_rule('/aspirate', 'aspirate', self.handle_aspirate_command, methods=['POST'])
        self.app.add_url_rule('/dispense', 'dispense', self.handle_dispense_command, methods=['POST'])
        self.app.add_url_rule('/set_parameters', 'set_parameters', self.handle_set_parameters, methods=['POST'])
        self.app.add_url_rule('/set_calibration_offset', 'set_calibration_offset', self.handle_set_calibration_offset, methods=['POST'])
        self.app.add_url_rule('/set_safe_bounds', 'set_safe_bounds', self.handle_set_safe_bounds, methods=['POST'])
        self.app.add_url_rule('/ping', 'ping', self.handle_ping, methods=['GET'])
        self.app.add_url_rule('/request', 'request', self.handle_request, methods=['GET'])
        self.app.add_url_rule('/zero_robot', 'zero_robot', self.zero_robot, methods=['GET'])
        self.app.add_url_rule('/eject_tip', 'eject_tip', self.handle_eject, methods=['GET'])

    def setup_logging(self,log_files_path:str):
        log_file_path_server = os.path.abspath(f"{log_files_path}/server_log.log") # Relative path
        log_file_path_common = os.path.abspath(f"{log_files_path}/common_log.log") # Relative path
        
        os.makedirs(os.path.dirname(log_file_path_server), exist_ok=True)
        os.makedirs(os.path.dirname(log_file_path_common), exist_ok=True)

        log_formatter_server = colorlog.ColoredFormatter(
            f"%(log_color)s%(asctime)s %(levelname)-12s{'Server':<13}%(reset)s%(message)s",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'cyan',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler_server = logging.StreamHandler()
        console_handler_server.setFormatter(log_formatter_server)

        file_formatter_server = logging.Formatter(
            f"%(asctime)s %(levelname)-12s{'Server':<13}%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler_server = logging.FileHandler(log_file_path_server, mode="a")
        file_handler_server.setFormatter(file_formatter_server)

        file_handler_common_server = logging.FileHandler(log_file_path_common, mode="a")
        file_handler_common_server.setFormatter(file_formatter_server)

        self.logger_server = logging.getLogger("Server")
        self.logger_server.setLevel(logging.INFO)
        self.logger_server.addHandler(console_handler_server)
        self.logger_server.addHandler(file_handler_server)
        self.logger_server.addHandler(file_handler_common_server)
        self.logger_server.propagate = False

        self.logger_server.info(f"Server logging initialized. Logs are saved at: {log_files_path}")

    def handle_aspirate_command(self)->tuple[dict[str,str],int]:
        try:
            command = request.get_json()
            volume = command.get("volume")
            rate = command.get("rate")
            self.logger_server.info(f"Received aspirate command: volume={volume}, rate={rate}")
            response = self.robot.aspirate_pipette(volume=volume, rate=rate)
            self.logger_server.info(f"{response["message"]}")
            return {"status": "Success", "message": response["message"]},200
        
        except Exception as e:
            return self.exception_handler(str(e),"Error aspirating")

    def handle_dispense_command(self)->tuple[dict[str,str],int]:
        try:
            command = request.get_json()
            volume = command.get("volume")
            rate = command.get("rate")
            self.logger_server.info(f"Received dispense command: volume={volume}, rate={rate}")
            response = self.robot.dispense_pipette(volume=volume, rate=rate)
            self.logger_server.info(f"{response["message"]}")
            return {"status": "Success", "message": f"{response["message"]}"},200
        
        except Exception as e:
            return self.exception_handler(str(e), "Error dispensing")

    def handle_ping(self)->tuple[dict[str,str],int]:
        self.logger_server.info("Received ping request")
        return {"status": "Success", "message": "pong"},200

    def handle_request(self)->tuple[dict[str,str],int]:
        try:
            self.logger_server.info(f"Received volume request")
            current_volume = self.robot.get_current_volume()
            return {"status": "Success", "message": f"Current volume: {current_volume} ul"},200
        except Exception as e:
            return self.exception_handler(str(e), "Error handling volume request")

    def handle_set_parameters(self)->tuple[dict[str,str],int]:
        try:
            command = request.get_json()
            microsteps = command.get("stepper_pipet_microsteps")
            lead = command.get("pipet_lead")
            vtr = command.get("volume_to_travel_ratio")
            self.logger_server.info(f"Received set parameters command: microsteps={microsteps}, lead={lead}, vtr={vtr}")
            return self.robot.set_parameters(stepper_pipet_microsteps=microsteps, pipet_lead = lead, volume_to_travel_ratio = vtr),200
        
        except Exception as e:
            return self.exception_handler(str(e), "Error handling set parameter command")

    def handle_set_calibration_offset(self)->tuple[dict[str,str],int]:
        try:
            command = request.get_json()
            offset:float = float(command.get("offset"))
            self.logger_server.info(f"Received calibration command: offset={offset}")
            response = self.robot.set_calibration_offset(offset=offset)
            self.logger_server.info(f"{response["message"]}")
            return {"status": "Success", "message": response["message"]},200
        except Exception as e:
            return self.exception_handler(str(e),"Error setting calibration")

    def handle_set_safe_bounds(self)->tuple[dict[str,str],int]:
        try:
            command = request.get_json()
            lower = command.get("lower")
            upper = command.get("upper")
            self.logger_server.info(f"Received set safe bounds command: [{upper},{lower}]")
            return self.robot.set_safe_bounds([lower,upper]),200
        
        except Exception as e:
            return self.exception_handler(str(e),'Error setting safe bounds')

    def handle_eject(self)->tuple[dict[str,str],int]:
        try:
            self.logger_server.info("Received eject tip command")
            self.robot.eject_tip()
            return {"status": "Success", "message": "Tip ejected"},200
        except Exception as e:
            return self.exception_handler(str(e),"Error processing eject command")

    def zero_robot(self)->tuple[dict[str,str],int]:
        try:
            self.logger_server.info("Received zero robot command")
            self.robot.zero_robot()
            return {"status": "Success", "message": "Robot homed. Current volume: 0"},200
        except Exception as e:
            return self.exception_handler(str(e),"Error processing zero_robot command")

    def handle_serial_error(self):
        return "Error opening serial port"
        error = "Error opening serial port"
        width = len(str(error))+10
        errorstring = f"""\033[31m
{"-"*width}
{"Error opening serial port" : ^{width}}
{str(error): ^{width}}
{"-"*width}\033[0m"""
        return errorstring

    def exception_handler(self,error_msg:str,error_template:str)->tuple[dict[str,str],int]:
        if str(error_msg) == "Position out of safe bounds":
            self.logger_server.warning(f"{error_template}: {error_msg}")
            return {"status": "Error", "message": f"{error_template}: {error_msg}"}, 400
        if str(error_msg) == "Error opening serial port":
            error_msg = self.handle_serial_error()
            self.logger_server.critical(f"{error_template}: {error_msg}")
            return {"status": "Error", "message": f"{error_template}: {error_msg}"}, 504
        else:
            self.logger_server.error(f"{error_template}: {error_msg}")
        return {"status": "Error", "message": f"{error_template}: {error_msg}"}, 500

    def run(self, host, port):
        from waitress import serve
        self.logger_server.info(f"Server running on http://{host}:{port}")
        serve(self.app, host=host, port=port)