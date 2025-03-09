from .point import Point
from .coordinate_range import CoordinateRange

class RobotObject:
    def __init__(self):
        self.current_position = Point(10, 20, 30)
        self.pipet_level = 0
        self.safe_bounds = CoordinateRange([0, 100], [0, 100], [0, 50])

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
