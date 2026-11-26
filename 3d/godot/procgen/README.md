# Godot 4 Procedural World Loader (`3d/godot/procgen`)

Godot 4 runtime adapter for bundles produced by [`arcore_procgen`](../../../shared/procgen/README.md).

## What It Does

`procgen_world_loader.gd` loads a baked bundle directory (`terrain.glb`, `meshes.glb`, `instances.json`, `manifest.json`) via Godot's built-in `GLTFDocument` + `MultiMeshInstance3D`:

- Instantiates one `MeshInstance3D` per non-empty terrain cell (`cell_<x>_<z>`); optional trimesh collision lives on a single `StaticBody3D` (`Terrain/TerrainCollision`).
- Populates one `MultiMeshInstance3D` per `(scatter_layer, cell)` for frustum-culled instancing, uploading each batch in one `MultiMesh.buffer` call.
- Applies per-layer draw settings (`layer_settings`: `cast_shadow`, `visibility_range_end`, `visibility_range_fade`, `extra_cull_margin`); the `"*"` key is the fallback for `layer_settings` and `layer_materials`.
- Optionally fills `INSTANCE_CUSTOM` with four deterministic random values per instance (`instance_custom_data`) so one material can vary tint and animation phase across a batch.
- Tags every prop node with `procgen_mesh_id` / `procgen_external` metadata so the consumer can style or replace it.
- Reports `layers` (`{ layer_id: { mesh, instances, batches } }`) alongside `stats`.
- Places props from `meshes.glb`, consumer-supplied `external_prop_scenes`, or `Marker3D` anchors when an external hero mesh is not yet bound.

## Consumer Boundary

Keep look, audio, and gameplay in the consuming game:

- Pass underwater/terrain `ShaderMaterial` overrides through `options.terrain_material` and `options.layer_materials` (e.g. Beer-Lambert fog, caustics, vertex kelp sway).
- Read `manifest.presentation` and `manifest.water_level` to configure the game's `WorldEnvironment`, water plane, and audio.
- Terrain meshes carry baked ambient occlusion as vertex color (`COLOR.r`, `1.0` = open). The loader never applies it; the terrain material chooses how to use it.
- Use GDScript only — no C#/.NET dependency is introduced, preserving Godot web/mobile export compatibility.

## Example Usage

```gdscript
var result := ProcgenWorldLoader.load_bundle(self, "res://levels/underwater_basin", {
	"terrain_material": preload("res://shaders/seabed.tres"),
	"layer_materials": {
		"kelp_forest": preload("res://shaders/kelp_sway.tres"),
	},
	"layer_settings": {
		"*": {"visibility_range_end": 130.0},
		"sea_grass": {"cast_shadow": false, "visibility_range_end": 80.0, "extra_cull_margin": 1.0},
	},
	"instance_custom_data": true,
	"external_prop_scenes": {
		"hero_shipwreck": preload("res://props/shipwreck.tscn"),
	},
	"create_terrain_collision": true,
})
assert(result.ok, str(result.errors))
```

## Companions

Two more files sit beside the loader. Each is independent: vendor only what the game uses.

### `procgen_preview.gd`: a world as one distant mesh

Every bake writes `preview.json`, a coarse grid of top and underside heights. `ProcgenPreview.build(bundle_dir, options)` turns it into one `MeshInstance3D` of a few thousand triangles, so a scene can show a neighboring or far-away world without loading its bundle: land under a cloud deck, islands overhead, the shore around a lake.

```gdscript
const ProcgenPreview := preload("res://addons/gamecore_procgen/procgen_preview.gd")
var islands := ProcgenPreview.build("res://worlds/sky_islands", {
	"offset": Vector3(0, 110, 0),   # where the previewed world's `pivot` at `y_origin` lands here
	"y_origin": 14.0,
	"material": haze_material,      # look stays with the consumer; default is plain matte grey
})
if islands != null:
	add_child(islands)
```

Options: `pivot`, `offset`, `y_origin`, `scale_xz`, `scale_y`, `clip_below` (drop land under a height, such as a lake bed), `undersides` (bottoms of floating land), `material`. The mesh has smooth normals and no vertex colors or UVs.

### `procgen_quality.gd`: quality presets by scene walk

Add it as an autoload (any name; `Quality` below). It scales a game from an integrated GPU to a desktop card without touching level code, by tuning nodes as they enter the tree and again after each scene change:

- loader scatter batches: share of instances drawn (`MultiMesh.visible_instance_count`) and draw distance
- `GPUParticles3D`: share of particles
- `DirectionalLight3D`: shadows on or off, and shadow distance
- `WorldEnvironment`: SSAO and glow, only ever switched off
- the viewport: 3D render scale (FSR under Forward+) and MSAA

Bake at full scatter density: `arcore_procgen` stores each cell's instances in random order, so drawing a prefix thins evenly and no rebake is needed per preset. Code that spawns things can ask for `Quality.scaled(count)` or `Quality.value("detail")`.

Defaults are three presets (`low`, `medium`, `high`), `F6` to cycle, and a saved choice in `user://quality.cfg`; with nothing saved, integrated and software GPUs start on the lightest preset. `-- --quality=<name>` overrides. `order`, `default_level`, `toggle_key`, `save_path` and the `presets` dictionary are all settable, so a game can add tiers or rename them.

### Reuse suitability review (companions)

Per [module-specialization.md](../../../shared/module-specialization.md#reuse-suitability-review):

```json
{
  "module": "gamecore.godot.procgen-world-loader",
  "responsibility": "Godot 4 adapters for arcore_procgen bake bundles: scene loader, preview mesh builder, and quality presets that scale loader output and common render settings.",
  "coupling_findings": [
    "procgen_preview.gd reads only preview.json (arcore.procgen.preview.v1) and takes placement and material as options; no game names or paths.",
    "procgen_quality.gd depends on the loader's scene layout (<world>/Scatter/<layer>/<cell>) and on stock Godot node types; preset values, key, save path and tier names are parameters.",
    "Neither file references the other or the loader script."
  ],
  "decision": "extract-adapter",
  "reason": "The bake already emitted preview.json and shuffled scatter with no Godot consumer for either upstream. Both adapters are small, stable and free of presentation choices.",
  "shared_changes": ["3d/godot/procgen/procgen_preview.gd", "3d/godot/procgen/procgen_quality.gd"],
  "consumer_adapter_paths": ["ShammyGodotSandbox/scripts/sandbox_world.gd", "ShammyGodotSandbox/scripts/levels/overland_world.gd", "ShammyGodotSandbox/scripts/levels/upper_atmosphere_world.gd"],
  "alternative_use_case": {
    "kind": "synthetic",
    "result": "passed",
    "evidence": "Preview: three placements in one consumer with different data and settings (land stretched 11x around a lake with a clip height; islands with undersides lifted overhead; land sunk under a cloud deck). Quality: four scenes, three baked worlds plus one built entirely at runtime with no loader scatter, at three presets and under two renderers. Not a second-game validation."
  },
  "compatibility": "0.3.0: additive (two new files). The loader is unchanged. Preview needs bundles baked by arcore_procgen with preview export; even thinning needs bundles baked after per-cell instance shuffling.",
  "checks": ["Rendered in ShammyGodotSandbox on Godot 4.7.2 (Forward+ and Mobile)."],
  "remaining_limits": [
    "No automated Godot test in this repository.",
    "Second-game validation not_run.",
    "Quality tunes only what it can see generically; counts a game spawns itself must read scaled()."
  ]
}
```

## Validation Status

- Bundle format (`terrain.glb`, `meshes.glb`, `instances.json`, `manifest.json`) is verified by `cargo test` in `shared/procgen/rust`.
- Rendered execution: verified through the `ShammyGodotSandbox` consumer on Godot 4.7.2 (Forward+), which vendors this file (9,009 instances in 409 batches plus 64 terrain cells load in about 0.3–0.6 s). No automated Godot test runs in this repository.
