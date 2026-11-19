extends RefCounted
## GameCore attention glance (workflow character-attention-glance): turns world-life pings
## (KIT.ping when something leaps, lands or flies past) into a head-turn for one character, with a
## glance-and-rest rhythm so ambient life never pins the character's gaze.
## Each frame call update(delta, head_transform, forward); then apply `look * weight` (yaw, pitch in
## radians, head-local) to the character's neck/head bones however the rig needs. `born` changes
## when a new ping is picked up (blink, raise brows). Do not edit the vendored copy.
const KIT := preload("world_life_kit.gd")
const VERSION := "0.1.0"

var reach := 32.0            # metres
var max_yaw := .55
var max_pitch := .38
var glance_seconds := 2.6    # look this long, then
var rest_seconds := 3.5      # rest this long before the next glance
var weak := .5               # pings weaker than this only count within `near` metres
var near := 6.0
var weight := 0.0
var look := Vector2.ZERO
var born := -1.0
var attending := 0.0
var resting := 0.0
var glances := 0

## head: the head's global transform (its -Z or +Z facing does not matter; yaw is measured in its
## basis). forward: the body's facing on the ground plane. available: false while busy (cutscene,
## talking to someone).
func update(delta: float, head: Transform3D, forward: Vector3, available := true) -> void:
    resting=maxf(0,resting-delta)
    var ping: Dictionary={}
    if available and resting<=0:
        ping=KIT.best_ping(head.origin,forward,reach)
        if not ping.is_empty() and float(ping.strength)<weak and head.origin.distance_to(ping.at)>near:ping={}
    attending=attending+delta if not ping.is_empty() else 0.0
    if attending>glance_seconds:attending=0.0;resting=rest_seconds;ping={}
    var target := 0.0
    if not ping.is_empty():
        target=1.0
        var local: Vector3=head.affine_inverse()*Vector3(ping.at)
        var flat := Vector2(local.x,local.z).length()
        var wanted := Vector2(clampf(atan2(local.x,absf(local.z)+.3),-max_yaw,max_yaw),-clampf(atan2(local.y,flat+.3),-max_pitch,max_pitch))
        look=look.lerp(wanted,1-exp(-delta*6))
        if float(ping.born)!=born:born=float(ping.born);glances+=1
    weight=lerpf(weight,target,1-exp(-delta*(5.0 if target>0 else 2.0)))

func offset() -> Vector2:
    return look*weight
