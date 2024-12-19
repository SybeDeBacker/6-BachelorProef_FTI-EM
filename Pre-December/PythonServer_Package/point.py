class Point:
    def __init__(self, x:float, y:float, z:float, coordinate_system: str = "cartesian_absolute") -> None:
        self.x = x
        self.y = y
        self.z = z
        self.coordinate_system = coordinate_system
        self.coordinates = (x,y,z)
        self.current_index = 0

    def __repr__(self):
        return f"Point(x={self.x}, y={self.y}, z={self.z})"
    
    def __iter__(self):
        self.current_index = 0
        return self
    
    def __next__(self):
        if self.current_index == 3:
            raise StopIteration
        
        self.current_index += 1
        return self.coordinates[self.current_index-1]
