extends Node3D
## GameCore route gates (workflow route-boost-gates): striped gates every `spacing` metres along a
## route (peppermint wind lanes, ring courses). When the vehicle passes through one, the gate
## sparkles and `passed(index)` fires so the game can apply a speed burst (and a sound). Gates are
## only placed where `allowed(point)` is true (for example deep water at the centre and both posts).
## Call build(from, to) after setting the options. Do not edit the vendored copy.
const KIT := preload("world_life_kit.gd")
const VERSION := "0.1.0"
signal passed(index: int)

@export var spacing := 26.0
@export var margin := 50.0             # keep clear of both ends (harbours)
@export var half_width := 4.2
@export var post_height := 5.0
@export var stripe_a := Color("e8283c")
@export var stripe_b := Color("fff8f4")
@export var view_range := 180.0
var vehicle_position := Callable()     # () -> Vector3
var allowed := Callable()              # (Vector3) -> bool
var gates: Array[Dictionary]=[]
var passes := 0

func build(from: Vector3, to: Vector3) -> int:
    var dir := to-from;dir.y=0
    var length := dir.length();dir=dir.normalized()
    var side := Vector3(-dir.z,0,dir.x)
    var parts: Array=[]
    var bands := int(post_height/.5)
    for k in range(bands):parts.append([KIT.cyl_mesh(.12,.12,8),KIT.xf(Vector3(0,.25+k*.5,0),Vector3(1,.5,1)),stripe_a if k%2==0 else stripe_b])
    parts.append([KIT.sphere_mesh(8),KIT.xf(Vector3(0,post_height+.1,0),Vector3.ONE*.32),stripe_a])
    var post := KIT.merge(parts)
    var d := margin
    while d<=length-margin:
        var c := from+dir*d;c.y=0
        var ok: bool=not allowed.is_valid() or (bool(allowed.call(c)) and bool(allowed.call(c+side*half_width)) and bool(allowed.call(c-side*half_width)))
        if ok:
            var holder := Node3D.new();add_child(holder);holder.global_position=c;holder.rotation.y=atan2(dir.x,dir.z)
            for k in [-1,1]:KIT.instance(holder,post,KIT.vcol(.4),Vector3(k*half_width,-.6,0),view_range,true)
            var ribbon := MeshInstance3D.new();var q := QuadMesh.new();q.size=Vector2(half_width*2,.5);q.subdivide_width=16;ribbon.mesh=q
            ribbon.material_override=KIT.flutter_material(stripe_b,.6,stripe_a);holder.add_child(ribbon);ribbon.position=Vector3(0,post_height-.7,0)
            ribbon.visibility_range_end=view_range
            var sparkle := CPUParticles3D.new();holder.add_child(sparkle);sparkle.position=Vector3(0,post_height*.4,0)
            var sq := QuadMesh.new();sq.size=Vector2(.25,.25);var m := StandardMaterial3D.new();m.billboard_mode=BaseMaterial3D.BILLBOARD_ENABLED
            m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;m.vertex_color_use_as_albedo=true;m.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;m.render_priority=3;sq.material=m
            sparkle.mesh=sq;sparkle.amount=40;sparkle.lifetime=1.2;sparkle.one_shot=true;sparkle.explosiveness=.9;sparkle.emission_shape=CPUParticles3D.EMISSION_SHAPE_BOX
            sparkle.emission_box_extents=Vector3(half_width,2,.3);sparkle.spread=180;sparkle.initial_velocity_min=1;sparkle.initial_velocity_max=3;sparkle.gravity=Vector3.ZERO
            var g := Gradient.new();g.set_color(0,stripe_a);g.add_point(.5,Color.WHITE);g.set_color(1,Color(1,1,1,0));sparkle.color_ramp=g;sparkle.emitting=false
            gates.append({"node":holder,"center":c,"dir":dir,"side":side,"sparkle":sparkle,"cool":0.0})
        d+=spacing
    return gates.size()

func _process(delta: float) -> void:
    if not vehicle_position.is_valid():return
    var at: Vector3=vehicle_position.call()
    for i in range(gates.size()):
        var g: Dictionary=gates[i]
        g.cool=maxf(0,float(g.cool)-delta)
        var rel: Vector3=at-g.center
        if float(g.cool)<=0 and absf(rel.dot(g.dir))<2.2 and absf(rel.dot(g.side))<half_width-.2:
            g.cool=6.0;passes+=1
            var sp: CPUParticles3D=g.sparkle;sp.restart();sp.emitting=true
            KIT.ping(g.center+Vector3(0,3,0),.9,2.0)
            passed.emit(i)
