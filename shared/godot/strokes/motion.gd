extends RefCounted
const StrokeData = preload("ink_stroke.gd")

## Spectral arc length of a speed profile.
## fc: max cutoff (Hz); amp_th: adaptive cutoff where the normalized magnitude drops below it.
## The DFT is evaluated only on [0, fc], with a zero-padded resolution capped at max_bins.
static func sparc(speed: PackedFloat32Array, fs: float, fc: float, amp_th: float, max_bins: int) -> float:
	var n := speed.size()
	if n < 4:
		return 0.0
	var nfft := 1
	while nfft < n:
		nfft *= 2
	# zero-pad up to 16Ã— for resolution, but keep the [0, fc] band within max_bins
	var pad := 16
	while pad > 1 and fc / fs * nfft * pad > max_bins:
		pad /= 2
	nfft *= pad
	var bins := mini(int(floor(fc / fs * nfft)) + 1, nfft / 2)
	var mag := PackedFloat32Array()
	mag.resize(bins)
	var peak := 0.0
	for k in bins:
		# Goertzel evaluates the same DFT bin with two recurrence states, avoiding
		# the complex phasor rotation and accumulation for every input sample.
		var coefficient := 2.0 * cos(TAU * float(k) / float(nfft))
		var previous := 0.0
		var previous2 := 0.0
		for i in n:
			var current := float(speed[i]) + coefficient * previous - previous2
			previous2 = previous
			previous = current
		var m := sqrt(maxf(0.0, previous * previous + previous2 * previous2 - coefficient * previous * previous2))
		mag[k] = m
		peak = maxf(peak, m)
	if peak <= 0.0:
		return 0.0
	var first := -1
	var last := -1
	for k in bins:
		mag[k] /= peak
		if mag[k] >= amp_th:
			if first < 0:
				first = k
			last = k
	if first < 0 or last <= first:
		return 0.0
	var df := fs / float(nfft)
	var span := float(last - first) * df
	var arc := 0.0
	for k in range(first + 1, last + 1):
		var dx := df / span
		var dy := mag[k] - mag[k - 1]
		arc += sqrt(dx * dx + dy * dy)
	return -arc


## Time spent dwelling: windows of `min_s` during which the pen stays within `radius` of
## where the window started. Displacement-based, so digitizer jitter cannot break a pause up.
## Dwells touching the stroke's start or end are natural acceleration/deceleration: excluded.
static func _dwell_time(pos: PackedVector2Array, hz: float, radius: float, min_s: float) -> float:
	var n := pos.size()
	var w := maxi(2, int(round(min_s * hz)))
	if n < w + 2:
		return 0.0
	var flagged := PackedByteArray()
	flagged.resize(n)
	flagged.fill(0)
	for i in range(0, n - w + 1):
		var a := pos[i]
		var still := true
		for j in range(i + 1, i + w):
			if pos[j].distance_to(a) > radius:
				still = false
				break
		if still:
			for j in range(i, i + w):
				flagged[j] = 1
	var total := 0
	var i := 0
	while i < n:
		if flagged[i] == 0:
			i += 1
			continue
		var j := i
		while j < n and flagged[j] == 1:
			j += 1
		if i > 0 and j < n:
			total += j - i
		i = j
	return total / hz


static func _time_resample(s: StrokeData, hz: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	var t0 := s.times[0]
	var t1 := s.times[s.size() - 1]
	var n := int(floor((t1 - t0) * hz)) + 1
	var k := 0
	for i in n:
		var t := t0 + float(i) / hz
		while k < s.size() - 2 and s.times[k + 1] < t:
			k += 1
		var ta := s.times[k]
		var tb := s.times[k + 1]
		var f := 0.0 if tb <= ta else clampf((t - ta) / (tb - ta), 0.0, 1.0)
		out.append(s.points[k].lerp(s.points[k + 1], f))
	return out


static func _moving_average(pts: PackedVector2Array, w: int) -> PackedVector2Array:
	if w <= 1:
		return pts
	var half := w / 2
	var out := PackedVector2Array()
	out.resize(pts.size())
	for i in pts.size():
		var a := maxi(0, i - half)
		var b := mini(pts.size() - 1, i + half)
		var acc := Vector2.ZERO
		for j in range(a, b + 1):
			acc += pts[j]
		out[i] = acc / float(b - a + 1)
	return out
