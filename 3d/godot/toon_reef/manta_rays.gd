extends MultiMeshInstance3D
## A few gentle manta rays gliding on wide laps, drawn as one MultiMesh and
## animated in `shaders/toon_manta.gdshader`. `populate()` takes a ground-height
## callback so each lap is lifted clear of the terrain it passes over.

const Atmosphere := preload("underwater_atmosphere.gd")
## Must match `uw_lap_radius` / `uw_lap_offset` in shaders/underwater.gdshaderinc.
const LAP_RADIUS_RANGE := Vector2(0.55, 1.15)
const LAP_DEPTH := 0.7
const ROUTE_SAMPLES := 20

@export var count: int = 4
@export var orbit_radius: float = 16.0
## Meters kept between a lap and the highest ground beneath it.
@export var clearance: float = 5.0


## `area` is the XZ rectangle laps may be centered in, `ceiling` the highest
## allowed swim height, and `ground_height` a `func(x, z) -> float`.
func populate(area: Rect2, ceiling: float, ground_height: Callable, seed_value: int = 1) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var transforms: Array[Transform3D] = []
	var customs: Array[Color] = []
	var bounds := AABB()
	for _attempt in count * 12:
		if transforms.size() >= count:
			break
		var pick := rng.randf()
		var radius := orbit_radius * lerpf(LAP_RADIUS_RANGE.x, LAP_RADIUS_RANGE.y, pick)
		var center := Vector2(
			rng.randf_range(area.position.x, area.end.x), rng.randf_range(area.position.y, area.end.y)
		)
		var highest := -INF
		for s in ROUTE_SAMPLES:
			var a := TAU * s / ROUTE_SAMPLES
			highest = maxf(highest, ground_height.call(center.x + cos(a) * radius, center.y + sin(a) * radius * LAP_DEPTH))
		var swim_y := highest + clearance
		if swim_y > ceiling:
			continue
		var origin := Vector3(center.x, swim_y, center.y)
		var half_span := rng.randf_range(1.6, 2.4)
		transforms.append(Transform3D(Basis.IDENTITY.scaled(Vector3.ONE * half_span), origin))
		customs.append(Color(rng.randf(), rng.randf(), pick, rng.randf()))
		bounds = AABB(origin, Vector3.ZERO) if transforms.size() == 1 else bounds.expand(origin)
	if transforms.is_empty():
		return

	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = _build_manta_mesh()
	mm.instance_count = transforms.size()
	for i in transforms.size():
		mm.set_instance_transform(i, transforms[i])
		mm.set_instance_custom_data(i, customs[i])
	Atmosphere.ensure_globals()
	var mat := ShaderMaterial.new()
	mat.shader = load((get_script() as Script).resource_path.get_base_dir().path_join("shaders/toon_manta.gdshader"))
	mat.set_shader_parameter("orbit_radius", orbit_radius)
	multimesh = mm
	material_override = mat
	# Moved in the vertex shader: cull against everywhere a lap can reach.
	custom_aabb = bounds.grow(orbit_radius * LAP_RADIUS_RANGE.y + 4.0)


## Diamond wing spanning x in [-1, 1], nose toward +Z, with two head lobes and a
## whip tail. Vertex color marks the back (1) and belly (0).
static func _build_manta_mesh() -> ArrayMesh:
	const SPAN_STEPS := 16
	const CHORD_STEPS := 6
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for side in [1.0, -1.0]:
		st.set_color(Color.WHITE if side > 0.0 else Color.BLACK)
		for i in SPAN_STEPS:
			for j in CHORD_STEPS:
				# Corners in clockwise order seen from above (x right, z toward the tail down-screen).
				var a := _wing_point(i, j + 1, SPAN_STEPS, CHORD_STEPS, side)
				var b := _wing_point(i + 1, j + 1, SPAN_STEPS, CHORD_STEPS, side)
				var c := _wing_point(i + 1, j, SPAN_STEPS, CHORD_STEPS, side)
				var d := _wing_point(i, j, SPAN_STEPS, CHORD_STEPS, side)
				for v: Vector3 in ([a, b, c, a, c, d] if side > 0.0 else [a, c, b, a, d, c]):
					st.add_vertex(v)
	st.set_color(Color.WHITE)
	for v in [Vector3(-0.035, 0.0, -0.42), Vector3(0.035, 0.0, -0.42), Vector3(0.0, 0.0, -1.55)]:
		st.add_vertex(v)
	st.index()
	st.generate_normals()
	return st.commit()


static func _wing_point(i: int, j: int, span_steps: int, chord_steps: int, side: float) -> Vector3:
	var x := lerpf(-1.0, 1.0, float(i) / span_steps)
	var reach := absf(x)
	var along := float(j) / chord_steps
	var lobe := 0.18 * maxf(0.0, 1.0 - absf(reach - 0.13) / 0.07)
	var front := 0.55 * (1.0 - pow(reach, 1.6)) - 0.12 * reach + lobe
	var back := -0.45 * pow(1.0 - reach, 0.9) - 0.12 * reach
	var thickness := 0.11 * pow(1.0 - reach, 1.3) * pow(sin(PI * along), 0.7)
	return Vector3(x, thickness * (1.0 if side > 0.0 else -0.6), lerpf(front, back, along))
