from flask import Flask, request, jsonify
import math

# Global Variables and Classes
class Point:
    def __init__(self, x: float, y: float, z: float, coordinate_system: str = "cartesian_absolute") -> None:
        self.x = x
        self.y = y
        self.z = z
        self.coordinate_system = coordinate_system

    def __repr__(self):
        return f"Point(x={self.x}, y={self.y}, z={self.z})"


class Coordinate_Range:
    def __init__(self, x_range, y_range, z_range, coordinate_system="cartesian_absolute"):
        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.coordinate_system = coordinate_system

    def contains(self, point: Point):
        return (
            self.x_range[0] <= point.x <= self.x_range[1] and
            self.y_range[0] <= point.y <= self.y_range[1] and
            self.z_range[0] <= point.z <= self.z_range[1]
        )


class RobotObject:
    def __init__(self):
        self.current_position = Point(10, 20, 30)
        self.pipet_level = 0
        self.safe_bounds = Coordinate_Range([0, 100], [0, 100], [0, 50])

    def MoveMotor(self, x, y, z):
        self.current_position = Point(x, y, z)
        print(f"Robot moved to position X={x}, Y={y}, Z={z}")

    def MovePipet(self, level):
        self.pipet_level = level
        print(f"Pipet level set to {level} ml")

    def get_current_position(self):
        return self.current_position

    def is_position_safe(self, x, y, z):
        return self.safe_bounds.contains(Point(x, y, z))

    def home_robot(self):
        self.current_position = Point(0, 0, 0)


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

            if coord_system == "cartesian_abs":
                x, y, z = float(data["x"]), float(data["y"]), float(data["z"])
            elif coord_system == "cartesian_rel":
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

    def run(self, host, port, debug):
        self.app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    robot = RobotObject()
    server = RobotServer(robot)
    server.run(host='127.0.0.1', port=80, debug=False)
