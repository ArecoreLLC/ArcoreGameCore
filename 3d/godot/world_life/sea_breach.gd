extends RefCounted
## GameCore leap arcs (workflow ambient-world-life): porpoising cycles and single arcs for anything
## that jumps out of the sea (dolphins, fish, flying fish), plus pitch and yaw for a velocity.
## Pure math: callers own the node, the clock and the splash. Do not edit the vendored copy.

## Height of a porpoising swimmer above its cruise depth at cycle fraction `u` (0..1).
## The leap occupies the first `leap` fraction of the cycle; the rest is a gentle underwater roll.
static func porpoise_height(u: float, depth: float, height: float, leap := .42) -> float:
    u=fposmod(u,1.0)
    if u<leap:return depth+(height-depth)*sin(PI*u/leap)
    var s := (u-leap)/(1.0-leap)
    return depth-.18*sin(PI*s)

## A single arc from `from` along horizontal `direction` (unit length): position at u (0..1).
static func arc_point(from: Vector3, direction: Vector3, length: float, height: float, u: float) -> Vector3:
    u=clampf(u,0,1)
    return from+direction*length*u+Vector3.UP*height*4.0*u*(1.0-u)

## Nose pitch for a velocity, in radians: positive is nose up.
static func pitch_for(velocity: Vector3) -> float:
    var flat := Vector2(velocity.x,velocity.z).length()
    return atan2(velocity.y,maxf(flat,.001))

## Yaw that points local +Z along a horizontal velocity.
static func yaw_for(velocity: Vector3, fallback: float) -> float:
    if Vector2(velocity.x,velocity.z).length_squared()<.0004:return fallback
    return atan2(velocity.x,velocity.z)
