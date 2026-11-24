extends SceneTree
const Stroke = preload("../../strokes/ink_stroke.gd")
const Codec = preload("../telemetry_codec.gd")
const Replay = preload("../recorded_replay.gd")
var failures := 0
var checks := 0
func check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures += 1
		printerr(label)
func _init() -> void:
	for rate in [24, 90, 240]:
		var stroke := Stroke.new()
		for i in range(rate + 1):
			stroke.add(5.0 + float(i) / rate, Vector2(i, i * 2), -1, Vector2(0.1, 0.2))
		var encoded := Codec.encode_checked([stroke])
		check(encoded.ok, "encode")
		var parsed := Replay.parse_line(JSON.stringify({"strokes": encoded.data, "factor": 3}))
		check(parsed.ok, "parse")
		var decoded := Codec.decode_checked(parsed.record.strokes)
		check(decoded.ok and decoded.strokes[0].size() == rate + 1, "roundtrip length")
		check(abs(decoded.strokes[0].duration() - 1.0) < 0.0001, "roundtrip time")
		var result := Replay.evaluate(parsed.record, func(record, strokes): return {"ok": true, "value": strokes[0].length() * record.factor})
		check(result.ok and abs(result.value - stroke.length() * 3) < 0.01, "synthetic length evaluator")
		var count_result := Replay.evaluate(parsed.record, func(_record, strokes): return {"ok": true, "value": strokes[0].size()})
		check(count_result.ok and count_result.value == rate + 1, "alternate evaluator")
	var valid := {"t": [0, 10], "x": [1, 2], "y": [3, 4], "p": [-1, -1]}
	check(Codec.decode_checked([valid]).ok, "legacy missing tilt")
	for field in ["t", "x", "y", "p", "tx", "ty"]:
		var bad := valid.duplicate(true)
		bad[field] = [1]
		check(not Codec.decode_checked([bad]).ok, "length rejection " + field)
	for value in [NAN, INF, -INF, null, "bad", true]:
		for field in ["t", "x", "y", "p"]:
			var bad := valid.duplicate(true)
			bad[field][0] = value
			var result := Codec.decode_checked([valid, bad])
			check(not result.ok and not result.has("strokes"), "atomic finite/type rejection")
	for field in ["x", "y", "p"]:
		var huge := valid.duplicate(true)
		huge[field][0] = 1e300
		check(not Codec.decode_checked([huge]).ok, "storage overflow")
	var backwards := valid.duplicate(true)
	backwards.t = [10, 0]
	check(not Codec.decode_checked([backwards]).ok, "decreasing timestamps")
	for bad in [null, {}, [null], [42]]:
		check(not Codec.decode_checked(bad).ok, "bad container")
	check(not Replay.parse_line("{").ok, "invalid JSON")
	check(not Replay.parse_line("[]").ok, "nonobject JSON")
	check(not Replay.evaluate({"strokes": [valid]}, Callable()).ok, "invalid callback")
	check(not Replay.evaluate({"strokes": [valid]}, func(_r, _s): return 2).ok, "bad evaluator envelope")
	var error := Replay.evaluate({"strokes": [valid]}, func(_r, _s): return {"ok": false, "error": "synthetic failure"})
	check(not error.ok and error.error == "synthetic failure", "evaluator failure")
	var broken := Stroke.new()
	broken.points.append(Vector2.ZERO)
	check(not Codec.encode_checked([broken]).ok, "encode mismatched arrays")
	broken = Stroke.new()
	broken.add(0, Vector2(INF, 0))
	check(not Codec.encode_checked([broken]).ok, "encode nonfinite")
	check(Codec.sanitize({"x": NAN}).x == null, "sanitize legacy behavior")
	print("REPLAY_0.1.0_PASS %d checks" % checks if failures == 0 else "REPLAY_FAIL")
	quit(0 if failures == 0 else 1)
