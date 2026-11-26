## Engine-specific Godot 4 loader for arcore_procgen bake bundles.
## Loads terrain.glb, meshes.glb, instances.json, and manifest.json into a Node3D
## hierarchy with per-cell MultiMeshInstance3D batches.
## Presentation (shaders, materials, fog, water, audio, external hero props) stays consumer-owned.
class_name ProcgenWorldLoader
extends RefCounted

const INSTANCES_SCHEMA := "arcore.procgen.instances.v1"
const MANIFEST_SCHEMA := "arcore.procgen.bake-manifest.v1"

## Key in `layer_materials` / `layer_settings` that applies to layers without their own entry.
const ANY_LAYER := "*"
## Suffix of a library mesh's lower-detail twin (arcore_procgen `LOD_SUFFIX`).
const LOD_SUFFIX := "__lod"

## Floats per instance in a MultiMesh buffer: a 3x4 transform, then optional custom data.
const _TRANSFORM_FLOATS := 12
const _CUSTOM_FLOATS := 4


## Load a baked bundle directory into `parent`.
## `options` keys (all optional):
##   - terrain_material: Material. Terrain meshes carry baked ambient occlusion as
##     vertex color (`COLOR.r`, 1 = open); the material decides whether to use it.
##   - terrain_cast_shadow: bool (default true)
##   - create_terrain_collision: bool (default true). One StaticBody3D for the world.
##   - terrain_collision_layer: int (default 1)
##   - layer_materials: Dictionary { layer_id: Material }; key "*" is the fallback.
##   - layer_settings: Dictionary { layer_id: Dictionary }; key "*" is the fallback. Per layer:
##       cast_shadow: bool (default true)
##       visibility_range_end: float meters (default 0 = always drawn)
##       visibility_range_fade: float meters of fade-out before the end (default 0)
##       extra_cull_margin: float meters, for shaders that move vertices (default 0)
##   - instance_custom_data: bool (default false). Fills INSTANCE_CUSTOM with four
##     deterministic random values in [0, 1) per instance (tint, phase, etc.).
##   - lod_distance: float meters (default 0 = off). Bundles baked with extra mesh detail
##     also carry each mesh's recipe-level twin ("<id>__lod"). With a distance set, a cell
##     draws the detailed mesh only while it is nearer than this, and the twin beyond.
##     A layer's settings may override it with their own `lod_distance`.
##   - external_meshes: Dictionary { mesh_id: Mesh }
##   - external_prop_scenes: Dictionary { mesh_id: PackedScene }
##   - prop_material: Material for props built from the bundle's mesh library.
## Returns a Dictionary with { ok, root, manifest, stats, layers, errors }, where
## `layers` is { layer_id: { mesh, instances, batches } } for the layers that loaded.
static func load_bundle(parent: Node3D, bundle_dir: String, options: Dictionary = {}) -> Dictionary:
	var errors: Array[String] = []
	var manifest := _read_json(bundle_dir.path_join("manifest.json"), errors)
	var instances_doc := _read_json(bundle_dir.path_join("instances.json"), errors)
	if not errors.is_empty():
		return _failure(manifest, errors)

	if str(manifest.get("schema", "")) != MANIFEST_SCHEMA:
		errors.append("Unexpected manifest schema: %s" % str(manifest.get("schema", "")))
	if str(instances_doc.get("schema", "")) != INSTANCES_SCHEMA:
		errors.append("Unexpected instances schema: %s" % str(instances_doc.get("schema", "")))
	if not errors.is_empty():
		return _failure(manifest, errors)

	var recipe_name := str(manifest.get("recipe", {}).get("name", "procgen_world"))
	var root := Node3D.new()
	root.name = "ProcgenWorld_%s" % recipe_name
	parent.add_child(root)

	var library_meshes := _extract_mesh_library(bundle_dir.path_join("meshes.glb"), errors)
	var external_meshes: Dictionary = options.get("external_meshes", {})
	for key in external_meshes.keys():
		library_meshes[str(key)] = external_meshes[key]

	var terrain_cells := _load_terrain(root, bundle_dir.path_join("terrain.glb"), options, errors)
	var layers := _load_scatter(root, instances_doc.get("layers", []), library_meshes, options, errors)
	var props_placed := _load_props(root, instances_doc.get("props", []), library_meshes, options)

	var multimesh_batches := 0
	var instance_total := 0
	for info in layers.values():
		multimesh_batches += int(info["batches"])
		instance_total += int(info["instances"])

	return {
		"ok": errors.is_empty(),
		"root": root,
		"manifest": manifest,
		"stats": {
			"terrain_cells": terrain_cells,
			"multimesh_batches": multimesh_batches,
			"instances": instance_total,
			"props": props_placed,
		},
		"layers": layers,
		"errors": errors,
	}


static func _failure(manifest: Dictionary, errors: Array[String]) -> Dictionary:
	return {"ok": false, "root": null, "manifest": manifest, "stats": {}, "layers": {}, "errors": errors}


## Adds `Terrain` (one MeshInstance3D per cell) and returns the cell count.
static func _load_terrain(root: Node3D, path: String, options: Dictionary, errors: Array[String]) -> int:
	var terrain_node := _load_glb(path, errors)
	if terrain_node == null:
		return 0
	terrain_node.name = "Terrain"
	root.add_child(terrain_node)

	var terrain_mat: Material = options.get("terrain_material", null)
	var shadow_mode := _shadow_mode(bool(options.get("terrain_cast_shadow", true)))
	var body: StaticBody3D = null
	if bool(options.get("create_terrain_collision", true)):
		body = StaticBody3D.new()
		body.name = "TerrainCollision"
		body.collision_layer = int(options.get("terrain_collision_layer", 1))
		terrain_node.add_child(body)

	var cells := 0
	for child in terrain_node.get_children():
		var cell := child as MeshInstance3D
		if cell == null or cell.mesh == null:
			continue
		cells += 1
		cell.cast_shadow = shadow_mode
		if terrain_mat != null:
			cell.material_override = terrain_mat
		if body != null:
			var shape := CollisionShape3D.new()
			shape.name = cell.name
			shape.shape = cell.mesh.create_trimesh_shape()
			shape.transform = cell.transform
			body.add_child(shape)
	return cells


## Adds `Scatter/<layer>/cell_<x>_<z>` MultiMesh batches and returns per-layer info.
static func _load_scatter(
	root: Node3D, layer_docs: Array, library_meshes: Dictionary, options: Dictionary, errors: Array[String]
) -> Dictionary:
	var scatter_root := Node3D.new()
	scatter_root.name = "Scatter"
	root.add_child(scatter_root)

	var layer_materials: Dictionary = options.get("layer_materials", {})
	var layer_settings: Dictionary = options.get("layer_settings", {})
	var use_custom := bool(options.get("instance_custom_data", false))
	var layers: Dictionary = {}
	for layer in layer_docs:
		var layer_id := str(layer.get("layer", "layer"))
		var mesh_id := str(layer.get("mesh", ""))
		var mesh: Mesh = library_meshes.get(mesh_id, null)
		if mesh == null:
			errors.append("Missing mesh '%s' for scatter layer '%s'" % [mesh_id, layer_id])
			continue
		var layer_node := Node3D.new()
		layer_node.name = layer_id
		scatter_root.add_child(layer_node)
		var mat: Material = layer_materials.get(layer_id, layer_materials.get(ANY_LAYER, null))
		var settings: Dictionary = layer_settings.get(layer_id, layer_settings.get(ANY_LAYER, {}))
		var shadow_mode := _shadow_mode(bool(settings.get("cast_shadow", true)))
		var range_end := float(settings.get("visibility_range_end", 0.0))
		var range_fade := float(settings.get("visibility_range_fade", 0.0))
		var cull_margin := float(settings.get("extra_cull_margin", 0.0))
		var lod_mesh: Mesh = library_meshes.get(mesh_id + LOD_SUFFIX, null)
		var lod_distance := float(settings.get("lod_distance", options.get("lod_distance", 0.0)))
		if range_end > 0.0 and lod_distance >= range_end:
			lod_mesh = null  # the whole layer is inside the detailed range

		var batches := 0
		var instance_count := 0
		for cell_entry in layer.get("cells", []):
			var cell_coords: Array = cell_entry.get("cell", [0, 0])
			var items: Array = cell_entry.get("instances", [])
			if items.is_empty():
				continue
			var cell_name := "cell_%d_%d" % [int(cell_coords[0]), int(cell_coords[1])]
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.use_custom_data = use_custom
			mm.mesh = mesh
			mm.instance_count = items.size()
			mm.buffer = _instance_buffer(items, hash("%s/%s" % [layer_id, cell_name]) if use_custom else -1)

			var mmi := MultiMeshInstance3D.new()
			mmi.name = cell_name
			mmi.multimesh = mm
			mmi.cast_shadow = shadow_mode
			mmi.extra_cull_margin = cull_margin
			if range_end > 0.0:
				mmi.visibility_range_end = range_end
				if range_fade > 0.0:
					mmi.visibility_range_end_margin = range_fade
					mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
			if mat != null:
				mmi.material_override = mat
			var far: MultiMeshInstance3D = null
			if lod_mesh != null and lod_distance > 0.0:
				# Detailed mesh near the camera, its recipe-level twin from there on out.
				# (Ranges are final before the nodes enter the tree, so tools that read
				# them on arrival, such as quality presets, see the right values.)
				var far_mm := mm.duplicate() as MultiMesh
				far_mm.mesh = lod_mesh
				far = mmi.duplicate() as MultiMeshInstance3D
				far.name = cell_name + "_far"
				far.multimesh = far_mm
				far.visibility_range_begin = lod_distance
				mmi.visibility_range_end = lod_distance
			layer_node.add_child(mmi)
			batches += 1
			instance_count += items.size()
			if far != null:
				layer_node.add_child(far)
				batches += 1
		layers[layer_id] = {"mesh": mesh_id, "instances": instance_count, "batches": batches}
	return layers


## Adds `Props` and returns how many props (meshes, scenes or anchors) were placed.
static func _load_props(root: Node3D, prop_docs: Array, library_meshes: Dictionary, options: Dictionary) -> int:
	var props_root := Node3D.new()
	props_root.name = "Props"
	root.add_child(props_root)
	var prop_scenes: Dictionary = options.get("external_prop_scenes", {})
	var prop_material: Material = options.get("prop_material", null)
	var placed := 0
	for prop in prop_docs:
		var mesh_id := str(prop.get("mesh", ""))
		var node: Node3D = null
		if prop_scenes.get(mesh_id) is PackedScene:
			var inst := (prop_scenes[mesh_id] as PackedScene).instantiate()
			node = inst as Node3D
			if node == null:
				inst.free()
		elif library_meshes.has(mesh_id):
			var mi := MeshInstance3D.new()
			mi.mesh = library_meshes[mesh_id]
			if prop_material != null:
				mi.material_override = prop_material
			node = mi
		if node == null:
			# Unbound external mesh: leave an anchor the consumer can decorate or replace.
			node = Marker3D.new()
		# Every prop records what it stands for, so consumers can style or replace it.
		node.set_meta("procgen_mesh_id", mesh_id)
		node.set_meta("procgen_external", bool(prop.get("external", false)))
		node.name = str(prop.get("id", "prop"))
		node.transform = _to_transform(prop.get("instance", {}))
		props_root.add_child(node)
		placed += 1
	return placed


## Packs instance transforms (and, when `custom_seed >= 0`, four random custom
## floats each) into the flat layout `MultiMesh.buffer` expects, so a batch is
## uploaded in one call instead of one call per instance.
static func _instance_buffer(items: Array, custom_seed: int) -> PackedFloat32Array:
	var with_custom := custom_seed >= 0
	var stride := _TRANSFORM_FLOATS + (_CUSTOM_FLOATS if with_custom else 0)
	var buffer := PackedFloat32Array()
	buffer.resize(items.size() * stride)
	var rng := RandomNumberGenerator.new()
	rng.seed = maxi(custom_seed, 0)
	var o := 0
	for item in items:
		var t := _to_transform(item)
		var b := t.basis
		buffer[o] = b.x.x
		buffer[o + 1] = b.y.x
		buffer[o + 2] = b.z.x
		buffer[o + 3] = t.origin.x
		buffer[o + 4] = b.x.y
		buffer[o + 5] = b.y.y
		buffer[o + 6] = b.z.y
		buffer[o + 7] = t.origin.y
		buffer[o + 8] = b.x.z
		buffer[o + 9] = b.y.z
		buffer[o + 10] = b.z.z
		buffer[o + 11] = t.origin.z
		if with_custom:
			buffer[o + 12] = rng.randf()
			buffer[o + 13] = rng.randf()
			buffer[o + 14] = rng.randf()
			buffer[o + 15] = rng.randf()
		o += stride
	return buffer


static func _shadow_mode(cast: bool) -> GeometryInstance3D.ShadowCastingSetting:
	return GeometryInstance3D.SHADOW_CASTING_SETTING_ON if cast else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


static func _to_transform(entry: Dictionary) -> Transform3D:
	var p: Array = entry.get("position", [0.0, 0.0, 0.0])
	var r: Array = entry.get("rotation", [0.0, 0.0, 0.0, 1.0])
	var s := float(entry.get("scale", 1.0))
	var q := Quaternion(float(r[0]), float(r[1]), float(r[2]), float(r[3])).normalized()
	var basis := Basis(q).scaled(Vector3.ONE * s)
	return Transform3D(basis, Vector3(float(p[0]), float(p[1]), float(p[2])))


static func _read_json(path: String, errors: Array[String]) -> Dictionary:
	if not FileAccess.file_exists(path):
		errors.append("Missing file: %s" % path)
		return {}
	var text := FileAccess.get_file_as_string(path)
	var parsed = JSON.parse_string(text)
	if parsed is Dictionary:
		return parsed
	errors.append("Invalid JSON object: %s" % path)
	return {}


static func _load_glb(path: String, errors: Array[String]) -> Node3D:
	if not FileAccess.file_exists(path):
		errors.append("Missing GLB: %s" % path)
		return null
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_file(path, state)
	if err != OK:
		errors.append("Failed to parse GLB %s (err=%d)" % [path, err])
		return null
	var scene := doc.generate_scene(state)
	return scene as Node3D


static func _extract_mesh_library(path: String, errors: Array[String]) -> Dictionary:
	var meshes: Dictionary = {}
	var root := _load_glb(path, errors)
	if root == null:
		return meshes
	for child in root.get_children():
		if child is MeshInstance3D and child.mesh != null:
			meshes[str(child.name)] = child.mesh
	root.free()
	return meshes
