extends RefCounted
## Pen input reliability primitives, v0.1.0. No autoloads, clock or device queries.
## The adapter owns source arbitration and decides which samples count as contact.

var last_position := Vector2.ZERO
var last_time := 0.0
var _touches: Dictionary = {}


func record_contact(position: Vector2, time_seconds: float) -> void:
	last_position = position
	last_time = time_seconds


func press_touch(index: int, position: Vector2, time_seconds: float) -> void:
	_touches[index] = {"start": position, "t0": time_seconds, "moved": 0.0}


func move_touch(index: int, position: Vector2) -> void:
	if _touches.has(index):
		var touch: Dictionary = _touches[index]
		touch["moved"] = maxf(touch["moved"], position.distance_to(touch["start"]))


func release_touch(index: int) -> void:
	_touches.erase(index)


func clear_touches() -> void:
	_touches.clear()


func is_resting(index: int, time_seconds: float, still_pixels: float, still_seconds: float) -> bool:
	if not _touches.has(index):
		return false
	var touch: Dictionary = _touches[index]
	return touch["moved"] < still_pixels and time_seconds - touch["t0"] >= still_seconds


static func rejects_emulated_mouse(is_mouse: bool, device_id: int, emulated_device_id: int) -> bool:
	return is_mouse and device_id == emulated_device_id


## Call with the adapter's eligible source (InkFury uses active non-finger sources).
## A new physical down is separately authoritative; end at last_position/last_time.
static func hover_ends_contact(eligible_contact: bool, primary_button_down: bool, pressure: float, release_threshold: float = 0.001) -> bool:
	return eligible_contact and not primary_button_down and sanitize_pressure(pressure) <= release_threshold


static func mm_to_pixels(mm: float, pixels_per_inch: float, viewport_scale_x: float) -> float:
	return mm * pixels_per_inch / 25.4 / maxf(viewport_scale_x, 1e-3)


static func sanitize_pressure(pressure: float) -> float:
	return pressure if is_finite(pressure) else -1.0
