# Godot 4 Procedural World Loader (`3d/godot/procgen`)

Godot 4 runtime adapter for bundles produced by [`arcore_procgen`](../../../shared/procgen/README.md).

## What It Does

`procgen_world_loader.gd` loads a baked bundle directory (`terrain.glb`, `meshes.glb`, `instances.json`, `manifest.json`) via Godot's built-in `GLTFDocument` + `MultiMeshInstance3D`:

- Instantiates one `MeshInstance3D` per non-empty terrain cell (`cell_<x>_<z>`) with optional trimesh collision.
- Populates one `MultiMeshInstance3D` per `(scatter_layer, cell)` for frustum-culled instancing.
- Places props from `meshes.glb`, consumer-supplied `external_prop_scenes`, or `Marker3D` anchors when an external hero mesh is not yet bound.

## Consumer Boundary

Keep look, audio, and gameplay in the consuming game:

- Pass underwater/terrain `ShaderMaterial` overrides through `options.terrain_material` and `options.layer_materials` (e.g. Beer-Lambert fog, caustics, vertex kelp sway).
- Read `manifest.presentation` and `manifest.water_level` to configure the game's `WorldEnvironment`, water plane, and audio.
- Use GDScript only — no C#/.NET dependency is introduced, preserving Godot web/mobile export compatibility.

## Example Usage

```gdscript
var result := ProcgenWorldLoader.load_bundle(self, "res://levels/underwater_basin", {
	"terrain_material": preload("res://shaders/seabed.tres"),
	"layer_materials": {
		"kelp_forest": preload("res://shaders/kelp_sway.tres"),
	},
	"external_prop_scenes": {
		"hero_shipwreck": preload("res://props/shipwreck.tscn"),
	},
	"create_terrain_collision": true,
})
assert(result.ok, str(result.errors))
```

## Validation Status

- Bundle format (`terrain.glb`, `meshes.glb`, `instances.json`, `manifest.json`) is verified by `cargo test` in `shared/procgen/rust`.
- Live Godot 4 headless/rendered execution of `procgen_world_loader.gd` is `not_run` in this workspace (no Godot 4 binary installed on `PATH`).
