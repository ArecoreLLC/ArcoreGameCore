extends RefCounted
## One-stop builder for a toon-styled reef from an arcore_procgen bake bundle.
##
##   var reef := ToonReef.build(self, ProcgenWorldLoader, "res://worlds/reef")
##   ToonReef.add_atmosphere(self, reef, world_environment.environment, sun)
##   await get_tree().physics_frame   # terrain collision must be live for ground queries
##   ToonReef.add_life(self, reef)
##
## The procgen loader script is passed in rather than preloaded, so this module
## does not care where either addon is vendored. Everything accepts an `origin`
## so the reef can sit anywhere inside a larger world.

const Materials := preload("reef_materials.gd")
const Atmosphere := preload("underwater_atmosphere.gd")
const FishSchool := preload("fish_school.gd")
const MantaRays := preload("manta_rays.gd")
const Jellyfish := preload("jellyfish.gd")
const VentPlumes := preload("vent_plumes.gd")

## Prop mesh ids the generator builds as timber wrecks.
const WRECK_MESH_IDS: Array[String] = ["shipwreck"]
## Prop mesh ids the generator builds as hydrothermal vent chimneys.
const VENT_MESH_IDS: Array[String] = ["vent_chimney"]
## Prop mesh ids the generator builds as carved stone ruins.
const RUIN_MESH_IDS: Array[String] = ["ruin_column"]


## Loads `bundle_dir` under `parent` with `loader` (the ProcgenWorldLoader script)
## and applies the toon materials. `options` (all optional):
##   - origin: Vector3 world position for the bundle root (default zero)
##   - any ProcgenWorldLoader option, e.g. `external_prop_scenes`,
##     `create_terrain_collision`, `terrain_collision_layer`
## Returns the loader result plus `materials` (ReefMaterials) and `origin`.
static func build(parent: Node3D, loader: Script, bundle_dir: String, options: Dictionary = {}) -> Dictionary:
	var origin: Vector3 = options.get("origin", Vector3.ZERO)
	# The manifest is read up front so materials exist before the loader builds batches.
	var materials := Materials.new(_read_presentation(bundle_dir.path_join("manifest.json")))
	var seabed := materials.seabed()

	var loader_options := options.duplicate()
	loader_options.erase("origin")
	loader_options["terrain_material"] = seabed
	loader_options["layer_settings"] = Materials.layer_settings()
	loader_options["instance_custom_data"] = true
	var reef: Dictionary = loader.load_bundle(parent, bundle_dir, loader_options)
	reef["materials"] = materials
	reef["origin"] = origin
	var root: Node3D = reef.get("root")
	if root == null:
		return reef
	root.position = origin

	_style_scatter(root, materials)
	_style_props(root, materials)
	var grotto := feature_zone(reef["manifest"])
	if not grotto.is_empty():
		var c: Array = grotto.get("center", [0.0, 0.0])
		seabed.set_shader_parameter("grotto_center", Vector2(float(c[0]) + origin.x, float(c[1]) + origin.z))
		seabed.set_shader_parameter("grotto_radius", float(grotto.get("radius", 24.0)))
	return reef


## Adds the UnderwaterAtmosphere for `reef`. `options` may carry `active_radius`
## (see underwater_atmosphere.gd); `origin` is filled in from the reef.
static func add_atmosphere(
	parent: Node3D, reef: Dictionary, environment: Environment, sun: DirectionalLight3D, options: Dictionary = {}
) -> Node3D:
	var atmosphere := Atmosphere.new()
	atmosphere.name = "ReefAtmosphere"
	parent.add_child(atmosphere)
	var atmosphere_options := options.duplicate()
	atmosphere_options["origin"] = reef.get("origin", Vector3.ZERO)
	atmosphere.configure(reef.get("manifest", {}), environment, sun, atmosphere_options)
	return atmosphere


## Adds fish schools and manta rays. Needs the terrain collision registered with
## physics (wait two physics frames after `build`). `options` (all optional):
##   - fish_schools: int (default 7), manta_rays: int (default 4), jellyfish: int (default 24)
## Vent chimney props (VENT_MESH_IDS) get bubble plumes and ember lights.
static func add_life(parent: Node3D, reef: Dictionary, options: Dictionary = {}) -> void:
	var manifest: Dictionary = reef.get("manifest", {})
	var origin: Vector3 = reef.get("origin", Vector3.ZERO)
	var size := bounds_size(manifest)
	var surface := water_level(reef)
	var bottom := surface - size.y
	var ground := func(x: float, z: float) -> float: return ground_height(parent, x, z, surface, bottom)

	# Schools circle open water above the non-arch zones and a few random flats.
	var spots: Array[Vector2] = []
	for z in manifest.get("zones", []):
		if not str(z.get("id", "")).begins_with("arch"):
			var c: Array = z.get("center", [0.0, 0.0])
			spots.append(Vector2(float(c[0]), float(c[1])))
	var rng := RandomNumberGenerator.new()
	rng.seed = int(manifest.get("recipe", {}).get("seed", 1))
	var half := size * 0.35
	for _i in 24:
		spots.append(Vector2(rng.randf_range(-half.x, half.x), rng.randf_range(-half.z, half.z)))
	var centers: Array[Vector3] = []
	var wanted := int(options.get("fish_schools", 7))
	for spot in spots:
		if centers.size() >= wanted:
			break
		var at := spot + Vector2(origin.x, origin.z)
		var floor_y: float = ground.call(at.x, at.y)
		# Skip mesa tops and anything too close to the surface.
		if floor_y < surface - 16.0:
			centers.append(Vector3(at.x, floor_y + rng.randf_range(4.5, 8.0), at.y))
	var school := FishSchool.new()
	school.name = "FishSchools"
	parent.add_child(school)
	school.populate(centers, rng.seed)

	var mantas := MantaRays.new()
	mantas.name = "MantaRays"
	mantas.count = int(options.get("manta_rays", 4))
	parent.add_child(mantas)
	var reach := size * 0.28
	mantas.populate(
		Rect2(origin.x - reach.x, origin.z - reach.z, reach.x * 2.0, reach.z * 2.0), surface - 4.0, ground, rng.seed + 1
	)

	var jelly_count := int(options.get("jellyfish", 24))
	if jelly_count > 0:
		var jellies := Jellyfish.new()
		jellies.name = "Jellyfish"
		jellies.count = jelly_count
		parent.add_child(jellies)
		var drift := size * 0.4
		jellies.populate(
			Rect2(origin.x - drift.x, origin.z - drift.z, drift.x * 2.0, drift.z * 2.0), surface - 2.0, ground, rng.seed + 2
		)

	var vents: Array[Node3D] = []
	var props := (reef.get("root") as Node3D).get_node_or_null("Props") if reef.get("root") != null else null
	if props != null:
		for prop in props.get_children():
			if str(prop.get_meta("procgen_mesh_id", "")) in VENT_MESH_IDS:
				vents.append(prop)
	if not vents.is_empty():
		var plumes := VentPlumes.new()
		plumes.name = "VentPlumes"
		parent.add_child(plumes)
		plumes.populate(vents, Atmosphere.color_from(manifest.get("presentation", {}).get("vent_color"), Color(1.0, 0.46, 0.2)))


## Terrain height under a world XZ point, by ray cast from `top` down to `bottom`
## (returns `bottom` when nothing is hit).
static func ground_height(node: Node3D, x: float, z: float, top: float, bottom: float) -> float:
	var query := PhysicsRayQueryParameters3D.create(Vector3(x, top, z), Vector3(x, bottom, z))
	var hit := node.get_world_3d().direct_space_state.intersect_ray(query)
	return float(hit["position"].y) if hit.has("position") else bottom


## World-space water surface height of a built reef.
static func water_level(reef: Dictionary) -> float:
	var level: Variant = reef.get("manifest", {}).get("water_level")
	return (float(level) if level != null else 0.0) + (reef.get("origin", Vector3.ZERO) as Vector3).y


static func feature_zone(manifest: Dictionary) -> Dictionary:
	for z in manifest.get("zones", []):
		if str(z.get("id", "")) in ["feature_zone", "grotto"]:
			return z
	return {}


static func bounds_size(manifest: Dictionary) -> Vector3:
	var sz: Array = manifest.get("bounds", {}).get("size", [192.0, 56.0, 192.0])
	return Vector3(float(sz[0]), float(sz[1]), float(sz[2]))


static func _read_presentation(manifest_path: String) -> Dictionary:
	if not FileAccess.file_exists(manifest_path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if parsed is Dictionary and parsed.get("presentation") is Dictionary:
		return parsed["presentation"]
	return {}


## Gives every scatter layer its material, sized from the layer mesh.
static func _style_scatter(root: Node3D, materials: Materials) -> void:
	var scatter := root.get_node_or_null("Scatter")
	if scatter == null:
		return
	for layer_node in scatter.get_children():
		var batches := layer_node.get_children()
		if batches.is_empty():
			continue
		var first := batches[0] as MultiMeshInstance3D
		if first == null or first.multimesh == null:
			continue
		var mat := materials.layer(str(layer_node.name), _mesh_height(first.multimesh.mesh))
		for batch in batches:
			(batch as GeometryInstance3D).material_override = mat


## Styles props built from the bundle's mesh library; unbound markers and
## consumer-supplied scenes are left for the consumer.
static func _style_props(root: Node3D, materials: Materials) -> void:
	var props := root.get_node_or_null("Props")
	if props == null:
		return
	for child in props.get_children():
		var prop := child as MeshInstance3D
		if prop == null or prop.material_override != null:
			continue
		var mesh_id := str(prop.get_meta("procgen_mesh_id", ""))
		if mesh_id in WRECK_MESH_IDS:
			prop.material_override = materials.wood()
		elif mesh_id in VENT_MESH_IDS:
			prop.material_override = materials.vent()
		elif mesh_id in RUIN_MESH_IDS:
			prop.material_override = materials.stone()
		else:
			prop.material_override = materials.prop(Materials.DEFAULT_CORAL_PALETTE, _mesh_height(prop.mesh))


static func _mesh_height(mesh: Mesh) -> float:
	return mesh.get_aabb().end.y if mesh != null else 1.0
