import json
import os
from time import sleep
import logging
import colorlog
from .robot_object_import import RobotObject

class RobotControlAPI:
    def __init__(self,log_files_path:str = "2e semester/PythonServer_Package/logs/"):
        self.setup_logging(log_files_path)
        try:
            self.robot = RobotObject(serial_port='COM3', baud_rate=9600)
            self.robot.setup_logging(log_files_path=log_files_path)
            self.robot.connect_serial()
        except Exception as e:
            print(f"Error initializing robot: {e}")
            self.logger_local.error(f"Error initializing robot: {e}")

    def setup_logging(self,log_files_path:str):
        log_file_path_local = f"{log_files_path}local.log"  # Relative path
        log_file_path_common = f"{log_files_path}common_log.log"  # Relative path
        
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

        self.logger_local = logging.getLogger("Server")
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
            self.robot.aspirate_pipette(volume=volume_in_ul, rate=rate_in_ul_per_s)
            self.logger_local.info(f"Aspirate command sent: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s")
            return{"status": "success", "message": f"Aspirate command sent: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s"}
        except Exception as e:
            self.logger_local.error(f"Error sending aspirate command: {e}")
            return{"status": "error", "message": f"Error sending aspirate command: {e}"}

    def dispense(self, volume_in_ul: int, rate_in_ul_per_s:int): 
        try:
            self.robot.dispense_pipette(volume=volume_in_ul, rate=rate_in_ul_per_s)
            self.logger_local.info(f"Dispense command sent: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s")
            return{"status": "success", "message": f"Dispense command sent: {volume_in_ul} ul at {rate_in_ul_per_s} ul/s"}
        except Exception as e:
            self.logger_local.error(f"Error sending dispense command: {e}")
            return{"status": "error", "message": f"Error sending dispense command: {e}"}

    def eject_tip(self):
        try:
            self.robot.eject_tip()
            self.logger_local.info(f"Eject tip command sent")
            return{"status": "success", "message": f"Eject tip command sent"}
        except Exception as e:
            self.logger_local.error(f"Error sending eject tip command: {e}")
            return{"status": "error", "message": f"Error sending eject tip command: {e}"}

    def zero_robot(self):
        try:
            self.robot.zero_robot()
            self.logger_local.info(f"Zero command sent")
            return{"status": "success", "message": f"Zero command sent"}
        except Exception as e:
            self.logger_local.error(f"Error sending zero command: {e}")
            return{"status": "error", "message": f"Error sending zero command: {e}"}

    def request_position(self):
        try: 
            v = self.robot.get_current_volume()
            self.logger_local.info(f"Volume request sent: current volume = {v}")
            return{"status": "success", "message": f"Volume request sent: current volume = {v}"}
        except Exception as e:
            self.logger_local.error(f"Error sending volume request: {e}")
            return{"status": "error", "message": f"Error sending volume request: {e}"}

    def set_microstep_size(self, microstep: int):
        try:
            self.robot.set_parameters(stepper_pipet_microsteps=microstep)
            self.logger_local.info(f"Parameter set: Microstep size = {microstep}")
            return {"status":"success","message":f"Parameter set: Microstep size = {microstep}"}
        except Exception as e:
            self.logger_local.error(f"Error setting microstep size: {e}")
            return {"status":"error","message":f"Error setting microstep size: {e}"}
    
    def set_lead(self, lead_in_mm_per_rotation: int):
        try:
            self.robot.set_parameters(pipet_lead=lead_in_mm_per_rotation)
            self.logger_local.info(f"Parameter set: Lead = {lead_in_mm_per_rotation}mm/rev")
            return {"status":"success","message":f"Parameter set: Lead = {lead_in_mm_per_rotation}mm/rev"}
        except Exception as e:
            self.logger_local.error(f"Error setting Lead: {e}")
            return {"status":"error","message":f"Error setting Lead: {e}"}
    
    def set_volume_to_travel_ratio(self, ratio_in_ul_per_mm: int):
        try:
            self.robot.set_parameters(volume_to_travel_ratio=ratio_in_ul_per_mm)
            self.logger_local.info(f"Parameter set: Volume to travel ratio = {ratio_in_ul_per_mm}ul/mm")
            return {"status":"success","message":f"Parameter set: Volume to travel ratio = {ratio_in_ul_per_mm}ul/mm"}
        except Exception as e:
            self.logger_local.error(f"Error setting Volume to travel ratio: {e}")
            return {"status":"error","message":f"Error setting Volume to travel ratio: {e}"}