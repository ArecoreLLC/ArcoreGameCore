# API — 0.1.0

Load scripts with preload relative to your caller. None declares class_name.

| Script | Operations |
| --- | --- |
| ink_stroke.gd | new(), add(seconds, Vector2, pressure=-1, tilt=ZERO), size(), duration(), length(), has_real_pressure(), repair_timestamps(); points/times/pressures/tilts packed arrays |
| ink_geom.gd | path_length, resample, decimate, resample_strokes, flatten, bbox, centroid, normalize_strokes, normalize_like, transform_strokes, flip_x, reversed |
| pdollar.gd | cloud(stroke_polylines, count), distance(cloud_a, cloud_b) |
| dtw.gd | tangents(points), distance(a, b, band_frac=0.1, tangent_w=0.5) |
| sample_math.gd | smooth(times, values, window_seconds), median(values) |
| motion.gd | sparc(speed, sample_hz, cutoff_hz, amplitude_threshold, max_bins), _time_resample(stroke, hz), _moving_average(points, window_samples), _dwell_time(points, hz, radius, minimum_seconds) |

Motion helper names retain their original underscore spelling; they are available
for callers in this version. The math accepts finite numeric samples, matching
parallel-array lengths, nondecreasing times, positive sampling rates, and valid
positive scale/window/spectral parameters. Time resampling requires at least two
samples. Validate untrusted recordings with the replay codec before applying math.
These primitives do not automatically repair or change sample timestamps.

Coordinates are arbitrary consistent units; timestamps are seconds. Pressure -1
means unavailable. add() preserves legacy replacement of nonfinite pressure with
-1; other invalid live input is the caller's responsibility. Analog-pressure
presence detection and timestamp-repair heuristics retain legacy thresholds.

Resample returns empty for nonpositive budgets/empty input, first point for budget
one, and repeated points for zero-length paths. Multi-stroke allocation remains
approximate, with at least two samples per nonempty stroke. Empty clouds return
empty; empty distances return INF. Cloud distance retains legacy min-length
comparison for unequal clouds; callers should normalize to equal sizes.
SPARC returns 0 for fewer than four samples. No scores, tiers, or pass/fail gates
are calculated here.
