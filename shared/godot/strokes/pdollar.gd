extends RefCounted
const InkGeom = preload("ink_geom.gd")
## $P point-cloud recognizer distance (Vatavu, Anthony & Wobbrock 2012).
## Stroke order and direction are ignored, so this is a forgiving "does it look like it" check.


## Normalize a multi-stroke shape into an n-point cloud (centroid at origin, uniform scale).
static func cloud(strokes: Array, n: int) -> PackedVector2Array:
	# Per-stroke resampling (by length share) avoids bridging pen-up gaps; it lands close
	# to n points, then we decimate/pad to exactly n.
	if n <= 0:
		return PackedVector2Array()
	var pts := InkGeom.flatten(InkGeom.resample_strokes(strokes, n))
	if pts.is_empty():
		return pts
	if pts.size() > n:
		var trimmed := PackedVector2Array()
		for i in n:
			trimmed.append(pts[int(floor(float(i) * pts.size() / n))])
		pts = trimmed
	while pts.size() < n:
		pts.append(pts[pts.size() - 1])
	var c := InkGeom.centroid(pts)
	var minp := Vector2(INF, INF)
	var maxp := Vector2(-INF, -INF)
	for p in pts:
		minp = minp.min(p)
		maxp = maxp.max(p)
	var s := maxf(maxf(maxp.x - minp.x, maxp.y - minp.y), 1e-9)
	var out := PackedVector2Array()
	for p in pts:
		out.append((p - c) / s)
	return out


static func distance(a: PackedVector2Array, b: PackedVector2Array) -> float:
	var n := mini(a.size(), b.size())
	if n == 0:
		return INF
	var step := maxi(1, int(floor(pow(n, 0.5))))
	var best := INF
	var i := 0
	while i < n:
		best = minf(best, _cloud_distance(a, b, i, n))
		best = minf(best, _cloud_distance(b, a, i, n))
		i += step
	return best


static func _cloud_distance(a: PackedVector2Array, b: PackedVector2Array, start: int, n: int) -> float:
	var matched := PackedByteArray()
	matched.resize(n)
	matched.fill(0)
	var total := 0.0
	var i := start
	var weight_i := 0
	while true:
		var best_d := INF
		var best_j := -1
		for j in n:
			if matched[j] == 0:
				var d := a[i].distance_squared_to(b[j])
				if d < best_d:
					best_d = d
					best_j = j
		matched[best_j] = 1
		var w := 1.0 - float(weight_i) / float(n)
		total += w * sqrt(best_d)
		weight_i += 1
		i = (i + 1) % n
		if i == start:
			break
	return total
