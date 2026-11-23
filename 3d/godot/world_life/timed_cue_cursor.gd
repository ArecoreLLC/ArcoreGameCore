extends RefCounted
## Observe the first active half-open time interval once per key, including skipped cues.
## Caller owns cooldown, text meaning and whether/what to dispatch.
const VERSION := "1.0.0"
var last_key := ""
var last_seconds := -1.0

func reset() -> void:
    last_key="";last_seconds=-1.0

func observe(track: String, seconds: float, cues: Array, rewind_tolerance := .5) -> int:
    if not is_finite(seconds) or not is_finite(rewind_tolerance) or rewind_tolerance<0:return -1
    if seconds<last_seconds-rewind_tolerance:last_key=""
    last_seconds=seconds
    for i in range(cues.size()):
        var cue = cues[i]
        if not cue is Dictionary:continue
        var start = cue.get("start")
        var end = cue.get("end")
        if not _number(start) or not _number(end) or end<=start:continue
        if seconds<start or seconds>=end:continue
        # JSON encoding avoids collisions between arbitrary track IDs and indices.
        var key := JSON.stringify([track,i])
        if key==last_key:return -1
        last_key=key
        return i
    return -1

static func _number(value: Variant) -> bool:
    return (value is float or value is int) and is_finite(float(value))
