extends MultiMeshInstance3D
## Drifting toon jellyfish. One MultiMesh holds every jelly; the bell pulse,
## slow bob and tentacle ripple all run in toon_jelly.gdshader, so they cost no
## script time. The mesh is generated here (bell dome plus ribbon tentacles).

@export var count: int = 24

const BELL_RADIUS := 0.6
const BELL_HEIGHT := 0.5
const TENTACLES := 8
const TENTACLE_LENGTH := 2.4


## Scatters `count` jellies over `area` (world XZ), between the seabed (via the
## `ground` callable `(x, z) -> y`) and `top`.
func populate(area: Rect2, top: float, ground: Callable, rng_seed: int) -> void:
	var mat := ShaderMaterial.new()
	mat.shader = load((get_script() as Script).resource_path.get_base_dir().path_join("shaders/toon_jelly.gdshader"))
	var rng := RandomNumberGenerator.new()
	rng.seed = rng_seed
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = build_mesh()
	mm.instance_count = count
	for i in count:
		var x := rng.randf_range(area.position.x, area.end.x)
		var z := rng.randf_range(area.position.y, area.end.y)
		var floor_y: float = ground.call(x, z)
		var y := rng.randf_range(minf(floor_y + 6.0, top - 4.0), top - 3.0)
		var s := rng.randf_range(0.7, 1.7)
		var basis := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * s)
		mm.set_instance_transform(i, Transform3D(basis, Vector3(x, y, z)))
		mm.set_instance_custom_data(i, Color(rng.randf(), rng.randf(), rng.randf(), rng.randf()))
	multimesh = mm
	material_override = mat
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# The shader bobs and drifts each jelly a couple of meters from its anchor.
	extra_cull_margin = 4.0


## Bell (COLOR.r = 0) and tentacles (COLOR.r = 1); UV.y runs 0 -> 1 down a tentacle.
static func build_mesh() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rings := 6
	var segments := 14
	# Dome: ring 0 is the apex, the last ring the rim (slightly flared).
	var points: Array[Vector3] = []
	for r in rings + 1:
		var t := float(r) / rings
		var angle := t * PI * 0.5
		var radius := sin(angle) * BELL_RADIUS * (1.0 + 0.12 * t * t)
		var y := cos(angle) * BELL_HEIGHT
		for s in segments:
			var a := TAU * s / segments
			points.append(Vector3(cos(a) * radius, y, sin(a) * radius))
	for r in rings:
		for s in segments:
			var i0 := r * segments + s
			var i1 := r * segments + (s + 1) % segments
			var j0 := i0 + segments
			var j1 := i1 + segments
			for idx in [i0, i1, j0, i1, j1, j0]:
				var p: Vector3 = points[idx]
				st.set_color(Color(0.0, 0.0, 0.0))
				st.set_uv(Vector2(0.0, 1.0 - p.y / BELL_HEIGHT))
				st.set_normal(p.normalized())
				st.add_vertex(p)
	# Tentacles: crossed ribbons hanging from just inside the rim.
	var steps := 6
	for k in TENTACLES:
		var a := TAU * (k + 0.5) / TENTACLES
		var root := Vector3(cos(a), 0.0, sin(a)) * BELL_RADIUS * 0.7
		var side := Vector3(-sin(a), 0.0, cos(a)) * 0.05
		for c in 2:
			var w := side if c == 0 else Vector3(cos(a), 0.0, sin(a)) * 0.05
			for i in steps:
				var t0 := float(i) / steps
				var t1 := float(i + 1) / steps
				var p0 := root + Vector3.DOWN * TENTACLE_LENGTH * t0
				var p1 := root + Vector3.DOWN * TENTACLE_LENGTH * t1
				var n := w.cross(Vector3.DOWN).normalized()
				var quad := [[p0 - w, t0], [p0 + w, t0], [p1 - w * 0.4, t1], [p0 + w, t0], [p1 + w * 0.4, t1], [p1 - w * 0.4, t1]]
				for v in quad:
					st.set_color(Color(1.0, 0.0, 0.0))
					st.set_uv(Vector2(0.0, v[1]))
					st.set_normal(n)
					st.add_vertex(v[0])
	return st.commit()
