## Engine-specific Godot 4 loader for arcore_procgen bake bundles.
## Loads terrain.glb, meshes.glb, instances.json, and manifest.json into a Node3D
## hierarchy with per-cell MultiMeshInstance3D batches.
## Presentation (shaders, materials, fog, water, audio, external hero props) stays consumer-owned.
class_name ProcgenWorldLoader
extends RefCounted

const INSTANCES_SCHEMA := "arcore.procgen.instances.v1"
const MANIFEST_SCHEMA := "arcore.procgen.bake-manifest.v1"


## Load a baked bundle directory into `parent`.
## `options` keys (all optional):
##   - terrain_material: Material
##   - layer_materials: Dictionary { layer_id: Material }
##   - external_meshes: Dictionary { mesh_id: Mesh }
##   - external_prop_scenes: Dictionary { mesh_id: PackedScene }
##   - create_terrain_collision: bool (default true)
## Returns a Dictionary with { ok, root, manifest, stats, errors }.
static func load_bundle(parent: Node3D, bundle_dir: String, options: Dictionary = {}) -> Dictionary:
	var errors: Array[String] = []
	var manifest := _read_json(bundle_dir.path_join("manifest.json"), errors)
	var instances_doc := _read_json(bundle_dir.path_join("instances.json"), errors)
	if not errors.is_empty():
		return {"ok": false, "root": null, "manifest": manifest, "stats": {}, "errors": errors}

	if str(manifest.get("schema", "")) != MANIFEST_SCHEMA:
		errors.append("Unexpected manifest schema: %s" % str(manifest.get("schema", "")))
	if str(instances_doc.get("schema", "")) != INSTANCES_SCHEMA:
		errors.append("Unexpected instances schema: %s" % str(instances_doc.get("schema", "")))
	if not errors.is_empty():
		return {"ok": false, "root": null, "manifest": manifest, "stats": {}, "errors": errors}

	var recipe_name := str(manifest.get("recipe", {}).get("name", "procgen_world"))
	var root := Node3D.new()
	root.name = "ProcgenWorld_%s" % recipe_name
	parent.add_child(root)

	var terrain_node := _load_glb(bundle_dir.path_join("terrain.glb"), errors)
	var library_meshes := _extract_mesh_library(bundle_dir.path_join("meshes.glb"), errors)
	var external_meshes: Dictionary = options.get("external_meshes", {})
	for key in external_meshes.keys():
		library_meshes[str(key)] = external_meshes[key]

	var terrain_mat: Material = options.get("terrain_material", null)
	var make_collision: bool = bool(options.get("create_terrain_collision", true))
	var terrain_cells := 0
	if terrain_node != null:
		terrain_node.name = "Terrain"
		root.add_child(terrain_node)
		for child in terrain_node.get_children():
			if child is MeshInstance3D:
				terrain_cells += 1
				if terrain_mat != null:
					child.material_override = terrain_mat
				if make_collision and child.mesh != null:
					child.create_trimesh_collision()

	var scatter_root := Node3D.new()
	scatter_root.name = "Scatter"
	root.add_child(scatter_root)

	var layer_materials: Dictionary = options.get("layer_materials", {})
	var multimesh_batches := 0
	var instance_total := 0
	for layer in instances_doc.get("layers", []):
		var layer_id := str(layer.get("layer", "layer"))
		var mesh_id := str(layer.get("mesh", ""))
		var mesh: Mesh = library_meshes.get(mesh_id, null)
		if mesh == null:
			errors.append("Missing mesh '%s' for scatter layer '%s'" % [mesh_id, layer_id])
			continue
		var layer_node := Node3D.new()
		layer_node.name = layer_id
		scatter_root.add_child(layer_node)
		var mat: Material = layer_materials.get(layer_id, null)

		for cell_entry in layer.get("cells", []):
			var cell_coords: Array = cell_entry.get("cell", [0, 0])
			var items: Array = cell_entry.get("instances", [])
			if items.is_empty():
				continue
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = mesh
			mm.instance_count = items.size()
			for idx in items.size():
				mm.set_instance_transform(idx, _to_transform(items[idx]))
			var mmi := MultiMeshInstance3D.new()
			mmi.name = "cell_%d_%d" % [int(cell_coords[0]), int(cell_coords[1])]
			mmi.multimesh = mm
			if mat != null:
				mmi.material_override = mat
			layer_node.add_child(mmi)
			multimesh_batches += 1
			instance_total += items.size()

	var props_root := Node3D.new()
	props_root.name = "Props"
	root.add_child(props_root)
	var prop_scenes: Dictionary = options.get("external_prop_scenes", {})
	var props_placed := 0
	for prop in instances_doc.get("props", []):
		var prop_id := str(prop.get("id", "prop"))
		var mesh_id := str(prop.get("mesh", ""))
		var xform := _to_transform(prop.get("instance", {}))
		if prop_scenes.has(mesh_id) and prop_scenes[mesh_id] is PackedScene:
			var inst := (prop_scenes[mesh_id] as PackedScene).instantiate()
			if inst is Node3D:
				inst.name = prop_id
				inst.transform = xform
				props_root.add_child(inst)
				props_placed += 1
		elif library_meshes.has(mesh_id):
			var mi := MeshInstance3D.new()
			mi.name = prop_id
			mi.mesh = library_meshes[mesh_id]
			mi.transform = xform
			props_root.add_child(mi)
			props_placed += 1
		else:
			var anchor := Marker3D.new()
			anchor.name = prop_id
			anchor.transform = xform
			anchor.set_meta("procgen_mesh_id", mesh_id)
			anchor.set_meta("procgen_external", bool(prop.get("external", false)))
			props_root.add_child(anchor)
			props_placed += 1

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
		"errors": errors,
	}


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
			meshes[child.name] = child.mesh
	root.queue_free()
	return meshes
