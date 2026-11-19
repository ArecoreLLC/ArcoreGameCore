extends Node3D
## GameCore celebration burst (workflow arrival-celebration): confetti cannons that fire a short
## salute (three volleys by default) with a synthesised boom, for an arrival, a docking or a
## finished task. Place it, call add_cannon(position, direction) once per cannon, then fire().
## Do not edit the vendored copy.
const KIT := preload("world_life_kit.gd")
const VERSION := "0.1.0"
signal volley(index: int)

@export var colors: Array[Color]=[Color("ff5c8a"),Color("ffd23f"),Color("4fc3f7"),Color("8bd650"),Color("b36bff"),Color.WHITE]
@export var volleys := 3
@export var interval := .9
@export var boom_db := -4.0
@export var with_barrels := true
var emitters: Array[CPUParticles3D]=[]
var queue: Array[float]=[]
var fired := 0
var boom: AudioStreamWAV

func _ready() -> void:
    boom=KIT.tone([60.0,90.0],.9,5.0,.75,.6)

func add_cannon(at: Vector3, direction: Vector3) -> void:
    direction=direction.normalized()
    if with_barrels:
        var barrel := KIT.merge([[KIT.cyl_mesh(.16,.2,10),KIT.xf(Vector3(0,.35,.2),Vector3(1,.9,1),Vector3(-1.0,0,0)),colors[0]],
            [KIT.cyl_mesh(.18,.18,10),KIT.xf(Vector3(0,.55,.55),Vector3(1,.08,1),Vector3(-1.0,0,0)),colors[1]],
            [KIT.cyl_mesh(.22,.22,10),KIT.xf(Vector3(0,.2,0),Vector3(1,.12,1),Vector3(0,0,PI*.5)),Color("8a5a3a")]])
        var c := KIT.instance(self,barrel,KIT.vcol(.4),Vector3.ZERO,90,true);c.global_position=at;c.rotation.y=atan2(direction.x,direction.z)
    var p := CPUParticles3D.new();add_child(p);p.global_position=at+Vector3(0,.7,0)+direction*.6
    var q := QuadMesh.new();q.size=Vector2(.12,.08);var m := StandardMaterial3D.new();m.vertex_color_use_as_albedo=true;m.cull_mode=BaseMaterial3D.CULL_DISABLED
    m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;m.render_priority=2;q.material=m
    p.mesh=q;p.amount=90;p.lifetime=3.0;p.one_shot=true;p.explosiveness=.95;p.direction=(direction+Vector3.UP*1.6).normalized();p.spread=22
    p.initial_velocity_min=7;p.initial_velocity_max=11;p.gravity=Vector3(0,-3.5,0);p.damping_min=1.5;p.damping_max=2.5
    p.angular_velocity_min=-400;p.angular_velocity_max=400;p.particle_flag_rotate_y=true
    var g := Gradient.new();var offsets := PackedFloat32Array();var cols := PackedColorArray()
    for i in range(colors.size()):offsets.append(float(i)/maxf(1,colors.size()-1));cols.append(colors[i])
    g.offsets=offsets;g.colors=cols;p.color_initial_ramp=g
    p.emitting=false;p.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;p.visibility_range_end=120
    emitters.append(p)

func fire() -> void:
    var t: float=KIT.time
    queue.clear()
    for i in range(volleys):queue.append(t+i*interval)
    fired+=1

func _process(_delta: float) -> void:
    var n := 0
    while queue.size()>0 and queue[0]<=KIT.time:
        queue.pop_front()
        for p in emitters:
            p.restart();p.emitting=true
            KIT.play_at(self,boom,p.global_position,boom_db,randf_range(.9,1.1))
        if emitters.size()>0:KIT.ping(emitters[0].global_position+Vector3(0,3,0),1.0,2.0)
        volley.emit(n);n+=1
