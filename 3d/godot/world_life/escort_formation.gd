extends Node
## GameCore escort formation (workflow vehicle-escort-formation): followers (dolphins, small ships,
## birds) hold loose slots around a moving leader (a ship, a cart), join from behind when the
## leader gets under way, and peel away when it stops. Positions are set directly from the leader's
## frame every frame, so there is no lag or physics.
## Set `leader`, `followers` and `slots` (leader-local, +Z forward), then set `active` from game
## state (for example ship speed > 2.5 m/s). Do not edit the vendored copy.
const KIT := preload("world_life_kit.gd")
const VERSION := "0.1.0"

@export var leader: Node3D
@export var followers: Array[Node3D]=[]
@export var slots: Array[Vector3]=[]
@export var join_seconds := 3.0
@export var leave_seconds := 4.0
@export var join_from := Vector3(4,0,-16)    # added to each slot (x mirrored by slot side) at the start of a join
@export var leave_to := Vector3(12,0,6)
@export var wander := Vector2(.7,1.5)        # side and fore-aft drift (metres)
@export var height := 0.0                    # y relative to the surface
var active := false
var blend := 0.0                             # 0 away … 1 in formation
var yaw_override := INF                      # use the leader's travel yaw instead of its basis (vehicles that roll)
var surface := Callable()                    # (Vector3) -> float, sea surface; default 0
var allowed := Callable()                    # (Vector3) -> bool, false hides a follower (over land)

func frame() -> Transform3D:
    var origin: Vector3=leader.get_global_transform_interpolated().origin
    var yaw: float=yaw_override if yaw_override!=INF else leader.global_rotation.y
    return Transform3D(Basis(Vector3.UP,yaw),Vector3(origin.x,0,origin.z))

## Snap into formation now (scripted shots).
func arrive_now() -> void:
    active=true;blend=1.0

func _process(delta: float) -> void:
    if not leader:return
    var dt := minf(delta,.1)
    blend=move_toward(blend,1.0 if active else 0.0,dt/(join_seconds if active else leave_seconds))
    var f := frame()
    var t: float=KIT.time
    for i in range(followers.size()):
        var node: Node3D=followers[i]
        if i>=slots.size():node.visible=false;continue
        var slot: Vector3=slots[i]+Vector3(sin(t*.37+i*1.9)*wander.x,0,sin(t*.29+i*2.3)*wander.y)
        var side := signf(slots[i].x+.001)
        var away: Vector3=slot+(Vector3(join_from.x*side,join_from.y,join_from.z) if active else Vector3(leave_to.x*side,leave_to.y,leave_to.z))
        var at: Vector3=f*away.lerp(slot,smoothstep(0,1,blend))
        var ok: bool=blend>.01 and (not allowed.is_valid() or bool(allowed.call(at)))
        node.visible=ok
        if not ok:continue
        var y: float=(float(surface.call(at)) if surface.is_valid() else 0.0)+height
        var prev: Vector3=node.global_position
        node.global_position=Vector3(at.x,y,at.z)
        var v: Vector3=node.global_position-prev
        if v.length_squared()>.00001:node.rotation.y=lerp_angle(node.rotation.y,atan2(v.x,v.z),1-exp(-dt*6))
