extends RefCounted
## Distant stand-in for a baked arcore_procgen world, built from that bake's
## `preview.json` (schema `arcore.procgen.preview.v1`: a coarse grid of top and
## underside heights). It is one mesh of a few thousand triangles, so a scene
## can show a neighboring or far-away world without loading its bundle: the
## land above a cloud deck, islands overhead, the shore around a lake.
##
##   const ProcgenPreview := preload("res://addons/gamecore_procgen/procgen_preview.gd")
##   var land := ProcgenPreview.build("res://worlds/overland", {"offset": Vector3(0, -120, 0)})
##   if land != null:
##       add_child(land)
##
## Presentation stays with the consumer: pass `material` (the mesh has smooth
## normals and no vertex colors or UVs); without one a plain matte grey is used.

const SCHEMA := "arcore.procgen.preview.v1"


## Returns a MeshInstance3D (not yet in the tree), or null when the bundle has
## no usable preview or nothing survives `clip_below`. `options` (all optional):
##   pivot: Vector2      world XZ of the previewed world that lands on `offset`
##   offset: Vector3     where `pivot`, at height `y_origin`, ends up in this scene
##   y_origin: float     previewed height mapped to offset.y (default 0)
##   scale_xz, scale_y: float   horizontal / vertical stretch (default 1)
##   clip_below: float   drop triangles whose corners all sit below this previewed height
##   undersides: bool    also draw the bottoms of floating land (default true)
##   material: Material  material_override for the mesh
static func build(bundle_dir: String, options: Dictionary = {}) -> MeshInstance3D:
	var doc := read(bundle_dir)
	if doc.is_empty():
		return null
	var n := int(doc.resolution)
	var origin := Vector2(float(doc.origin[0]), float(doc.origin[1]))
	var size := Vector2(float(doc.size[0]), float(doc.size[1]))
	var top: Array = doc.top
	var bottom: Array = doc.bottom
	var pivot: Vector2 = options.get("pivot", Vector2.ZERO)
	var offset: Vector3 = options.get("offset", Vector3.ZERO)
	var y0 := float(options.get("y_origin", 0.0))
	var sxz := float(options.get("scale_xz", 1.0))
	var sy := float(options.get("scale_y", 1.0))
	var clip: Variant = options.get("clip_below")
	var undersides := bool(options.get("undersides", true))

	var point := func(i: int, j: int, h: float) -> Vector3:
		var x := origin.x + size.x * i / (n - 1)
		var z := origin.y + size.y * j / (n - 1)
		return offset + Vector3((x - pivot.x) * sxz, (h - y0) * sy, (z - pivot.y) * sxz)

	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Each grid cell is two triangles; a triangle is drawn when all three of its
	# corners are land, so coastlines and island rims follow the diagonal too.
	var corners := [[0, 0], [1, 0], [0, 1], [1, 1]]
	for j in n - 1:
		for i in n - 1:
			for tri in [[0, 1, 2], [1, 3, 2]]:
				var tops: Array[Vector3] = []
				var unders: Array[Vector3] = []
				var highest := -INF
				for k in tri:
					var ci: int = i + corners[k][0]
					var cj: int = j + corners[k][1]
					var h: Variant = top[cj * n + ci]
					if h == null:
						break
					highest = maxf(highest, float(h))
					tops.append(point.call(ci, cj, float(h)))
					var u: Variant = bottom[cj * n + ci]
					if u != null:
						unders.append(point.call(ci, cj, float(u)))
				if tops.size() < 3 or (clip != null and highest < float(clip)):
					continue
				for v in tops:
					st.add_vertex(v)
				if undersides and unders.size() == 3:
					for v in [unders[0], unders[2], unders[1]]:
						st.add_vertex(v)
	st.generate_normals()
	var mesh := st.commit()
	if mesh.get_surface_count() == 0:
		return null
	var node := MeshInstance3D.new()
	node.name = "Preview_%s" % bundle_dir.get_file()
	node.mesh = mesh
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material: Material = options.get("material")
	if material == null:
		var matte := StandardMaterial3D.new()
		matte.albedo_color = Color(0.62, 0.64, 0.66)
		matte.roughness = 1.0
		material = matte
	node.material_override = material
	return node


## The parsed preview document of a bundle, or {} if it is missing or malformed.
static func read(bundle_dir: String) -> Dictionary:
	var path := bundle_dir.path_join("preview.json")
	if not FileAccess.file_exists(path):
		push_warning("No preview at %s (rebake the world with arcore_procgen 0.2.0 or later)" % path)
		return {}
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not (doc is Dictionary) or str(doc.get("schema", "")) != SCHEMA or int(doc.get("resolution", 0)) < 2:
		push_warning("Unexpected preview document: %s" % path)
		return {}
	return doc
