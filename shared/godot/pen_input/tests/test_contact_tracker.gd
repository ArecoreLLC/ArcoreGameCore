extends SceneTree

const Tracker = preload("../contact_tracker.gd")
var failures := 0
var checks := 0


func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)


func _init() -> void:
	var tracker := Tracker.new()
	# Inject two device calibrations and two preference sets, without globals.
	var desktop_limit := Tracker.mm_to_pixels(2.5, 96.0, 1.0)
	var tablet_limit := Tracker.mm_to_pixels(2.5, 254.0, 2.0)
	check(is_equal_approx(desktop_limit, 9.4488189), "desktop physical units")
	check(is_equal_approx(tablet_limit, 12.5), "scaled tablet physical units")
	check(is_equal_approx(Tracker.mm_to_pixels(1, 25.4, 0), 1000), "scale clamp")
	tracker.press_touch(7, Vector2(10, 10), 20.0)
	tracker.move_touch(7, Vector2(21, 10))
	check(not tracker.is_resting(7, 20.5, desktop_limit, 0.12), "desktop contact moved too far")
	check(tracker.is_resting(7, 20.5, tablet_limit, 0.12), "tablet contact within physical threshold")
	check(not tracker.is_resting(7, 20.5, tablet_limit, 0.8), "alternate resting duration")
	tracker.move_touch(7, Vector2(10, 10))
	check(not tracker.is_resting(7, 21, desktop_limit, 0.12), "return to origin retains maximum excursion")
	check(not tracker.is_resting(7, 21, 11, 0.12), "distance boundary is strict")
	tracker.press_touch(42, Vector2.ZERO, 30)
	check(tracker.is_resting(42, 30.25, 1, 0.25), "duration boundary is inclusive")
	check(not tracker.is_resting(42, 29, 1, 0.25), "earlier clock does not mature contact")
	tracker.release_touch(7)
	check(not tracker.is_resting(7, 40, 100, 0), "release removes only released contact")
	check(tracker.is_resting(42, 40, 1, 0), "other device contact remains")
	tracker.press_touch(42, Vector2.ONE, 50)
	check(not tracker.is_resting(42, 50, 1, 0.1), "reused index restarts age")
	tracker.move_touch(999, Vector2.ONE)
	tracker.release_touch(999)
	check(not tracker.is_resting(999, 100, 10, 0), "unknown contacts ignored")
	tracker.clear_touches()
	check(not tracker.is_resting(42, 100, 10, 0), "reset removes contacts")
	var other := Tracker.new()
	tracker.press_touch(1, Vector2.ZERO, 0)
	check(not other.is_resting(1, 1, 10, 0), "instances do not share contacts")
	tracker.record_contact(Vector2(12, 34), 123.25)
	check(Tracker.hover_ends_contact(true, false, 0), "hover recovers missed release")
	check(tracker.last_position == Vector2(12, 34) and tracker.last_time == 123.25, "recovery preserves contact endpoint and injected time")
	check(not Tracker.hover_ends_contact(true, true, 0), "held button protects contact")
	check(not Tracker.hover_ends_contact(false, false, 0), "ineligible source protected")
	check(not Tracker.hover_ends_contact(true, false, 0.2), "pressure protects contact")
	check(Tracker.hover_ends_contact(true, false, 0.001), "release boundary inclusive")
	check(Tracker.hover_ends_contact(true, false, 0.02, 0.05), "alternate pressure threshold")
	check(not Tracker.hover_ends_contact(true, false, 0.02), "default pressure threshold")
	check(Tracker.hover_ends_contact(true, false, NAN), "invalid pressure follows unknown-pressure fallback")
	check(Tracker.sanitize_pressure(INF) == -1 and Tracker.sanitize_pressure(-INF) == -1, "infinite pressure sanitized")
	check(Tracker.sanitize_pressure(255) == 255, "finite device pressure is not clamped")
	for emulated_id in [-1, -77]:
		check(Tracker.rejects_emulated_mouse(true, emulated_id, emulated_id), "synthetic mouse rejected")
		check(not Tracker.rejects_emulated_mouse(false, emulated_id, emulated_id), "original touch retained")
		check(not Tracker.rejects_emulated_mouse(true, 3, emulated_id), "physical device retained")
	if failures == 0:
		print("PASS pen_input 0.1.0 (%d checks)" % checks)
	quit(0 if failures == 0 else 1)
