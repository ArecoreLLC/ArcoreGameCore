extends RefCounted
## Geometry helpers on PackedVector2Array strokes. Pure functions.


static func path_length(pts: PackedVector2Array) -> float:
	var d := 0.0
	for i in range(1, pts.size()):
		d += pts[i].distance_to(pts[i - 1])
	return d


## Resample a polyline to n points spaced equally along its length.
static func resample(pts: PackedVector2Array, n: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	if pts.is_empty() or n <= 0:
		return out
	if n == 1:
		return PackedVector2Array([pts[0]])
	var total := path_length(pts)
	if pts.size() == 1 or total < 1e-9:
		for i in n:
			out.append(pts[0])
		return out
	var step := total / float(n - 1)
	out.append(pts[0])
	var acc := 0.0
	var prev := pts[0]
	var i := 1
	while i < pts.size() and out.size() < n - 1:
		var cur := pts[i]
		var seg := prev.distance_to(cur)
		if seg > 0.0 and acc + seg >= step:
			var t := (step - acc) / seg
			var q := prev.lerp(cur, t)
			out.append(q)
			prev = q
			acc = 0.0
		else:
			acc += seg
			prev = cur
			i += 1
	while out.size() < n:
		out.append(pts[pts.size() - 1])
	return out


## Drop points closer than min_dist to the last kept point (first and last always kept).
## Removes digitizer jitter that piles up where the pen moves slowly (touchdown, lift, corners),
## which would otherwise distort arc-length resampling.
static func decimate(pts: PackedVector2Array, min_dist: float) -> PackedVector2Array:
	if pts.size() <= 2:
		return pts
	var out := PackedVector2Array([pts[0]])
	for i in range(1, pts.size() - 1):
		if pts[i].distance_to(out[out.size() - 1]) >= min_dist:
			out.append(pts[i])
	var last := pts[pts.size() - 1]
	if out.size() > 1 and last.distance_to(out[out.size() - 1]) < min_dist * 0.5:
		out[out.size() - 1] = last
	else:
		out.append(last)
	return out


## Resample a multi-stroke shape to ~n points total, allocated by stroke length
## (every stroke keeps at least 2 points; dots stay represented).
static func resample_strokes(strokes: Array, n: int) -> Array:
	var lengths: Array[float] = []
	var total := 0.0
	for s: PackedVector2Array in strokes:
		var l := path_length(s)
		lengths.append(l)
		total += l
	var out: Array = []
	var k := strokes.size()
	var budget := maxi(n - 2 * k, 0)
	for idx in k:
		var share := 0 if total <= 1e-9 else int(round(budget * lengths[idx] / total))
		out.append(resample(strokes[idx], 2 + share))
	return out


static func flatten(strokes: Array) -> PackedVector2Array:
	var out := PackedVector2Array()
	for s: PackedVector2Array in strokes:
		out.append_array(s)
	return out


static func bbox(strokes: Array) -> Rect2:
	var first := true
	var r := Rect2()
	for s: PackedVector2Array in strokes:
		for p in s:
			if first:
				r = Rect2(p, Vector2.ZERO)
				first = false
			else:
				r = r.expand(p)
	return r


static func centroid(pts: PackedVector2Array) -> Vector2:
	if pts.is_empty():
		return Vector2.ZERO
	var c := Vector2.ZERO
	for p in pts:
		c += p
	return c / float(pts.size())


## Translate the (resampled) centroid to the origin and scale uniformly so the larger
## bounding-box side is 1. Aspect ratio is preserved: shape proportions are retained.
static func normalize_strokes(strokes: Array, n_points: int) -> Array:
	var rs := resample_strokes(strokes, n_points)
	var c := centroid(flatten(rs))
	var box := bbox(rs)
	var s := maxf(box.size.x, box.size.y)
	if s < 1e-9:
		s = 1.0
	var out: Array = []
	for st: PackedVector2Array in rs:
		var o := PackedVector2Array()
		for p in st:
			o.append((p - c) / s)
		out.append(o)
	return out


## Apply the same normalization to raw strokes without resampling them jointly.
static func normalize_like(strokes: Array, reference_n: int) -> Dictionary:
	var rs := resample_strokes(strokes, reference_n)
	var c := centroid(flatten(rs))
	var box := bbox(rs)
	var s := maxf(maxf(box.size.x, box.size.y), 1e-9)
	return {"center": c, "scale": s}


static func transform_strokes(strokes: Array, center: Vector2, scale: float) -> Array:
	var out: Array = []
	for st: PackedVector2Array in strokes:
		var o := PackedVector2Array()
		for p in st:
			o.append((p - center) / scale)
		out.append(o)
	return out


static func flip_x(strokes: Array) -> Array:
	var out: Array = []
	for st: PackedVector2Array in strokes:
		var o := PackedVector2Array()
		for p in st:
			o.append(Vector2(-p.x, p.y))
		out.append(o)
	return out


static func reversed(pts: PackedVector2Array) -> PackedVector2Array:
	var o := PackedVector2Array()
	for i in range(pts.size() - 1, -1, -1):
		o.append(pts[i])
	return o
