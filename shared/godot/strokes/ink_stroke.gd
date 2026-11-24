extends RefCounted
const InkGeom = preload("ink_geom.gd")
## One pen-down → pen-up stroke. Pure data, no scene dependencies.
## Positions are in canvas pixels (y down). Times are in seconds.
## Pressure is the RAW device value (0..1), or -1 when the source has none.

var points := PackedVector2Array()
var times := PackedFloat64Array()
var pressures := PackedFloat32Array()
var tilts := PackedVector2Array()


func add(t: float, pos: Vector2, pressure: float = -1.0, tilt: Vector2 = Vector2.ZERO) -> void:
	if not is_finite(pressure):
		pressure = -1.0  # iOS can report NaN (force / maximumPossibleForce with max = 0)
	points.append(pos)
	times.append(t)
	pressures.append(pressure)
	tilts.append(tilt)


func size() -> int:
	return points.size()


func duration() -> float:
	if times.size() < 2:
		return 0.0
	return times[times.size() - 1] - times[0]


func length() -> float:
	return InkGeom.path_length(points)


## True when the stroke carries real analog pressure: values strictly inside (0, 1)
## that actually vary. A mouse (0/1), finger on most devices, or a passive stylus fail this.
func has_real_pressure() -> bool:
	var lo := INF
	var hi := -INF
	var inside := 0
	for p in pressures:
		if p < 0.0:
			continue
		lo = minf(lo, p)
		hi = maxf(hi, p)
		if p > 0.001 and p < 0.999:
			inside += 1
	return inside >= maxi(3, pressures.size() / 2) and (hi - lo) > 0.01


## Engines often deliver several samples in one frame with the same receipt time.
## Spread each run of identical timestamps evenly back to the previous distinct time
## so velocity/jerk estimates are not polluted by zero-dt samples.
func repair_timestamps() -> void:
	var n := times.size()
	if n < 3:
		return
	var i := 1
	while i < n:
		if times[i] > times[i - 1] + 1e-5:
			i += 1
			continue
		# run of samples sharing (approximately) times[i - 1]
		var run_start := i - 1
		var j := i
		while j < n and times[j] <= times[run_start] + 1e-5:
			j += 1
		var t_prev: float = times[run_start - 1] if run_start > 0 else times[run_start] - 1.0 / 240.0
		var t_end: float = times[run_start]
		var count := j - run_start
		for k in count:
			times[run_start + k] = t_prev + (t_end - t_prev) * float(k + 1) / float(count)
		i = j
	# guarantee strictly increasing
	for k in range(1, n):
		if times[k] <= times[k - 1]:
			times[k] = times[k - 1] + 1e-4
