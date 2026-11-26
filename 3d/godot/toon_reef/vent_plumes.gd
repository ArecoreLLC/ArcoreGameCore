extends Node3D
## Hydrothermal vent dressing: a rising bubble plume from every chimney mouth
## and a flickering ember light at its base. Chimneys are the bake's
## `vent_chimney` props; their mouth sits at `MOUTH_HEIGHT` in model space.

const MOUTH_HEIGHT := 6.1

var _lights: Array[OmniLight3D] = []
var _phases: Array[float] = []


func populate(vents: Array[Node3D], glow: Color) -> void:
	var bubble := SphereMesh.new()
	bubble.radius = 0.5
	bubble.height = 1.0
	bubble.radial_segments = 10
	bubble.rings = 6
	var bubble_mat := ShaderMaterial.new()
	bubble_mat.shader = load((get_script() as Script).resource_path.get_base_dir().path_join("shaders/toon_bubble.gdshader"))
	bubble.material = bubble_mat

	var i := 0
	for vent in vents:
		var mouth := vent.global_transform * Vector3(0.0, MOUTH_HEIGHT, 0.0)
		var vent_scale := vent.global_transform.basis.get_scale().y

		var pmat := ParticleProcessMaterial.new()
		pmat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
		pmat.emission_sphere_radius = 0.35 * vent_scale
		pmat.direction = Vector3.UP
		pmat.spread = 8.0
		pmat.initial_velocity_min = 2.2
		pmat.initial_velocity_max = 3.6
		pmat.gravity = Vector3(0.15, 0.6, 0.05)
		pmat.scale_min = 0.12
		pmat.scale_max = 0.38
		pmat.turbulence_enabled = true
		pmat.turbulence_noise_strength = 0.6
		pmat.turbulence_noise_scale = 2.0

		var plume := GPUParticles3D.new()
		plume.name = "Plume%d" % i
		plume.amount = 70
		plume.lifetime = 7.0
		plume.preprocess = 7.0
		plume.process_material = pmat
		plume.draw_pass_1 = bubble
		plume.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		plume.visibility_aabb = AABB(Vector3(-6, -1, -6), Vector3(12, 40, 12))
		add_child(plume)
		plume.global_position = mouth

		var light := OmniLight3D.new()
		light.name = "Ember%d" % i
		light.light_color = glow
		light.light_energy = 1.6
		light.omni_range = 11.0 * vent_scale
		light.shadow_enabled = false
		add_child(light)
		light.global_position = vent.global_position + Vector3.UP * 1.5
		_lights.append(light)
		_phases.append(float(i) * 1.7)
		i += 1


func _process(_delta: float) -> void:
	var t := Time.get_ticks_msec() / 1000.0
	for k in _lights.size():
		_lights[k].light_energy = 1.4 + 0.35 * sin(t * 5.3 + _phases[k]) + 0.2 * sin(t * 13.1 + _phases[k] * 2.0)
