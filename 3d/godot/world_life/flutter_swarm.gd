extends RefCounted
## Fixed-size spawn once / update in place. No private scenes, species or world coordinates.
const VERSION := "1.0.0"
const KIT := preload("world_life_kit.gd")
const MOTION := preload("flutter_motion.gd")

static func spawn(parent: Node3D, scene: PackedScene, amount: int, rng: RandomNumberGenerator, paint := Callable(), min_scale := .8, max_scale := 1.1, visibility_range := 50.0) -> Array[Node3D]:
    var nodes: Array[Node3D]=[]
    if scene==null or amount<0:return nodes
    for i in range(amount):
        var instance := scene.instantiate()
        if not instance is Node3D:
            instance.free();push_error("Flutter swarm requires a Node3D scene");break
        var node := instance as Node3D
        parent.add_child(node);KIT.quiet(node,visibility_range)
        node.scale=Vector3.ONE*rng.randf_range(min_scale,max_scale)
        nodes.append(node)
        if paint.is_valid():paint.call(node,i)
    return nodes

static func update(nodes: Array, center: Vector3, phase: float, time: float, visible: bool, spread := 1.0) -> void:
    for i in range(nodes.size()):
        var node: Node3D=nodes[i]
        node.visible=visible
        if not visible:continue
        var ph := phase+i*1.37
        var point := MOTION.swarm_position(center,time,ph,spread)
        var velocity := point-node.global_position
        node.global_position=point
        if velocity.length_squared()>.00001:node.rotation.y=atan2(velocity.x,velocity.z)
        KIT.flap(node,time+ph,1.0,20.0)
