extends RefCounted
## Frozen pre-extraction direct-DFT reference from game/tests/smoothness_reference.gd.
static func sparc(speed: PackedFloat32Array, fs: float, fc: float, amp_th: float, max_bins: int) -> float:
	var n := speed.size()
	if n < 4:
		return 0.0
	var nfft := 1
	while nfft < n:
		nfft *= 2
	# zero-pad up to 16× for resolution, but keep the [0, fc] band within max_bins
	var pad := 16
	while pad > 1 and fc / fs * nfft * pad > max_bins:
		pad /= 2
	nfft *= pad
	var bins := mini(int(floor(fc / fs * nfft)) + 1, nfft / 2)
	var mag := PackedFloat32Array()
	mag.resize(bins)
	var peak := 0.0
	for k in bins:
		# DFT bin k via rotating phasor (no per-sample trig)
		var w := -TAU * float(k) / float(nfft)
		var step_re := cos(w)
		var step_im := sin(w)
		var ph_re := 1.0
		var ph_im := 0.0
		var re := 0.0
		var im := 0.0
		for i in n:
			var v := speed[i]
			re += v * ph_re
			im += v * ph_im
			var nre := ph_re * step_re - ph_im * step_im
			ph_im = ph_re * step_im + ph_im * step_re
			ph_re = nre
		var m := sqrt(re * re + im * im)
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
