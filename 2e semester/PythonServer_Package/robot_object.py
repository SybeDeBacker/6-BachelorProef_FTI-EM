import serial # Module needed for serial communication
import logging

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
            exit(1)
        self.current_volume = 0
        self.safe_bounds = [0, 1000]
        self.stepper_pipet_microsteps = 16
        self.pipet_lead = 1
        self.volume_to_travel_ratio = 0.1

    def send_command(self, command: str):
        print(f"Command sent over serial: {command}")
        self.ser.write(command.encode('utf-8'))
        return

    def aspirate_pipette(self, volume: int, rate: int):
        aspiration_command = f"A{volume} R{rate}"
        self.send_command(aspiration_command)
        print(f"Aspirating {volume} ml at a rate of {rate} ml/s")

        while (1):
            while (not self.ser.in_waiting):
                pass
            while (self.ser.in_waiting):
                # Receive data from the Arduino
                receive_string = self.ser.readline().decode('utf-8', 'replace').rstrip()
                # Print the data received from Arduino to the terminal
                print(receive_string)
            break

        self.current_volume += volume
        print(f"Aspirated by {volume} ml. Current volume: {self.current_volume} ml")

    def dispense_pipette(self, volume: int, rate: int):
        dispense_command = f"D{volume} R{rate}"
        self.send_command(dispense_command)
        print(f"Dispensing {volume} ml at a rate of {rate} ml/s")

        while (1):
            while (not self.ser.in_waiting):
                pass
            while (self.ser.in_waiting):
                # Receive data from the Arduino
                receive_string = self.ser.readline().decode('utf-8', 'replace').rstrip()
                # Print the data received from Arduino to the terminal
                print(receive_string)
            break

        self.current_volume -= volume
        print(f"Dispensed by {volume} ml. Current volume: {self.current_volume} ml")

    def eject_tip(self):
        eject_tip_command = "E"
        self.send_command(eject_tip_command)
        print("Ejecting tip")

        while (1):
            while (not self.ser.in_waiting):
                pass
            while (self.ser.in_waiting):
                # Receive data from the Arduino
                receive_string = self.ser.readline().decode('utf-8', 'replace').rstrip()
                # Print the data received from Arduino to the terminal
                print(receive_string)
            break

        print("Tip ejected")

    def set_parameters(self, stepper_pipet_microsteps: int=0, pipet_lead: int=0, volume_to_travel_ratio: int=0):
        parameter_command = ""
        parameter_command += f"S{stepper_pipet_microsteps}"*(stepper_pipet_microsteps != 0)
        parameter_command += f"L{pipet_lead}"*(pipet_lead != 0)
        parameter_command += f"V{volume_to_travel_ratio}"*(volume_to_travel_ratio != 0)
        self.send_command(parameter_command)
        
        self.stepper_pipet_microsteps = stepper_pipet_microsteps if stepper_pipet_microsteps != 0 else self.stepper_pipet_microsteps
        self.pipet_lead = pipet_lead if pipet_lead != 0 else self.pipet_lead
        self.volume_to_travel_ratio = volume_to_travel_ratio if volume_to_travel_ratio != 0 else self.volume_to_travel_ratio

        confirmation_string = ""
        confirmation_string += f"Microsteps: {self.stepper_pipet_microsteps} "*(stepper_pipet_microsteps != 0)
        confirmation_string += f"Lead: {self.pipet_lead} "*(pipet_lead != 0)
        confirmation_string += f"VolumeToTravel ratio: {self.volume_to_travel_ratio} "*(volume_to_travel_ratio != 0)

        print(f"Setting Parameters: {confirmation_string}")

        while (1):
            while (not self.ser.in_waiting):
                pass
            while (self.ser.in_waiting):
                # Receive data from the Arduino
                receive_string = self.ser.readline().decode('utf-8', 'replace').rstrip()
                # Print the data received from Arduino to the terminal
                print(receive_string)
            break

        print(f"Parameters set: Microsteps: {self.stepper_pipet_microsteps}, Lead: {self.pipet_lead}, VolumeToTravel ratio: {self.volume_to_travel_ratio}")

    def get_current_volume(self):
        return self.current_volume

    def is_action_safe(self, volume: int):
        return (self.safe_bounds[0] <= self.current_volume + volume <= self.safe_bounds[1])

    def zero_robot(self):
        self.current_volume = 0

    def set_safe_bounds(self, safe_bounds: list[int]):
        self.safe_bounds = safe_bounds