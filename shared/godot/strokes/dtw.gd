extends RefCounted
## Dynamic Time Warping with a Sakoe-Chiba band on (position + unit tangent) features.
## Returns the accumulated cost normalized by (n + m), so values are comparable across lengths.


static func tangents(pts: PackedVector2Array) -> PackedVector2Array:
	var out := PackedVector2Array()
	var n := pts.size()
	out.resize(n)
	for i in n:
		var a := pts[maxi(i - 1, 0)]
		var b := pts[mini(i + 1, n - 1)]
		var d := b - a
		out[i] = d.normalized() if d.length_squared() > 1e-12 else Vector2.ZERO
	return out


static func distance(a: PackedVector2Array, b: PackedVector2Array, band_frac: float = 0.1, tangent_w: float = 0.5) -> float:
	var n := a.size()
	var m := b.size()
	if n == 0 or m == 0:
		return INF
	var ta := tangents(a)
	var tb := tangents(b)
	var w := maxi(int(ceil(band_frac * maxf(n, m))), absi(n - m) + 1)
	var prev := PackedFloat64Array()
	var cur := PackedFloat64Array()
	prev.resize(m + 1)
	cur.resize(m + 1)
	prev.fill(INF)
	prev[0] = 0.0
	for i in range(1, n + 1):
		cur.fill(INF)
		var center := int(round(float(i) * m / n))
		var j0 := maxi(1, center - w)
		var j1 := mini(m, center + w)
		for j in range(j0, j1 + 1):
			var cost := a[i - 1].distance_to(b[j - 1]) + tangent_w * ta[i - 1].distance_to(tb[j - 1])
			cur[j] = cost + minf(prev[j], minf(cur[j - 1], prev[j - 1]))
		var tmp := prev
		prev = cur
		cur = tmp
	return prev[m] / float(n + m)
