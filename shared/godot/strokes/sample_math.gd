extends RefCounted

static func smooth(times: PackedFloat64Array, values: PackedFloat32Array, window_s: float) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(values.size())
	var start := 0
	var acc := 0.0
	for i in values.size():
		acc += values[i]
		while times[i] - times[start] > window_s and start < i:
			acc -= values[start]
			start += 1
		out[i] = acc / float(i - start + 1)
	return out


static func median(values: Array) -> float:
	if values.is_empty():
		return 0.0
	var s := values.duplicate()
	s.sort()
	var m := s.size() / 2
	return float(s[m]) if s.size() % 2 == 1 else (float(s[m - 1]) + float(s[m])) * 0.5
