extends RefCounted
## Sample a horizontal ring plus its center against a caller-owned terrain field.
## Discrete samples are not swept collision detection or proof between samples.
const VERSION := "1.0.0"

static func clear(home: Vector3, radius: float, margin: float, height_at: Callable, samples := 32) -> bool:
    if not home.is_finite() or not is_finite(radius) or not is_finite(margin):return false
    if radius<0 or margin<0 or samples<3 or not height_at.is_valid():return false
    var ceiling := home.y-margin
    for i in range(samples):
        var p := home+Vector3(cos(i*TAU/samples),0,sin(i*TAU/samples))*(radius+margin)
        var height = height_at.call(p.x,p.z)
        if not _height_valid(height) or height>ceiling:return false
    var center = height_at.call(home.x,home.z)
    # Preserve the source contract: ring equality allowed, center equality blocked.
    return _height_valid(center) and center<ceiling

static func _height_valid(value: Variant) -> bool:
    return (value is float or value is int) and is_finite(float(value))
