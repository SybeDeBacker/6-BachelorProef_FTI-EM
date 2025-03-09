from flask import Flask, request, jsonify
import math
from .robot_object import RobotObject

class RobotServer:
    def __init__(self, robot: RobotObject):
        self.robot = robot
        self.app = Flask(__name__)

        # Define routes
        self.app.add_url_rule('/move', 'move', self.handle_move_command, methods=['POST'])
        self.app.add_url_rule('/pipet_control', 'pipet_control', self.handle_pipet_control, methods=['POST'])
        self.app.add_url_rule('/ping', 'ping', self.handle_ping, methods=['GET'])
        self.app.add_url_rule('/request', 'request', self.handle_request, methods=['GET'])
        self.app.add_url_rule('/home_robot', 'home_robot', self.home_robot, methods=['GET'])

    def handle_move_command(self):
        try:
            command = request.get_json()
            coord_system = command.get("coordinate_system")
            data = command.get("data")

            if not coord_system or not data:
                return jsonify({"status": "Error", "message": "Invalid command format"}), 400

            if coord_system == "cartesian_absolute":
                x, y, z = float(data["x"]), float(data["y"]), float(data["z"])
            elif coord_system == "cartesian_relative":
                dx, dy, dz = float(data["x"]), float(data["y"]), float(data["z"])
                current_pos = self.robot.get_current_position()
                x, y, z = current_pos.x + dx, current_pos.y + dy, current_pos.z + dz
            elif coord_system == "polar":
                r, theta, z = float(data["r"]), float(data["theta"]), float(data["z"])
                theta_rad = math.radians(theta)
                x, y = r * math.cos(theta_rad), r * math.sin(theta_rad)
            else:
                return jsonify({"status": "Error", "message": "Invalid coordinate system"}), 400

            if not self.robot.is_position_safe(x, y, z):
                return jsonify({"status": "Error", "message": "Position out of safe bounds"}), 400

            self.robot.MoveMotor(x, y, z)
            return jsonify({"status": "Success", "message": f"Moved to position X={x} Y={y} Z={z}"})
        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing move command: {e}"}), 500

    def handle_pipet_control(self):
        try:
            command = request.get_json()
            pipet_level = command["data"].get("pipet_level")

            if pipet_level is None:
                return jsonify({"status": "Error", "message": "Missing pipet_level in command"}), 400

            self.robot.MovePipet(pipet_level)
            return jsonify({"status": "Success", "message": f"Pipet level set to {pipet_level}"})
        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing pipet control command: {e}"}), 500

    def handle_ping(self):
        return jsonify({"status": "Success", "message": "pong"})

    def handle_request(self):
        try:
            current_pos = self.robot.get_current_position()
            return jsonify({"status": "Success", "message": f"Current position: X={current_pos.x} Y={current_pos.y} Z={current_pos.z}"})
        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing request: {e}"}), 500

    def home_robot(self):
        try:
            self.robot.home_robot()
            return jsonify({"status": "Success", "message": "Robot homed. Current position: X=0 Y=0 Z=0"})
        except Exception as e:
            return jsonify({"status": "Error", "message": f"Error processing home_robot command: {e}"}), 500

    def run(self, host, port):
        from waitress import serve
        print(fr"* Running on http://{host}:{port}")
        serve(self.app, host=host, port=port)
