extends SceneTree
## Asset-free second-game adapter. Launch through video_lighting_studio.
var environment: Environment
var sun: DirectionalLight3D
var fill: SpotLight3D
var amount := 0.0
func _initialize() -> void:call_deferred("_start")
func _start() -> void:
    var world=Node3D.new();root.add_child(world)
    environment=Environment.new()
    environment.background_mode=Environment.BG_COLOR
    environment.background_color=Color("768ba7")
    environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
    environment.ambient_light_color=Color("b2c6e5")
    var env=WorldEnvironment.new();env.environment=environment;world.add_child(env)
    sun=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-35,-40,0);sun.shadow_enabled=true;world.add_child(sun)
    var camera=Camera3D.new();world.add_child(camera);camera.position=Vector3(0,1.8,4);camera.look_at(Vector3(0,.9,0));camera.current=true
    var subject=MeshInstance3D.new();subject.mesh=SphereMesh.new();subject.position=Vector3(0,1,0);world.add_child(subject)
    var material=StandardMaterial3D.new();material.albedo_color=Color("5989bd");material.roughness=.8;subject.material_override=material
    var floor_mesh=MeshInstance3D.new();var plane=PlaneMesh.new();plane.size=Vector2(20,20);floor_mesh.mesh=plane;world.add_child(floor_mesh)
    var core=OS.get_environment("GAMECORE_ROOT")
    fill=load(core.path_join("3d/godot/music_video/capture_fill.gd")).new();world.add_child(fill);fill.configure([subject])
    var studio=load(core.path_join("3d/godot/music_video/lighting_studio.gd")).new();world.add_child(studio)
    studio.configure(OS.get_environment("ARCORE_STUDIO_SESSION"),_apply,_day,func():return amount)
func _day(value: String) -> void:amount={"day":0.0,"dusk":0.55,"night":1.0}[value]
func _apply(look: Dictionary, exposure: float) -> void:
    environment.tonemap_exposure=exposure
    sun.light_energy=lerpf(1.0,.08,amount)*float(look.sunlight)
    environment.ambient_light_energy=lerpf(.45,.12,amount)*float(look.ambient)
    fill.light_energy=float(look.camera_fill)
