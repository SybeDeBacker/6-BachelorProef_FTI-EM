import json
import os
from time import sleep
import logging
import colorlog
from .robot_object_import import RobotObject

class RobotControlAPI:
    def __init__(self,serial_port:str,baud_rate:int,log_files_path:str = "C:/Users/Sybe/Documents/!UAntwerpen/6e Semester/6 - Bachelorproef/Code/Github/6-BachelorProef_FTI-EM_CoSysLab/2e semester/PythonServer_Package/logs"):
        self.setup_logging(log_files_path)
        try:
            self.robot = RobotObject(serial_port=serial_port, baud_rate=baud_rate)
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
            response = self.robot.aspirate_pipette(volume=volume_in_ul, rate=rate_in_ul_per_s)
            self.logger_local.info(response["message"])
            return{"status": "success", "message": response["message"]}
        except Exception as e:
            return self.exception_handler(str(e),"Error sending aspirate command")

    def dispense(self, volume_in_ul: int, rate_in_ul_per_s:int): 
        try:
            self.logger_local.info(f"Sent dispense command: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s")
            response = self.robot.dispense_pipette(volume=volume_in_ul, rate=rate_in_ul_per_s)
            self.logger_local.info(response["message"])
            return{"status": "success", "message": response["message"]}
        except Exception as e:
            return self.exception_handler(str(e),"Error sending dispense command")

    def eject_tip(self):
        try:
            self.logger_local.info("Sent eject command")
            response = self.robot.eject_tip()
            self.logger_local.info(response["message"])
            return{"status": "success", "message": response["message"]}
        except Exception as e:
            return self.exception_handler(str(e),"Error sending eject tip command")

    def zero_robot(self):
        try:
            self.logger_local.info(f"Sent zero command")
            self.robot.zero_robot()
            return{"status": "success", "message": f"Zero command sent"}
        except Exception as e:
            return self.exception_handler(str(e),"Error sending zero command")

    def request_position(self):
        try: 
            self.logger_local.info(f"Sent volume request")
            v = self.robot.get_current_volume()
            self.logger_local.info(f"Current volume = {v}ul")
            return{"status": "success", "message": f"Current volume = {v}ul"}
        except Exception as e:
            return self.exception_handler(str(e),"Error sending volume request")

    def set_microstep_size(self, microstep: int):
        try:
            self.logger_local.info(f"Setting parameter: Microstep size = {microstep}")
            response = self.robot.set_parameters(stepper_pipet_microsteps=microstep)
            self.logger_local.info(response["message"])
            return{"status": "success", "message": response["message"]}
        except Exception as e:
            return self.exception_handler(str(e),"Error setting microstep size")
    
    def set_lead(self, lead_in_mm_per_rotation: int):
        try:
            self.logger_local.info(f"Setting parameter: Lead = {lead_in_mm_per_rotation}mm/rev")
            response = self.robot.set_parameters(pipet_lead=lead_in_mm_per_rotation)
            self.logger_local.info(response["message"])
            return{"status": "success", "message": response["message"]}
        except Exception as e:
            return self.exception_handler(str(e),"Error setting Lead")

    def set_safe_bounds(self,bounds: list[int]):
        self.logger_local.info(f"Setting safe bounds to {bounds}")
        try:
            bounds = sorted(bounds)
            response = self.robot.set_safe_bounds(bounds)
            self.logger_local.info(response["message"])
            return{"status": "success", "message": response["message"]}
        except Exception as e:
            return self.exception_handler(str(e),"Error setting safe bounds")

    def set_volume_to_travel_ratio(self, ratio_in_ul_per_mm: int):
        try:
            self.logger_local.info(f"Setting parameter: Volume to travel ratio = {ratio_in_ul_per_mm}ul/mm")
            self.robot.set_parameters(volume_to_travel_ratio=ratio_in_ul_per_mm)
            return {"status":"success","message":f"Parameter set: Volume to travel ratio = {ratio_in_ul_per_mm}ul/mm"}
        except Exception as e:
            return self.exception_handler(str(e),"Error setting Volume to travel ratio")
        
    def exception_handler(self, error_msg: str, error_template:str)->dict[str,str]:
        if error_msg == "Position out of safe bounds":
                self.logger_local.warning(f"Error sending dispense command: {error_msg}")
        if error_msg == "Error opening serial port":
            self.logger_local.critical(f"{error_template}: {error_msg}")
        else:
            self.logger_local.error(f"Error setting Volume to travel ratio: {error_msg}")
        return {"status":"error","message":f"Error setting Volume to travel ratio: {error_msg}"}
