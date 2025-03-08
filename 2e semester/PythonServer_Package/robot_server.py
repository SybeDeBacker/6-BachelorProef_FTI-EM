from flask import Flask, request, jsonify
from .robot_object import RobotObject
import logging

class RobotServer:
    def __init__(self, robot: RobotObject):
        self.robot = robot
        self.app = Flask(__name__)
        
        logging.basicConfig(
            level=logging.INFO,
            format="\033[1;4;35m%(asctime)s %(levelname)s %(message)s\033[0m",  # Green color for Server logs
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Define routes
        self.app.add_url_rule('/aspirate', 'aspirate', self.handle_aspirate_command, methods=['POST'])
        self.app.add_url_rule('/dispense', 'dispense', self.handle_dispense_command, methods=['POST'])
        self.app.add_url_rule('/set_parameters', 'set_parameters', self.handle_set_parameters, methods=['POST'])
        self.app.add_url_rule('/ping', 'ping', self.handle_ping, methods=['GET'])
        self.app.add_url_rule('/request', 'request', self.handle_request, methods=['GET'])
        self.app.add_url_rule('/zero_robot', 'zero_robot', self.zero_robot, methods=['GET'])
        self.app.add_url_rule('/eject_tip', 'eject_tip', self.handle_eject, methods=['GET'])

    def handle_aspirate_command(self):
        try:
            command = request.get_json()
            volume = command.get("volume")
            rate = command.get("rate")
            logging.info(f"Server received aspirate command: volume={volume}, rate={rate}")

            if not self.robot.is_action_safe(volume):
                logging.warning("Server: Aspirate command out of safe bounds")
                return jsonify({"status": "Error", "message": "Error processing aspirate command: Position out of safe bounds"}), 400

            self.robot.aspirate_pipette(volume=volume, rate=rate)
            logging.info(f"Server: Aspirated {volume} ul at a rate of {rate} ul/s")
            return jsonify({"status": "Success", "message": f"Aspirated {volume} ml at a rate of {rate} ml/s"})
        except Exception as e:
            logging.error(f"Server: Error processing aspirate command: {e}")
            if str(e) == "13":
                e = self.handle_serial_error()
            return jsonify({"status": "Error", "message": f"Error processing aspirate command: {e}"}), 500

    def handle_dispense_command(self):
        try:
            command = request.get_json()
            volume = command.get("volume")
            rate = command.get("rate")
            logging.info(f"Server received dispense command: volume={volume}, rate={rate}")

            if not self.robot.is_action_safe(-volume):
                logging.warning("Server: Dispense command out of safe bounds")
                return jsonify({"status": "Error", "message": "Error processing dispense command: Position out of safe bounds"}), 400

            self.robot.dispense_pipette(volume=volume, rate=rate)
            logging.info(f"Server: Dispensed {volume} ml at a rate of {rate} ml/s")
            return jsonify({"status": "Success", "message": f"Dispensed {volume} ml at a rate of {rate} ml/s"})
        
        except Exception as e:
            logging.error(f"Server: Error processing dispense command: {e}")
            if str(e) == "13":
                e = self.handle_serial_error()
            return jsonify({"status": "Error", "message": f"Error processing dispense command: {e}"}), 500

    def handle_serial_error(self):
        error = "Serial not connected"
        logging.critical(error)
        width = len(str(error))+10
        errorstring = f"""\033[31m
{"-"*width}
{"Error opening serial port" : ^{width}}
{str(error): ^{width}}
{"-"*width}\033[0m"""
        return errorstring
    
    def handle_ping(self):
        logging.info("Server received ping request")
        return jsonify({"status": "Success", "message": "pong"})

    def handle_request(self):
        try:
            current_pos = self.robot.get_current_volume()
            logging.info(f"Server: Current volume: {current_pos} ml")
            return jsonify({"status": "Success", "message": f"Current volume: {current_pos} ml"})
        except Exception as e:
            logging.error(f"Server: Error processing request: {e}")
            return jsonify({"status": "Error", "message": f"Error processing request: {e}"}), 500

    def handle_set_parameters(self):
        try:
            command = request.get_json()
            microsteps = command.get("stepper_pipet_microsteps")
            lead = command.get("pipet_lead")
            vtr = command.get("volume_to_travel_ratio")
            logging.info(f"Server received set parameters command: microsteps={microsteps}, lead={lead}, vtr={vtr}")
            return jsonify(self.robot.set_parameters(stepper_pipet_microsteps=microsteps, pipet_lead = lead, volume_to_travel_ratio = vtr)),500
        
        except Exception as e:
            logging.error(f"Server: Error processing set parameters command: {e}")
            if str(e) == "13":
                e = self.handle_serial_error()
            return jsonify({"status": "Error", "message": f"Error processing parameter set command: {e}"}), 500

    def handle_eject(self):
        try:
            logging.info("Server received eject tip command")
            self.robot.eject_tip()
            logging.info("Server: Tip ejected")
            return jsonify({"status": "Success", "message": "Tip ejected"})
        except Exception as e:
            logging.error(f"Server: Error processing eject_tip command: {e}")
            if str(e) == "13":
                e = self.handle_serial_error()
            return jsonify({"status": "Error", "message": f"Error processing eject_tip command: {e}"}), 500

    def zero_robot(self):
        try:
            logging.info("Server received zero robot command")
            self.robot.zero_robot()
            logging.info("Server: Robot homed. Current volume: 0")
            return jsonify({"status": "Success", "message": "Robot homed. Current volume: 0"})
        except Exception as e:
            logging.error(f"Server: Error processing zero_robot command: {e}")
            return jsonify({"status": "Error", "message": f"Error processing zero_robot command: {e}"}), 500

    def run(self, host, port):
        from waitress import serve
        logging.info(f"Server running on http://{host}:{port}")
        serve(self.app, host=host, port=port)