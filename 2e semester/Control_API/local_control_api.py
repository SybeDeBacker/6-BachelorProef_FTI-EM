import json
import os
from time import sleep
import logging
import colorlog
from .robot_object_import import RobotObject

class RobotControlAPI:
    def __init__(self,log_files_path:str = "C:/Users/Sybe/Documents/!UAntwerpen/6e Semester/6 - Bachelorproef/Code/Github/6-BachelorProef_FTI-EM_CoSysLab/2e semester/PythonServer_Package/logs"):
        self.setup_logging(log_files_path)
        try:
            self.robot = RobotObject(serial_port='COM3', baud_rate=9600)
            self.robot.setup_logging(log_files_path=log_files_path)
            self.robot.connect_serial()
        except Exception as e:
            print(f"Error initializing robot: {e}")
            self.logger_local.error(f"Error initializing robot: {e}")

    def setup_logging(self,log_files_path:str):
        log_file_path_local = os.path.abspath(f"{log_files_path}/local.log")  # Relative path
        log_file_path_common = os.path.abspath(f"{log_files_path}/common_log.log")  # Relative path
        
        os.makedirs(os.path.dirname(log_file_path_local), exist_ok=True)
        os.makedirs(os.path.dirname(log_file_path_common), exist_ok=True)

        log_formatter_local = colorlog.ColoredFormatter(
            f"%(log_color)s%(asctime)s %(levelname)-12s{'Local':<13}%(reset)s%(message)s",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'cyan',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler_local = logging.StreamHandler()
        console_handler_local.setFormatter(log_formatter_local)

        file_formatter_local = logging.Formatter(
            f"%(asctime)s %(levelname)-12s{'Local':<13}%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler_local = logging.FileHandler(log_file_path_local, mode="a")
        file_handler_local.setFormatter(file_formatter_local)

        file_handler_common_local = logging.FileHandler(log_file_path_common, mode="a")
        file_handler_common_local.setFormatter(file_formatter_local)

        self.logger_local = logging.getLogger("Local")
        self.logger_local.setLevel(logging.INFO)
        self.logger_local.addHandler(console_handler_local)
        self.logger_local.addHandler(file_handler_local)
        self.logger_local.addHandler(file_handler_common_local)
        self.logger_local.propagate = False

        self.logger_local.warning("Operating on Local Control API")
        self.logger_local.info(f"Local logging initialized. Logs are saved at: {log_files_path}")
        
    def aspirate(self, volume_in_ul: int, rate_in_ul_per_s:int):
        """Sends an aspirate command."""
        try:
            self.logger_local.info(f"Sent aspirate command: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s")
            self.robot.aspirate_pipette(volume=volume_in_ul, rate=rate_in_ul_per_s)
            return{"status": "success", "message": f"Aspirate command sent: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s"}
        except Exception as e:
            if str(e) == "Position out of safe bounds":
                self.logger_local.warning(f"Error sending aspirate command: {e}")
                return{"status": "error", "message": f"Error sending aspirate command: {e}"}
            self.logger_local.error(f"Error sending aspirate command: {e}")
            return{"status": "error", "message": f"Error sending aspirate command: {e}"}

    def dispense(self, volume_in_ul: int, rate_in_ul_per_s:int): 
        try:
            self.logger_local.info(f"Sent dispense command: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s")
            self.robot.dispense_pipette(volume=volume_in_ul, rate=rate_in_ul_per_s)
            return{"status": "success", "message": f"Dispense command sent: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s"}
        except Exception as e:
            if str(e) == "Position out of safe bounds":
                self.logger_local.warning(f"Error sending aspirate command: {e}")
                return{"status": "error", "message": f"Error sending aspirate command: {e}"}
            self.logger_local.error(f"Error sending aspirate command: {e}")
            return{"status": "error", "message": f"Error sending aspirate command: {e}"}

    def eject_tip(self):
        try:
            self.logger_local.info("Sent eject command")
            self.robot.eject_tip()
            return{"status": "success", "message": f"Eject tip command sent"}
        except Exception as e:
            self.logger_local.error(f"Error sending eject tip command: {e}")
            return{"status": "error", "message": f"Error sending eject tip command: {e}"}

    def zero_robot(self):
        try:
            self.logger_local.info(f"Sent zero command")
            self.robot.zero_robot()
            return{"status": "success", "message": f"Zero command sent"}
        except Exception as e:
            self.logger_local.error(f"Error sending zero command: {e}")
            return{"status": "error", "message": f"Error sending zero command: {e}"}

    def request_position(self):
        try: 
            self.logger_local.info(f"Sent volume request")
            v = self.robot.get_current_volume()
            self.logger_local.info(f"Current volume = {v}")
            return{"status": "success", "message": f"Volume request sent: current volume = {v}ul"}
        except Exception as e:
            self.logger_local.error(f"Error sending volume request: {e}")
            return{"status": "error", "message": f"Error sending volume request: {e}"}

    def set_microstep_size(self, microstep: int):
        try:
            self.logger_local.info(f"Setting parameter: Microstep size = {microstep}")
            self.robot.set_parameters(stepper_pipet_microsteps=microstep)
            return {"status":"success","message":f"Parameter set: Microstep size = {microstep}"}
        except Exception as e:
            self.logger_local.error(f"Error setting microstep size: {e}")
            return {"status":"error","message":f"Error setting microstep size: {e}"}
    
    def set_lead(self, lead_in_mm_per_rotation: int):
        try:
            self.logger_local.info(f"Setting parameter: Lead = {lead_in_mm_per_rotation}mm/rev")
            self.robot.set_parameters(pipet_lead=lead_in_mm_per_rotation)
            return {"status":"success","message":f"Parameter set: Lead = {lead_in_mm_per_rotation}mm/rev"}
        except Exception as e:
            self.logger_local.error(f"Error setting Lead: {e}")
            return {"status":"error","message":f"Error setting Lead: {e}"}
    
    def set_safe_bounds(self,bounds: list[int]):
        try:
            bounds = sorted(bounds)
            self.robot.set_safe_bounds(bounds)
            return{"status": "success", "message": f"Set bounds command sent: {bounds}"}
        except Exception as e:
            self.logger_local.error(f"Error setting safe bounds: {e}")
            return {"status":"error","message":f"Error setting safe bounds: {e}"}
 
    def set_volume_to_travel_ratio(self, ratio_in_ul_per_mm: int):
        try:
            self.logger_local.info(f"Setting parameter: Volume to travel ratio = {ratio_in_ul_per_mm}ul/mm")
            self.robot.set_parameters(volume_to_travel_ratio=ratio_in_ul_per_mm)
            return {"status":"success","message":f"Parameter set: Volume to travel ratio = {ratio_in_ul_per_mm}ul/mm"}
        except Exception as e:
            self.logger_local.error(f"Error setting Volume to travel ratio: {e}")
            return {"status":"error","message":f"Error setting Volume to travel ratio: {e}"}