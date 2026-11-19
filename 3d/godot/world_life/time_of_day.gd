extends Node3D
## GameCore time of day (workflow time-of-day-toggle): Day, Dusk and Night as a player toggle and a
## scripted mode. Eases the sun's energy, colour and angle, the sky and ambient light, raises a moon
## and a star dome, adds faint moonlight, and publishes KIT.night (0..1) for lanterns, fireflies and
## glowing sea life. Set `sun` and `environment` (or leave them to be found under `world`).
## Do not edit the vendored copy.
const KIT := preload("world_life_kit.gd")
const VERSION := "0.1.0"
const MODES := ["Day","Dusk","Night"]
const TARGET := [0.0,.55,1.0]
signal mode_changed(mode: int)

@export var world: Node
@export var sun: DirectionalLight3D
@export var environment: Environment
@export var toggle_key: Key=KEY_NONE      # e.g. KEY_F5; KEY_NONE disables the key
@export var ease_per_second := .25
@export var moon_direction := Vector3(deg_to_rad(28),deg_to_rad(150),0)   # euler, like a light's rotation
var mode := 0
var amount := 0.0
var day := {}
var stars: MeshInstance3D
var star_mat: ShaderMaterial
var moon: MeshInstance3D
var moon_mat: StandardMaterial3D
var moon_light: DirectionalLight3D

func _ready() -> void:
    if world and not sun:
        for c in world.get_children():
            if c is DirectionalLight3D:sun=c;break
    if world and not environment:
        for c in world.get_children():
            if c is WorldEnvironment:environment=c.environment;break
    if sun:day.sun_energy=sun.light_energy;day.sun_color=sun.light_color;day.sun_rot=sun.rotation_degrees
    if environment:day.bg=environment.background_energy_multiplier;day.ambient=environment.ambient_light_energy;day.ambient_color=environment.ambient_light_color
    var sphere := SphereMesh.new();sphere.radius=900;sphere.height=1800;sphere.radial_segments=32;sphere.rings=16
    star_mat=ShaderMaterial.new()
    star_mat.shader=KIT.shader("gc_stars","""shader_type spatial;
render_mode unshaded,cull_front,depth_draw_never,fog_disabled;
uniform float amount=0.0;
float hash(vec3 p){p=fract(p*0.3183099+0.1);p*=17.0;return fract(p.x*p.y*p.z*(p.x+p.y+p.z));}
void fragment(){
    vec3 d=normalize((INV_VIEW_MATRIX*vec4(VERTEX,0.0)).xyz);
    float h=hash(floor(d*260.0));
    float star=step(0.9965,h)*smoothstep(0.02,0.25,d.y);
    float twinkle=0.6+0.4*sin(TIME*3.0+h*80.0);
    ALBEDO=vec3(0.92,0.95,1.0)*star*twinkle;
    ALPHA=star*amount*twinkle;
}""")
    star_mat.render_priority=-10
    stars=MeshInstance3D.new();stars.mesh=sphere;stars.material_override=star_mat;stars.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(stars);stars.visible=false
    var disk := SphereMesh.new();disk.radius=14;disk.height=28
    moon_mat=StandardMaterial3D.new();moon_mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;moon_mat.albedo_color=Color(.97,.97,.9,0)
    moon_mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;moon_mat.disable_fog=true
    moon=MeshInstance3D.new();moon.mesh=disk;moon.material_override=moon_mat;moon.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(moon);moon.visible=false
    moon_light=DirectionalLight3D.new();moon_light.light_color=Color("9fb8ff");moon_light.light_energy=0;moon_light.rotation=Vector3(-moon_direction.x,moon_direction.y,0);add_child(moon_light)

func cycle() -> void:
    set_mode((mode+1)%MODES.size())

func set_mode(value: int, instant := false) -> void:
    mode=clampi(value,0,MODES.size()-1)
    if instant:amount=TARGET[mode]
    mode_changed.emit(mode)

func _unhandled_input(event: InputEvent) -> void:
    if toggle_key!=KEY_NONE and event is InputEventKey and event.pressed and not event.echo and event.keycode==toggle_key:cycle()

func _process(delta: float) -> void:
    amount=move_toward(amount,TARGET[mode],delta*ease_per_second)
    KIT.night=amount
    var cam := get_viewport().get_camera_3d()
    var show := amount>.01
    stars.visible=show;moon.visible=show
    if cam:
        stars.global_position=cam.global_position
        moon.global_position=cam.global_position+Basis.from_euler(moon_direction)*Vector3.FORWARD*700
    star_mat.set_shader_parameter("amount",smoothstep(.35,1.0,amount))
    moon_mat.albedo_color.a=smoothstep(.15,.8,amount)
    moon_light.light_energy=smoothstep(.5,1.0,amount)*.32
    if sun and day.has("sun_energy"):
        var dusk := sin(clampf(amount/.55,0,1)*PI*.5)*(1.0-smoothstep(.55,1.0,amount))
        sun.light_energy=lerpf(day.sun_energy,.05,smoothstep(.3,1.0,amount))
        sun.light_color=day.sun_color.lerp(Color("ff9a5a"),dusk*.8)
        sun.rotation_degrees=day.sun_rot.lerp(Vector3(-8,day.sun_rot.y-25,0),clampf(amount/.55,0,1))
    if environment and day.has("bg"):
        environment.background_energy_multiplier=lerpf(day.bg,.06,smoothstep(.2,1.0,amount))
        environment.ambient_light_energy=lerpf(day.ambient,.18,amount)
        environment.ambient_light_color=day.ambient_color.lerp(Color("5a6fa8"),amount)
