extends Node3D
## GameCore splash pool (workflow sea-leap-and-splash): pooled water splashes (a droplet spray, a
## widening ring and an optional positional sound) for anything that leaps out of or falls into
## water. Nothing is allocated after _ready. Pair it with sea_breach.gd arcs. Do not edit the
## vendored copy.
const KIT := preload("world_life_kit.gd")
const VERSION := "0.1.0"

@export var pool_size := 10
@export var sound: AudioStream            # optional splash sound (otherwise a synthesised one)
@export var view_range := 110.0
var entries: Array[Dictionary]=[]
var next := 0
var spawned := 0

func _ready() -> void:
    if not sound:sound=KIT.tone([180.0,240.0,330.0],.5,7.0,.25,.8)
    var drop_mat := StandardMaterial3D.new();drop_mat.albedo_color=Color(.95,.99,1,.95);drop_mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
    drop_mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;drop_mat.vertex_color_use_as_albedo=true;drop_mat.render_priority=2
    var drop := SphereMesh.new();drop.radius=.11;drop.height=.22;drop.radial_segments=6;drop.rings=3;drop.material=drop_mat
    var fade := Gradient.new();fade.set_color(0,Color(1,1,1,1));fade.set_color(1,Color(1,1,1,0))
    var shrink := Curve.new();shrink.add_point(Vector2(0,1));shrink.add_point(Vector2(1,.35))
    for i in range(pool_size):
        var holder := Node3D.new();add_child(holder)
        var spray := CPUParticles3D.new();holder.add_child(spray)
        spray.emitting=false;spray.one_shot=true;spray.explosiveness=.92;spray.amount=28;spray.lifetime=1.0
        spray.mesh=drop;spray.direction=Vector3.UP;spray.spread=32;spray.gravity=Vector3(0,-9.8,0)
        spray.color_ramp=fade;spray.scale_amount_curve=shrink;spray.emission_shape=CPUParticles3D.EMISSION_SHAPE_SPHERE;spray.emission_sphere_radius=.25
        spray.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;spray.visibility_range_end=view_range
        var ring := MeshInstance3D.new();holder.add_child(ring)
        var torus := TorusMesh.new();torus.inner_radius=.9;torus.outer_radius=1;torus.rings=32;torus.ring_segments=6;ring.mesh=torus
        var ring_mat := StandardMaterial3D.new();ring_mat.albedo_color=Color(.92,.98,1,0);ring_mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
        ring_mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;ring_mat.render_priority=2;ring.material_override=ring_mat
        ring.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;ring.visible=false;ring.visibility_range_end=view_range
        entries.append({"holder":holder,"spray":spray,"ring":ring,"mat":ring_mat,"age":9.0,"size":1.0})

## A splash at a point on the water: size 1 for a dolphin re-entry, about .4 for a small fish.
func spawn(at: Vector3, size := 1.0, with_sound := true) -> void:
    var e: Dictionary=entries[next];next=(next+1)%pool_size;spawned+=1
    var holder: Node3D=e.holder;holder.global_position=at
    var spray: CPUParticles3D=e.spray
    spray.scale_amount_min=.6*size;spray.scale_amount_max=1.1*size
    spray.initial_velocity_min=1.6+1.4*size;spray.initial_velocity_max=2.4+2.6*size
    spray.restart();spray.emitting=true
    e.age=0.0;e.size=size;(e.ring as MeshInstance3D).visible=true
    if with_sound:KIT.play_at(self,sound,at,-9.0+6.0*log(maxf(size,.2))/log(2.0),clampf(1.25-.25*size,.85,1.6))
    KIT.ping(at,clampf(size,.3,1.2),2.0)

func _process(delta: float) -> void:
    for e in entries:
        if float(e.age)>=1.2:continue
        e.age=float(e.age)+delta
        var u := clampf(float(e.age)/1.1,0,1)
        var r: float=(.4+2.0*u)*float(e.size)
        (e.ring as MeshInstance3D).scale=Vector3(r,.25,r)
        (e.mat as StandardMaterial3D).albedo_color.a=.8*(1.0-u)
        if u>=1:(e.ring as MeshInstance3D).visible=false
