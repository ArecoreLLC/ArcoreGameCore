extends Node3D
## Owns everything between the camera and a toon reef: depth-driven fog and
## light, the shared shader globals, sun shafts, drifting marine snow and bubbles.
##
## It borrows the host scene's Environment and sun instead of owning them: the
## values it changes are captured in `configure()` and blended back whenever the
## camera leaves the water (or the optional active radius), so the same node
## works in a dedicated underwater scene and inside a larger open world.

## Emitted when the camera enters or leaves the active water volume.
signal submerged_changed(submerged: bool)

const SHADER_GLOBALS := {
	&"uw_water_level": [RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 0.0],
	&"uw_deep_color": [RenderingServer.GLOBAL_VAR_TYPE_COLOR, Color(0.05, 0.24, 0.48)],
	&"uw_caustic_strength": [RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 0.22],
	&"uw_sun_dir": [RenderingServer.GLOBAL_VAR_TYPE_VEC3, Vector3(0.35, 0.74, 0.57)],
	# Draw-distance scale for scatter fades; a quality module may own and change it.
	&"gc_range_scale": [RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 1.0],
}
## Seconds to blend between the host look and the underwater look.
const BLEND_SECONDS := 0.45

## Depth in meters at which the water reaches its deepest color.
@export var deep_depth: float = 44.0
@export var god_ray_count: int = 90
@export var snow_amount: int = 420
@export var bubble_amount: int = 110
@export var caustic_strength: float = 0.22

var water_level: float = 0.0
var water_color := Color(0.10, 0.72, 0.86)
var deep_color := Color(0.05, 0.24, 0.48)
var sun_color := Color(1.0, 0.96, 0.82)
## True while the camera is inside the active water volume.
var submerged: bool = false

static var _globals_ready: bool = false

var _environment: Environment
var _sun: DirectionalLight3D
var _host: Dictionary = {}
var _center := Vector2.ZERO
var _active_radius: float = 0.0
var _wet: float = 0.0
var _followers: Array[Node3D] = []
var _underwater_only: Array[Node3D] = []


## Registers the shader globals the reef shaders read. Safe to call repeatedly;
## must run before any toon_reef shader is loaded (materials call it for you).
static func ensure_globals() -> void:
	if _globals_ready:
		return
	_globals_ready = true
	for key: StringName in SHADER_GLOBALS:
		# A host project may already declare them under Project Settings > Shader Globals.
		# Another GameCore module may have registered a shared global already; modules
		# leave a note on Engine so nobody adds one twice.
		if not ProjectSettings.has_setting("shader_globals/%s" % key) and not Engine.has_meta("shader_global_%s" % key):
			RenderingServer.global_shader_parameter_add(key, SHADER_GLOBALS[key][0], SHADER_GLOBALS[key][1])
			Engine.set_meta("shader_global_%s" % key, true)


## `manifest` is the bake manifest; `environment` and `sun` belong to the host scene.
## `options` (all optional):
##   - origin: Vector3 world position of the bundle root (default zero)
##   - active_radius: float; underwater look only applies within this XZ distance
##     of the bundle center (default 0 = anywhere below the water level)
func configure(manifest: Dictionary, environment: Environment, sun: DirectionalLight3D, options: Dictionary = {}) -> void:
	ensure_globals()
	# Followers are repositioned every rendered frame; keep them out of physics interpolation.
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	var origin: Vector3 = options.get("origin", Vector3.ZERO)
	_active_radius = float(options.get("active_radius", 0.0))

	var pres: Dictionary = manifest.get("presentation", {})
	water_color = color_from(pres.get("water_color"), water_color)
	deep_color = color_from(pres.get("deep_color"), deep_color)
	sun_color = color_from(pres.get("sun_color"), sun_color)
	if manifest.get("water_level") != null:
		water_level = float(manifest["water_level"])
	water_level += origin.y

	_environment = environment
	_sun = sun
	_capture_host()

	var sun_dir := _sun.global_transform.basis.z.normalized() if _sun != null else Vector3(0.3, 0.9, 0.3).normalized()
	RenderingServer.global_shader_parameter_set(&"uw_water_level", water_level)
	RenderingServer.global_shader_parameter_set(&"uw_deep_color", deep_color)
	RenderingServer.global_shader_parameter_set(&"uw_caustic_strength", caustic_strength)
	RenderingServer.global_shader_parameter_set(&"uw_sun_dir", sun_dir)

	var bounds: Dictionary = manifest.get("bounds", {})
	var corner: Array = bounds.get("origin", [-96.0, -48.0, -96.0])
	var size: Array = bounds.get("size", [192.0, 56.0, 192.0])
	var area := Rect2(float(corner[0]) + origin.x, float(corner[2]) + origin.z, float(size[0]), float(size[2]))
	_center = area.get_center()
	_build_god_rays(area, sun_dir, absf(float(corner[1])))
	_build_marine_snow()
	_build_ambient_bubbles()
	for node in _underwater_only:
		node.visible = false


func _process(delta: float) -> void:
	var camera := get_viewport().get_camera_3d()
	if camera == null:
		return
	var eye := camera.global_position
	for node in _followers:
		node.global_position = eye
	var inside := _active_radius <= 0.0 or Vector2(eye.x, eye.z).distance_to(_center) < _active_radius
	var now_submerged := inside and eye.y < water_level
	if now_submerged != submerged:
		submerged = now_submerged
		for node in _underwater_only:
			node.visible = submerged
		submerged_changed.emit(submerged)
	var target := 1.0 if submerged else 0.0
	if _wet == target and not submerged:
		return
	_wet = move_toward(_wet, target, delta / BLEND_SECONDS)
	_apply(clampf((water_level - eye.y) / deep_depth, 0.0, 1.0))


## Remember the host's values for everything this node animates.
func _capture_host() -> void:
	if _environment != null:
		for property in [
			"fog_enabled", "fog_mode", "fog_light_color", "fog_density", "fog_depth_begin", "fog_depth_end",
			"fog_depth_curve", "fog_sky_affect", "ambient_light_color", "ambient_light_energy",
		]:
			_host[property] = _environment.get(property)
	if _sun != null:
		_host["sun_energy"] = _sun.light_energy
		_host["sun_color"] = _sun.light_color


## Blend between the host look (`_wet` = 0) and the underwater look for `depth01`
## (0 = just under the surface, 1 = deep).
func _apply(depth01: float) -> void:
	if _sun != null:
		_sun.light_energy = lerpf(_host["sun_energy"], float(_host["sun_energy"]) * lerpf(1.1, 0.78, depth01), _wet)
		_sun.light_color = (_host["sun_color"] as Color).lerp(sun_color, _wet)
	if _environment == null:
		return
	if _wet <= 0.0:
		for property in _host:
			if not property.begins_with("sun_"):
				_environment.set(property, _host[property])
		return
	# Depth fog fades in from nothing, so a fog-free host scene blends cleanly.
	var host_fog: bool = _host["fog_enabled"] and _host["fog_mode"] == Environment.FOG_MODE_DEPTH
	_environment.fog_enabled = true
	_environment.fog_mode = Environment.FOG_MODE_DEPTH
	_environment.fog_light_color = water_color.lerp(deep_color, depth01 * 0.8)
	_environment.fog_density = lerpf(float(_host["fog_density"]) if host_fog else 0.0, 1.0, _wet)
	_environment.fog_depth_begin = lerpf(24.0, 12.0, depth01)
	_environment.fog_depth_end = lerpf(135.0, 95.0, depth01)
	_environment.fog_depth_curve = 1.35
	_environment.fog_sky_affect = _wet
	_environment.ambient_light_color = (_host["ambient_light_color"] as Color).lerp(
		water_color.lerp(deep_color, depth01 * 0.6).lightened(0.35), _wet
	)
	_environment.ambient_light_energy = lerpf(_host["ambient_light_energy"], lerpf(0.62, 0.42, depth01), _wet)


## One MultiMesh of camera-facing shafts hanging from the surface across the world.
func _build_god_rays(area: Rect2, sun_dir: Vector3, water_depth: float) -> void:
	var quad := QuadMesh.new()
	var mat := ShaderMaterial.new()
	mat.shader = _shader("toon_god_ray.gdshader")
	mat.set_shader_parameter("ray_color", sun_color.lerp(water_color, 0.25))
	mat.set_shader_parameter("base_length", clampf(water_depth * 0.75, 12.0, 60.0))
	quad.material = mat

	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = quad
	mm.instance_count = god_ray_count
	for i in god_ray_count:
		var pos := Vector3(
			rng.randf_range(area.position.x, area.end.x), water_level, rng.randf_range(area.position.y, area.end.y)
		)
		mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, pos))
		mm.set_instance_custom_data(i, Color(rng.randf(), rng.randf(), rng.randf(), rng.randf()))

	var rays := MultiMeshInstance3D.new()
	rays.name = "GodRays"
	rays.multimesh = mm
	rays.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# The shader stretches each quad far below its anchor; cover the whole water column.
	var slant := Vector3(sun_dir.x, 0.0, sun_dir.z) * 80.0
	rays.custom_aabb = AABB(
		Vector3(area.position.x, water_level - water_depth, area.position.y) - slant.abs(),
		Vector3(area.size.x, water_depth, area.size.y) + slant.abs() * 2.0
	)
	add_child(rays)
	_underwater_only.append(rays)


## Tiny drifting specks around the camera give the water volume and a sense of speed.
func _build_marine_snow() -> void:
	var pmat := ParticleProcessMaterial.new()
	pmat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pmat.emission_box_extents = Vector3(22.0, 12.0, 22.0)
	pmat.direction = Vector3(0.2, -1.0, 0.1)
	pmat.spread = 60.0
	pmat.initial_velocity_min = 0.05
	pmat.initial_velocity_max = 0.35
	pmat.gravity = Vector3(0.12, -0.04, 0.05)
	pmat.scale_min = 0.5
	pmat.scale_max = 1.6
	pmat.turbulence_enabled = true
	pmat.turbulence_noise_strength = 0.4
	pmat.turbulence_noise_scale = 3.0

	var speck := QuadMesh.new()
	speck.size = Vector2(0.05, 0.05)
	var smat := StandardMaterial3D.new()
	smat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	smat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	smat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	smat.albedo_color = Color(0.92, 1.0, 0.98, 0.42)
	smat.disable_receive_shadows = true
	speck.material = smat

	var snow := _make_particles("MarineSnow", snow_amount, 9.0, pmat, speck)
	snow.visibility_aabb = AABB(Vector3(-26, -16, -26), Vector3(52, 32, 52))
	_followers.append(snow)
	_underwater_only.append(snow)


## Soap-film bubbles rising through the water near the camera.
func _build_ambient_bubbles() -> void:
	var pmat := ParticleProcessMaterial.new()
	pmat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pmat.emission_box_extents = Vector3(30.0, 6.0, 30.0)
	pmat.direction = Vector3(0.0, 1.0, 0.0)
	pmat.spread = 10.0
	pmat.initial_velocity_min = 0.8
	pmat.initial_velocity_max = 1.9
	pmat.gravity = Vector3(0.0, 0.18, 0.0)
	pmat.scale_min = 0.10
	pmat.scale_max = 0.30

	var sphere := SphereMesh.new()
	sphere.radius = 0.5
	sphere.height = 1.0
	sphere.radial_segments = 12
	sphere.rings = 8
	var smat := ShaderMaterial.new()
	smat.shader = _shader("toon_bubble.gdshader")
	sphere.material = smat

	# The emitter hangs below eye level so bubbles drift up through the view.
	var anchor := Node3D.new()
	anchor.name = "BubbleAnchor"
	add_child(anchor)
	var bubbles := _make_particles("AmbientBubbles", bubble_amount, 9.0, pmat, sphere, anchor)
	bubbles.position = Vector3(0.0, -10.0, 0.0)
	bubbles.visibility_aabb = AABB(Vector3(-34, -22, -34), Vector3(68, 44, 68))
	_followers.append(anchor)
	_underwater_only.append(anchor)


func _make_particles(
	node_name: String, amount: int, lifetime: float, process: ParticleProcessMaterial, mesh: Mesh, parent: Node3D = self
) -> GPUParticles3D:
	var particles := GPUParticles3D.new()
	particles.name = node_name
	particles.amount = amount
	particles.lifetime = lifetime
	particles.preprocess = lifetime
	particles.local_coords = false
	particles.process_material = process
	particles.draw_pass_1 = mesh
	particles.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(particles)
	return particles


func _shader(file_name: String) -> Shader:
	return load((get_script() as Script).resource_path.get_base_dir().path_join("shaders").path_join(file_name))


## Converts a manifest `[r, g, b]` array to a Color, or returns `fallback`.
static func color_from(value: Variant, fallback: Color) -> Color:
	if value is Array and value.size() >= 3:
		return Color(float(value[0]), float(value[1]), float(value[2]))
	return fallback
