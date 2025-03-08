import serial # Module needed for serial communication
import logging
import re
from json import loads as dictify, JSONDecodeError

class RobotObject:
    def __init__(self):

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        
        #open serial port

        try:
            self.ser = serial.Serial('COM3', 9600, timeout=1)
        except Exception as e:
            logging.critical(f"Error opening serial port: {e}")
            width = len(str(e))+10
            print(f"""\033[31m
{"-"*width}
{"Error opening serial port" : ^{width}}
{str(e): ^{width}}
{"-"*width}\033[0m""")
            raise Exception(13)
        self.current_volume = 0
        self.safe_bounds = [0, 1000]
        self.stepper_pipet_microsteps = 16
        self.pipet_lead = 1
        self.volume_to_travel_ratio = 100

        self.ser.flush()  
        if self.ser.in_waiting:    
            self.receive_response(print_confirmation=False)
        self.send_command("Ping")

        self.set_parameters(self.stepper_pipet_microsteps,self.pipet_lead,self.volume_to_travel_ratio,print_confirmation=False)

    def send_command(self, command: str, print_confirmation: bool = False) -> dict:
        try:
            self.ser.flush()
        except Exception as e:
            raise Exception(13)
        
        if print_confirmation:
            logging.info(f"Sent command: {command}")
            print(f"Command sent over serial: {command}")
        self.ser.write(command.encode('utf-8'))

        return self.receive_response(print_confirmation=print_confirmation)

    def aspirate_pipette(self, volume: int, rate: int, print_confirmation: bool = True):
        if not self.is_action_safe(volume):
            logging.warning(f"Action unsafe: Volume {self.current_volume + volume} is out of bounds!")
            raise Exception("Position out of safe bounds")
        if volume < 0 or rate < 0:
            raise Exception("Volume and rate must be positive")
        
        if print_confirmation:
            print(f"Aspirating {volume} ul at a rate of {rate} ul/s")

        aspiration_command = f"A{volume} R{rate}"
        success = self.send_command(aspiration_command, print_confirmation=print_confirmation)["status"] == "success"
        if not success:
            raise Exception("Arduino failed to aspirate pipette")
        
        self.current_volume += volume

        if print_confirmation:
            print(f"Aspirated by {volume} ul. Current volume: {self.current_volume} ul")

    def dispense_pipette(self, volume: int, rate: int, print_confirmation: bool = True):
        if not self.is_action_safe(-volume):
            logging.warning(f"Action unsafe: Volume {self.current_volume + volume} is out of bounds!")
            raise Exception("Position out of safe bounds")
        if volume < 0 or rate < 0:
            raise Exception("Volume and rate must be positive")
        
        dispense_command = f"D{volume} R{rate}"
        if print_confirmation:
            print(f"Dispensing {volume} ul at a rate of {rate} ul/s")

        success = self.send_command(dispense_command, print_confirmation=print_confirmation)["status"] == "success"
        if not success:
            raise Exception("Arduino failed to dispense pipette")
        
        self.current_volume -= volume

        if print_confirmation:
            print(f"Dispensed by {volume} ul. Current volume: {self.current_volume} ul")

    def eject_tip(self,print_confirmation: bool = True):
        eject_tip_command = "E"
        self.send_command(eject_tip_command, print_confirmation = print_confirmation)

        print("Ejecting tip")

        print("Tip ejected")

    def set_parameters(self, stepper_pipet_microsteps: int=0, pipet_lead: int=0, volume_to_travel_ratio: int=0, print_confirmation: bool=True) -> dict:
        if stepper_pipet_microsteps == 0 and pipet_lead == 0 and volume_to_travel_ratio == 0:
            return {"status":"error","message":"No parameters provided"}
        if stepper_pipet_microsteps < 0 or pipet_lead < 0 or volume_to_travel_ratio < 0:
            return {"status":"error","message":"Parameters must be positive"}

        self.stepper_pipet_microsteps = stepper_pipet_microsteps if stepper_pipet_microsteps > 0 else self.stepper_pipet_microsteps
        self.pipet_lead = pipet_lead if pipet_lead > 0 else self.pipet_lead
        self.volume_to_travel_ratio = volume_to_travel_ratio if volume_to_travel_ratio > 0 else self.volume_to_travel_ratio

        parameter_command = f"S{self.stepper_pipet_microsteps} L{self.pipet_lead} V{self.volume_to_travel_ratio}"
        self.send_command(parameter_command, print_confirmation = print_confirmation)

        confirmation_string = ""
        confirmation_string += f"Microsteps: {self.stepper_pipet_microsteps} "*(stepper_pipet_microsteps != 0)
        confirmation_string += f"Lead: {self.pipet_lead} "*(pipet_lead != 0)
        confirmation_string += f"VolumeToTravel ratio: {self.volume_to_travel_ratio} "*(volume_to_travel_ratio != 0)

        if print_confirmation:
            print(f"Setting Parameters: {confirmation_string}")

        return {"status":"success","message":f"Parameters set: Microsteps: {self.stepper_pipet_microsteps}, Lead: {self.pipet_lead}, VolumeToTravel ratio: {self.volume_to_travel_ratio}"}

    def get_current_volume(self):
        return self.current_volume

    def is_action_safe(self, volume: int):
        return (self.safe_bounds[0] <= self.current_volume + volume <= self.safe_bounds[1])

    def zero_robot(self, print_confirmation: bool = True):
        response: dict = self.send_command("Z", print_confirmation=print_confirmation)
        status = response["status"] == "success"
        self.current_volume = 0 if status else self.current_volume
        if not status:
            raise Exception("Arduino failed to zero robot")
        
    def sanitize_json(self, json_string: str) -> str:
        # Replace single quotes with double quotes
        json_string = json_string.replace("'", '"')
        # Ensure property names are enclosed in double quotes
        json_string = re.sub(r'(?<!")(\b\w+\b)(?=\s*:)', r'"\1"', json_string)
        # Ensure values are enclosed in double quotes if they are not numbers or booleans
        json_string = re.sub(r'(?<=: )(\b\w+\b)(?=[,}])', r'"\1"', json_string)
        return json_string
    
    def receive_response(self, print_confirmation: bool = True) -> dict:
        try:
            while True:
                while not self.ser.in_waiting:
                    pass
                while self.ser.in_waiting:
                    # Receive data from the Arduino
                    receive_string = self.ser.readline()
                    # Print the data received from Arduino to the terminal
                    if print_confirmation:
                        print(receive_string.decode('utf-8', 'replace').rstrip())
                try:
                    sanitized_string = self.sanitize_json(receive_string.decode('utf-8', 'replace').rstrip())
                    return dictify(sanitized_string)
                except JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    return {"status": "error", "message": "Invalid JSON response from Arduino"}
        except Exception as e:
            print("except: ", e)
            return {"status": "error", "message": "No response from Arduino"}

    def set_safe_bounds(self, safe_bounds: list[int]):
        self.safe_bounds = safe_bounds