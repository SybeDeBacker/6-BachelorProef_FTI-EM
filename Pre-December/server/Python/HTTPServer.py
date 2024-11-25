from flask import Flask, request, jsonify
import math
from time import time

app = Flask(__name__)

# Global Variables and Robot Object
class RobotObject:
    def __init__(self):
        self.current_position = {"x": 10, "y": 10, "z": 10}  # Initial position
        self.pipet_level = 0  # Initial pipet level

    def MoveMotor(self, x, y, z):
        # Simulates moving the robot to a new position
        self.current_position = {"x": x, "y": y, "z": z}
        print(f"Robot moved to position X={x}, Y={y}, Z={z}")

    def MovePipet(self, level):
        # Simulates controlling the pipet
        self.pipet_level = level
        print(f"Pipet level set to {level} ml")

# Create an instance of RobotObject
robot = RobotObject()

# Safety limits
SAFE_LIMITS = {
    "x": (0, 100),
    "y": (0, 100),
    "z": (0, 100)
}

def is_position_safe(x, y, z):
    """
    Check if the target position is within safe operating bounds.
    """
    return (SAFE_LIMITS["x"][0] <= x <= SAFE_LIMITS["x"][1] and
            SAFE_LIMITS["y"][0] <= y <= SAFE_LIMITS["y"][1] and
            SAFE_LIMITS["z"][0] <= z <= SAFE_LIMITS["z"][1])

def get_current_position():
    """
    Get the current position of the robot.
    """
    return robot.current_position

@app.route('/move', methods=['POST'])
def handle_move_command():
    """
    Handles the /move endpoint to move the robot.
    """
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
            current_pos = get_current_position()
            x, y, z = current_pos["x"] + dx, current_pos["y"] + dy, current_pos["z"] + dz

        elif coord_system == "polar":
            r, theta, z = float(data["r"]), float(data["theta"]), float(data["z"])
            theta_rad = math.radians(theta)
            x, y = r * math.cos(theta_rad), r * math.sin(theta_rad)

        else:
            return jsonify({"status": "Error", "message": "Invalid coordinate system"}), 400

        if not is_position_safe(x, y, z):
            return jsonify({"status": "Error", "message": "Position out of safe bounds"}), 400

        robot.MoveMotor(x, y, z)
        return jsonify({"status": "Success", "message": f"Moved to position X={x} Y={y} Z={z}"})

    except Exception as e:
        return jsonify({"status": "Error", "message": f"Error processing move command: {e}"}), 500

@app.route('/pipet_control', methods=['POST'])
def handle_pipet_control():
    """
    Handles the /pipet_control endpoint to set the pipet level.
    """
    try:
        command = request.get_json()
        pipet_level = command["data"].get("pipet_level")

        if pipet_level is None:
            return jsonify({"status": "Error", "message": "Missing pipet_level in command"}), 400

        robot.MovePipet(pipet_level)
        return jsonify({"status": "Success", "message": f"Pipet level set to {pipet_level}"})

    except Exception as e:
        return jsonify({"status": "Error", "message": f"Error processing pipet control command: {e}"}), 500

@app.route('/ping', methods=['GET'])
def sample():
    """
    Handles the /ping endpoint to confirm connectivity.
    """
    print("Ping received")
    return jsonify({"status": "Success", "message": "test"})

@app.route('/', methods=['GET'])
def handle_ping():
    """
    Handles the /ping endpoint to confirm connectivity.
    """
    print("Ping received")
    return jsonify({"status": "Success", "message": "pong"})

@app.route('/request', methods=['GET'])
def handle_request():
    """
    Handles the /request endpoint to retrieve robot information.
    """
    try:
        current_pos = get_current_position()
        return jsonify({"status": "Success", "message": f"Current position: X={current_pos['x']} Y={current_pos['y']} Z={current_pos['z']}"})

    except Exception as e:
        return jsonify({"status": "Error", "message": f"Error processing request: {e}"}), 500

# Start the Flask server
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=80, debug=False)
