from flask import Flask, request, jsonify
import math
from .robot_object import RobotObject

class RobotServer:
    def __init__(self, robot: RobotObject):
        self.robot = robot
        self.app = Flask(__name__)

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

            if not self.robot.is_action_safe(volume):
                return jsonify({"status": "Error", "message": "Position out of safe bounds"}), 400

            self.robot.aspirate_pipette(volume=volume, rate=rate)
            return jsonify({"status": "Success", "message": f"Aspirated {volume} ml at a rate of {rate} ml/s"})
        
        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing aspirate command: {e}"}), 500

    def handle_dispense_command(self):
        try:
            command = request.get_json()
            volume = command.get("volume")
            rate = command.get("rate")

            if not self.robot.is_action_safe(-volume):
                return jsonify({"status": "Error", "message": "Position out of safe bounds"}), 400

            self.robot.dispense_pipette(volume=volume, rate=rate)
            return jsonify({"status": "Success", "message": f"Dispensed {volume} ml at a rate of {rate} ml/s"})
        
        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing dispense command: {e}"}), 500

    def handle_ping(self):
        return jsonify({"status": "Success", "message": "pong"})

    def handle_request(self):
        try:
            current_pos = self.robot.get_current_volume()
            return jsonify({"status": "Success", "message": f"Current volume: {current_pos} ml"})
        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing request: {e}"}), 500

    def handle_set_parameters(self):
        try:
            command = request.get_json()
            microsteps = command.get("stepper_pipet_microsteps")
            lead = command.get("pipet_lead")
            vtr = command.get("volume_to_travel_ratio")
            self.robot.set_parameters(stepper_pipet_microsteps=microsteps, pipet_lead = lead, volume_to_travel_ratio = vtr)

            return jsonify({"status": "Success", "message": f"Set parameters"})
        
        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing parameter set command: {e}"}), 500

    def handle_eject(self):
        try:
            self.robot.eject_tip()
            return jsonify({"status": "Success", "message": "Tip ejected"})
        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing eject_tip command: {e}"}), 500

    def zero_robot(self):
        try:
            self.robot.zero_robot()
            return jsonify({"status": "Success", "message": "Robot homed. Current volume: 0"})
        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing home_robot command: {e}"}), 500

    def run(self, host, port):
        from waitress import serve
        print(fr"* Running on http://{host}:{port}")
        serve(self.app, host=host, port=port)