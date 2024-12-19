from .point import Point

class CoordinateRange:
    def __init__(self, x_range: list[float], y_range: list[float], z_range: list[float], coordinate_system: str = "cartesian_absolute") -> None:
        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.ranges = [x_range, y_range, z_range]
        self.current_range_index = 0
        self.coordinate_system = coordinate_system

    def contains(self, Point: Point):
        x_safe = (min(self.x_range) <= Point.x <= max(self.x_range))
        y_safe = (min(self.y_range) <= Point.y <= max(self.y_range))
        z_safe = (min(self.z_range) <= Point.z <= max(self.z_range))
        return x_safe and y_safe and z_safe

    def __repr__(self):
        return f"{self.x_range}, {self.y_range}, {self.z_range}"
    
    def __iter__(self):
        self.current_range_index = 0
        return self

    def __next__(self):
        if self.current_range_index >= len(self.ranges):
            raise StopIteration
        self.current_range_index += 1
        return self.ranges[self.current_range_index-1]
