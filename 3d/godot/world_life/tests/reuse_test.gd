extends SceneTree
const MOTION := preload("res://addons/gamecore_world_life/flutter_motion.gd")
const SWARM := preload("res://addons/gamecore_world_life/flutter_swarm.gd")
const PATTERNS := preload("res://addons/gamecore_world_life/wing_patterns.gd")
const TRACK := preload("res://addons/gamecore_world_life/timed_stroke_track.gd")
var failures: Array[String]=[]
var checks := 0
func check(ok: bool,label: String):
    checks+=1
    if not ok:failures.append(label);push_error(label)
func _initialize():call_deferred("run")
func run():
    var center := Vector3(10,2,-5)
    for i in range(120):
        var t := i*.137
        var ph := i*.43
        var expected := center+Vector3(sin(t*.7+ph)*2.2+sin(t*1.9+ph*2)*.6,1.0+sin(t*1.3+ph)*.6+.4*sin(t*3.1+ph),cos(t*.6+ph)*2.2+cos(t*2.3+ph)*.5)
        check(MOTION.swarm_position(center,t,ph).distance_to(expected)<.000001,"swarm trajectory parity")
        var orbit := center+Vector3(cos(t*.8)*.65+sin(t*1.9)*.10,sin(t*1.5)*.12+sin(t*3.1)*.03,sin(t*.8)*.39+cos(t*1.3)*.08)
        check(MOTION.orbit_position(center,t).distance_to(orbit)<.000001,"local orbit parity")
    var start := Vector3(3,3,2);var perch := Vector3(0,1,0);var end := Vector3(-3,4,0)
    check(MOTION.visit_position(start,perch,end,0)==start,"visit starts correctly")
    check(MOTION.visit_position(start,perch,end,2.2)==perch,"arrives at perch")
    check(MOTION.visit_position(start,perch,end,4)==perch,"holds moving perch")
    check(MOTION.visit_position(start,perch,end,7.5)==end,"finishes departure")
    check(is_equal_approx(MOTION.burst_amplitude(5,false),.65),"steady buzz")
    check(TRACK.valid([[0,0,0],[.5,1,1]]),"valid ordered track")
    check(not TRACK.valid([[1,0,0],[0,1,1]]),"reject unordered track")
    check(not TRACK.valid([[0,NAN,0]]),"reject nonfinite track")
    check(TRACK.sample([],0)==null,"empty track")
    check(TRACK.sample([[0,0,0],[.5,1,1]],.25)==Vector2(.5,.5),"interpolate stroke")
    check(TRACK.sample([[0,0,0],[2,1,1]],1)==Vector2.ZERO,"hold across pen-up gap")
    check(TRACK.sample([[1,.2,.3]],1)==Vector2(.2,.3),"single point")
    check(TRACK.sample([[1,.2,.3]],1.2)==null,"outside grace")
    var data := PATTERNS.read_catalog("res://species.json")
    check(data.size()==2 and is_equal_approx(data[1].base.a,.18),"JSON catalog and transparent alpha")
    var parent := Node3D.new();root.add_child(parent)
    var source := Node3D.new()
    for label in ["WingL","WingR","Body"]:
        var part := MeshInstance3D.new();part.name=label;part.mesh=BoxMesh.new();source.add_child(part);part.owner=source
    var scene := PackedScene.new();scene.pack(source);source.free()
    var rng := RandomNumberGenerator.new();rng.seed=2311
    var nodes := SWARM.spawn(parent,scene,6,rng,func(node,index):PATTERNS.paint(node,data[index%2]))
    check(nodes.size()==6 and parent.get_child_count()==6,"fixed spawn count")
    check(nodes[0].get_node("WingL").material_override is ShaderMaterial,"pattern material applied")
    var identities := nodes.map(func(n):return n.get_instance_id())
    SWARM.update(nodes,center,1.0,4.0,true)
    check(nodes[0].global_position.distance_to(MOTION.swarm_position(center,4.0,1.0))<.000001,"pool uses shared trajectory")
    SWARM.update(nodes,center,1.0,5.0,false)
    check(not nodes[0].visible and nodes.map(func(n):return n.get_instance_id())==identities,"hide without respawn")
    parent.queue_free();await process_frame
    print("REUSABLE_WORLD_LIFE ","PASS" if failures.is_empty() else "FAIL"," checks=",checks)
    quit(0 if failures.is_empty() else 1)
