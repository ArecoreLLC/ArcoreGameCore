extends Node3D
## Test world for the world-life components: land (height 1) for z < 5, water (height -3) beyond.
func height_at(_x: float, z: float) -> float:
    return 1.0 if z<5.0 else -3.0
