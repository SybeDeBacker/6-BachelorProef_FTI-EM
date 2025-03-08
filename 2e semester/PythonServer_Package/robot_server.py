from flask import Flask, request, jsonify
from .robot_object import RobotObject
import logging
import colorlog

class RobotServer:
    def __init__(self, robot: RobotObject):
        self.robot = robot
        self.app = Flask(__name__)

        # Set up logging
        self.setup_logging()

        self.app.logger.handlers = self.logger_server.handlers
        self.app.logger.setLevel(self.logger_server.level)

        # Define routes
        self.app.add_url_rule('/aspirate', 'aspirate', self.handle_aspirate_command, methods=['POST'])
        self.app.add_url_rule('/dispense', 'dispense', self.handle_dispense_command, methods=['POST'])
        self.app.add_url_rule('/set_parameters', 'set_parameters', self.handle_set_parameters, methods=['POST'])
        self.app.add_url_rule('/ping', 'ping', self.handle_ping, methods=['GET'])
        self.app.add_url_rule('/request', 'request', self.handle_request, methods=['GET'])
        self.app.add_url_rule('/zero_robot', 'zero_robot', self.zero_robot, methods=['GET'])
        self.app.add_url_rule('/eject_tip', 'eject_tip', self.handle_eject, methods=['GET'])

    def setup_logging(self):
        log_formatter_server = colorlog.ColoredFormatter(
            f"%(log_color)s%(asctime)s %(levelname)-12s {"Server":<13}%(reset)s%(message)s",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'cyan',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Set up the logging handler with the color formatter
        console_handler_server = logging.StreamHandler()
        console_handler_server.setFormatter(log_formatter_server)

        # Set up the logger
        self.logger_server = logging.getLogger("Server")
        self.logger_server.setLevel(logging.INFO)  # You can adjust the level to your needs
        self.logger_server.addHandler(console_handler_server)
        self.logger_server.propagate = False
        self.logger_server.info("Server logging set up")

    def handle_aspirate_command(self):
        try:
            command = request.get_json()
            volume = command.get("volume")
            rate = command.get("rate")
            self.logger_server.info(f"Server received aspirate command: volume={volume}, rate={rate}")

            if not self.robot.is_action_safe(volume):
                self.logger_server.warning("Server: Aspirate command out of safe bounds")
                return jsonify({"status": "Error", "message": "Error processing aspirate command: Position out of safe bounds"}), 400

            self.robot.aspirate_pipette(volume=volume, rate=rate)
            return jsonify({"status": "Success", "message": f"Aspirated {volume} ul at a rate of {rate} ul/s"})
        except Exception as e:
            if str(e) == "Serial not connected":
                e = self.handle_serial_error()
            else:
                self.logger_server.error(f"Server: Error processing aspirate command: {e}")
            
            return jsonify({"status": "Error", "message": f"Error processing aspirate command: {e}"}), 500

    def handle_dispense_command(self):
        try:
            command = request.get_json()
            volume = command.get("volume")
            rate = command.get("rate")
            self.logger_server.info(f"Server received dispense command: volume={volume}, rate={rate}")

            if not self.robot.is_action_safe(-volume):
                self.logger_server.warning("Server: Dispense command out of safe bounds")
                return jsonify({"status": "Error", "message": "Error processing dispense command: Position out of safe bounds"}), 400

            self.robot.dispense_pipette(volume=volume, rate=rate)
            return jsonify({"status": "Success", "message": f"Dispensed {volume} ul at a rate of {rate} ul/s"})
        
        except Exception as e:
            if str(e) == "Serial not connected":
                e = self.handle_serial_error()
            else:
                self.logger_server.error(f"Server: Error processing aspirate command: {e}")
            return jsonify({"status": "Error", "message": f"Error processing dispense command: {e}"}), 500

    def handle_ping(self):
        self.logger_server.info("Server received ping request")
        return jsonify({"status": "Success", "message": "pong"})

    def handle_request(self):
        try:
            current_pos = self.robot.get_current_volume()
            self.logger_server.info(f"Server received volume request: Current volume: {current_pos} ul")
            return jsonify({"status": "Success", "message": f"Current volume: {current_pos} ul"})
        except Exception as e:
            self.logger_server.error(f"Server: Error processing request: {e}")
            return jsonify({"status": "Error", "message": f"Error processing request: {e}"}), 500

    def handle_set_parameters(self):
        try:
            command = request.get_json()
            microsteps = command.get("stepper_pipet_microsteps")
            lead = command.get("pipet_lead")
            vtr = command.get("volume_to_travel_ratio")
            self.logger_server.info(f"Server received set parameters command: microsteps={microsteps}, lead={lead}, vtr={vtr}")
            return jsonify(self.robot.set_parameters(stepper_pipet_microsteps=microsteps, pipet_lead = lead, volume_to_travel_ratio = vtr)),500
        
        except Exception as e:
            if str(e) == "Serial not connected":
                e = self.handle_serial_error()
            else:
                self.logger_server.error(f"Server: Error processing aspirate command: {e}")
            return jsonify({"status": "Error", "message": f"Error processing parameter set command: {e}"}), 500

    def handle_eject(self):
        try:
            self.logger_server.info("Server received eject tip command")
            self.robot.eject_tip()
            return jsonify({"status": "Success", "message": "Tip ejected"})
        except Exception as e:
            if str(e) == "Serial not connected":
                e = self.handle_serial_error()
            else:
                self.logger_server.error(f"Server: Error processing aspirate command: {e}")
            return jsonify({"status": "Error", "message": f"Error processing eject_tip command: {e}"}), 500

    def zero_robot(self):
        try:
            self.logger_server.info("Server received zero robot command")
            self.robot.zero_robot()
            return jsonify({"status": "Success", "message": "Robot homed. Current volume: 0"})
        except Exception as e:
            self.logger_server.error(f"Server: Error processing zero_robot command: {e}")
            return jsonify({"status": "Error", "message": f"Error processing zero_robot command: {e}"}), 500

    def handle_serial_error(self):
        error = "Serial not connected"
        self.logger_server.critical(f"Server: Error processing aspirate command: {error}")
        width = len(str(error))+10
        errorstring = f"""\033[31m
{"-"*width}
{"Error opening serial port" : ^{width}}
{str(error): ^{width}}
{"-"*width}\033[0m"""
        return errorstring
        
    def run(self, host, port):
        from waitress import serve
        self.logger_server.info(f"Server running on http://{host}:{port}")
        serve(self.app, host=host, port=port)