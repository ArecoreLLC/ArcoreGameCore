extends RefCounted
const StrokeData = preload("../strokes/ink_stroke.gd")

## Make values JSON-safe: NaN/Inf → null, packed arrays → plain arrays, Vector2 → [x, y].
static func sanitize(v: Variant) -> Variant:
	match typeof(v):
		TYPE_FLOAT:
			return v if is_finite(v) else null
		TYPE_VECTOR2:
			return [sanitize(v.x), sanitize(v.y)]
		TYPE_DICTIONARY:
			var out := {}
			for k in v:
				out[str(k)] = sanitize(v[k])
			return out
		TYPE_ARRAY, TYPE_PACKED_FLOAT32_ARRAY, TYPE_PACKED_FLOAT64_ARRAY, TYPE_PACKED_INT32_ARRAY, TYPE_PACKED_VECTOR2_ARRAY:
			var arr: Array = []
			for x in v:
				arr.append(sanitize(x))
			return arr
		_:
			return v


static func _encode_strokes(strokes: Array) -> Array:
	var out: Array = []
	var t0 := INF
	for s: StrokeData in strokes:
		if s.size() > 0:
			t0 = minf(t0, s.times[0])
	for s: StrokeData in strokes:
		var ts: Array = []
		var xs: Array = []
		var ys: Array = []
		var ps: Array = []
		var tx: Array = []
		var ty: Array = []
		for i in s.size():
			ts.append(snappedf((s.times[i] - t0) * 1000.0, 0.01))
			xs.append(snappedf(s.points[i].x, 0.01))
			ys.append(snappedf(s.points[i].y, 0.01))
			ps.append(snappedf(s.pressures[i], 0.0001))
			tx.append(snappedf(s.tilts[i].x, 0.001))
			ty.append(snappedf(s.tilts[i].y, 0.001))
		out.append({"t": ts, "x": xs, "y": ys, "p": ps, "tx": tx, "ty": ty})
	return out



## Atomic validation: a bad sample rejects the entire batch; no partial strokes escape.
static func decode_checked(data: Variant, factory: Callable = Callable()) -> Dictionary:
	if not data is Array:
		return {"ok": false, "error": "strokes must be an array"}
	for index in data.size():
		var d: Variant = data[index]
		if not d is Dictionary:
			return {"ok": false, "error": "stroke %d must be a dictionary" % index}
		if not d.get("t", null) is Array:
			return {"ok": false, "error": "stroke %d: missing t array" % index}
		var count: int = d.t.size()
		for key in ["t", "x", "y", "p", "tx", "ty"]:
			if key in ["tx", "ty"] and not d.has("tx") and not d.has("ty"):
				continue
			if not d.get(key, null) is Array or d[key].size() != count:
				return {"ok": false, "error": "stroke %d: %s length/type mismatch" % [index, key]}
			for v in d[key]:
				if not (v is float or v is int) or not is_finite(float(v)):
					return {"ok": false, "error": "stroke %d: %s requires finite numbers" % [index, key]}
		for i in range(1, count):
			if d.t[i] < d.t[i - 1]:
				return {"ok": false, "error": "stroke %d: decreasing time" % index}
	var out: Array = []
	for d: Dictionary in data:
		var s: Variant = factory.call() if factory.is_valid() else StrokeData.new()
		if not s is StrokeData:
			return {"ok": false, "error": "factory must return stroke data"}
		for i in d.t.size():
			var tilt := Vector2(float(d.tx[i]), float(d.ty[i])) if d.has("tx") else Vector2.ZERO
			var position := Vector2(float(d.x[i]), float(d.y[i]))
			var pressure := PackedFloat32Array([float(d.p[i])])[0]
			if not position.is_finite() or not tilt.is_finite() or not is_finite(pressure):
				return {"ok": false, "error": "sample exceeds storage precision"}
			s.add(float(d.t[i]) / 1000.0, position, pressure, tilt)
		out.append(s)
	return {"ok": true, "strokes": out}

static func encode_checked(strokes: Array) -> Dictionary:
	for s in strokes:
		if not s is StrokeData:
			return {"ok": false, "error": "expected stroke data"}
		if s.times.size() != s.size() or s.pressures.size() != s.size() or s.tilts.size() != s.size():
			return {"ok": false, "error": "sample array length mismatch"}
		for i in s.size():
			if not is_finite(s.times[i]) or not s.points[i].is_finite() or not is_finite(s.pressures[i]) or not s.tilts[i].is_finite():
				return {"ok": false, "error": "nonfinite sample"}
			if i > 0 and s.times[i] < s.times[i - 1]:
				return {"ok": false, "error": "decreasing time"}
	var data := _encode_strokes(strokes)
	var checked := decode_checked(data)
	if not checked.ok:
		return checked
	return {"ok": true, "data": data}

static func encode_strokes(strokes: Array) -> Array:
	var result := encode_checked(strokes)
	return result.get("data", [])

static func decode_strokes(data: Array) -> Array:
	var result := decode_checked(data)
	return result.get("strokes", [])
