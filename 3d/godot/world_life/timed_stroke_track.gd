extends RefCounted
## Sorted [seconds, u, v] samples; independent of textures, songs and world coordinates.
const VERSION := "1.0.0"

static func valid(track: Array) -> bool:
    var previous := -INF
    for point in track:
        if not point is Array or point.size()!=3:return false
        for value in point:
            if not (value is float or value is int) or not is_finite(float(value)):return false
        if float(point[0])<previous:return false
        previous=float(point[0])
    return true

## Null outside the track. Hold the earlier point across long pen-up intervals.
## Validate once on import; sampling is O(log n), without per-frame full validation.
static func sample(track: Array, time: float, grace := .05, gap := .6) -> Variant:
    if not is_finite(time) or track.is_empty() or time<float(track[0][0])-grace or time>float(track[-1][0])+grace:return null
    var lo := 0
    var hi := track.size()-1
    while hi-lo>1:
        var mid := (lo+hi)/2
        if float(track[mid][0])<=time:lo=mid
        else:hi=mid
    var a: Array=track[lo]
    var b: Array=track[hi]
    if float(b[0])-float(a[0])>gap:return Vector2(float(a[1]),float(a[2]))
    var f := clampf((time-float(a[0]))/maxf(float(b[0])-float(a[0]),.001),0,1)
    return Vector2(lerpf(float(a[1]),float(b[1]),f),lerpf(float(a[2]),float(b[2]),f))
