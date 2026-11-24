extends SceneTree
const Stroke = preload("../ink_stroke.gd")
const Geom = preload("../ink_geom.gd")
const Cloud = preload("../pdollar.gd")
const DTW = preload("../dtw.gd")
const Motion = preload("../motion.gd")
const Reference = preload("sparc_reference.gd")
const Samples = preload("../sample_math.gd")
var failures := 0
var checks := 0
func check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures += 1
		printerr(label)
func _init() -> void:
	for rate in [30, 60, 120, 240]:
		for shape in [0, 1, 2]:
			var s := Stroke.new()
			for i in range(rate + 1):
				var t: float = float(i) / rate
				var pos := Vector2(t * 100.0, 0.0)
				if shape == 1:
					pos = Vector2(cos(t * TAU), sin(t * TAU)) * 50.0
				elif shape == 2:
					pos.y = sin(t * PI) * 80.0
				s.add(10.0 + t, pos, 0.2 + t * 0.3)
			check(abs(s.duration() - 1.0) < 0.00001, "duration")
			check(s.has_real_pressure(), "analog pressure")
			var rs := Geom.resample(s.points, 32)
			check(rs.size() == 32 and rs[0] == s.points[0] and rs[-1] == s.points[-1], "resample endpoints")
			check(DTW.distance(rs, rs) == 0.0, "DTW identity")
			var a := Cloud.cloud([s.points], 32)
			var moved := PackedVector2Array()
			for p in s.points:
				moved.append(p * 2.0 + Vector2(150, -80))
			check(Cloud.distance(a, Cloud.cloud([moved], 32)) < 0.001, "translation/scale invariance")
			var timed := Motion._time_resample(s, 60.0)
			check(timed.size() == 61, "alternate rates")
	check(Geom.resample(PackedVector2Array([Vector2.ZERO, Vector2.ONE]), 1).size() == 1, "single point budget")
	check(Cloud.cloud([], 32).is_empty(), "empty cloud")
	check(Cloud.cloud([], 0).is_empty(), "zero cloud budget")
	check(is_inf(DTW.distance(PackedVector2Array(), PackedVector2Array())), "empty DTW")
	var s := Stroke.new()
	for t in [0.0, 0.1, 0.1, 0.1, 0.2]:
		s.add(t, Vector2.ZERO)
	s.repair_timestamps()
	for i in range(1, s.size()):
		check(s.times[i] > s.times[i-1], "timestamp repair")
	check(Samples.median([4, 1, 3, 2]) == 2.5, "median")
	check(Samples.smooth(PackedFloat64Array([0, 1, 2]), PackedFloat32Array([2, 4, 6]), 1.0) == PackedFloat32Array([2, 3, 5]), "window mean")
	check(Motion.sparc(PackedFloat32Array([0, 1, 2]), 60, 10, 0.05, 128) == 0, "short SPARC")
	for hz in [30.0, 60.0, 120.0]:
		for cycles in [1.0, 3.0, 7.0]:
			var speed := PackedFloat32Array()
			for i in 120:
				speed.append(1.0 + sin(float(i) / 119.0 * TAU * cycles))
			check(abs(Motion.sparc(speed, hz, 10, 0.05, 128) - Reference.sparc(speed, hz, 10, 0.05, 128)) < 0.0001, "legacy DFT parity")
	print("STROKES_0.1.0_PASS %d checks" % checks if failures == 0 else "STROKES_FAIL")
	quit(0 if failures == 0 else 1)
