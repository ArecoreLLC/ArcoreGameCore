extends RefCounted
## Committed-turn counters, independent of action eligibility and game rules.

static func remaining(counters: Dictionary, key: Variant) -> int:
	return int(counters.get(key, 0))

## Tick existing counters first, then arm supplied durations without ticking them.
## Call only after acceptance. Inputs are unchanged; nonpositive counters expire.
static func committed(counters: Dictionary, armed: Dictionary = {}) -> Dictionary:
	var next: Dictionary = {}
	for key in counters:
		var left := int(counters[key]) - 1
		if left > 0:
			next[key] = left
	for key in armed:
		var duration := int(armed[key])
		if duration > 0:
			next[key] = duration
	return next
