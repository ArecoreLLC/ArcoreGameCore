extends MultiMeshInstance3D
## Schools of cartoon reef fish drawn as a single MultiMesh and animated entirely
## in `shaders/toon_fish.gdshader` (no per-frame script work). Call `populate()` with
## the world-space centers the schools should circle.

const Atmosphere := preload("underwater_atmosphere.gd")

@export var fish_per_school: int = 36
@export var orbit_radius: float = 7.0
@export var orbit_height: float = 2.4


func populate(centers: Array[Vector3], seed_value: int = 1) -> void:
	if centers.is_empty():
		return
	Atmosphere.ensure_globals()
	var mat := ShaderMaterial.new()
	mat.shader = load((get_script() as Script).resource_path.get_base_dir().path_join("shaders/toon_fish.gdshader"))
	mat.set_shader_parameter("orbit_radius", orbit_radius)
	mat.set_shader_parameter("orbit_height", orbit_height)

	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = _build_fish_mesh()
	mm.instance_count = centers.size() * fish_per_school
	var bounds := AABB(centers[0], Vector3.ZERO)
	var i := 0
	for center in centers:
		bounds = bounds.expand(center)
		# One species (palette pick) per school, with the odd visitor.
		var species := rng.randf()
		for _n in fish_per_school:
			var size := rng.randf_range(0.7, 1.25)
			mm.set_instance_transform(i, Transform3D(Basis.IDENTITY.scaled(Vector3.ONE * size), center))
			var pick := species if rng.randf() > 0.12 else rng.randf()
			mm.set_instance_custom_data(i, Color(rng.randf(), pick, rng.randf(), rng.randf()))
			i += 1
	multimesh = mm
	material_override = mat
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# Fish are moved in the vertex shader, so cull against the area they can reach.
	custom_aabb = bounds.grow(orbit_radius * 1.3 + 2.0)
	visibility_range_end = 110.0


## A plump +Z-facing fish: squashed sphere body, forked tail and a dorsal fin.
static func _build_fish_mesh() -> ArrayMesh:
	var body := SphereMesh.new()
	body.radius = 0.5
	body.height = 1.0
	body.radial_segments = 10
	body.rings = 6
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.append_from(body, 0, Transform3D(Basis.IDENTITY.scaled(Vector3(0.26, 0.42, 0.86)), Vector3.ZERO))
	# Fins are flat, double-sided triangles in the YZ plane.
	var fins: Array[PackedVector3Array] = [
		PackedVector3Array([Vector3(0, 0.0, -0.34), Vector3(0, 0.30, -0.78), Vector3(0, 0.02, -0.60)]),
		PackedVector3Array([Vector3(0, 0.0, -0.34), Vector3(0, -0.02, -0.60), Vector3(0, -0.30, -0.78)]),
		PackedVector3Array([Vector3(0, 0.17, 0.14), Vector3(0, 0.36, -0.12), Vector3(0, 0.16, -0.22)]),
	]
	for fin in fins:
		st.set_normal(Vector3.RIGHT)
		for v in fin:
			st.add_vertex(v)
	return st.commit()
