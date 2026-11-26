# Toon Biome (`3d/godot/toon_biome`)

Godot 4 presentation module that dresses an open-air [`arcore_procgen`](../../../shared/procgen/README.md) bundle (rolling land, floating islands, anything above water) in the same three-tone cartoon look as the [toon reef](../toon_reef/README.md). It has no assets: the ground, the trees and every scatter layer are shaders plus a style table the game supplies.

## What It Provides

| File | Role |
| :--- | :--- |
| `biome_styler.gd` | Builds materials from a style table and the bundle's `presentation` colors: `ground()` for terrain, `layer()` / `style_scatter()` for scatter layers (kinds `prop`, `blade`, `tree`), `style_props()` for props by mesh id, `layer_settings()` for the loader, and `set_open_air_globals()` to point the shared toon globals at an above-water scene. |
| `shaders/toon_ground.gdshader` | Painted ground: grass on the flats with stripes and clover, an optional meadow zone with painted flower dots, layered rock on slopes, darker rock on overhang undersides, a beach band at a water line, optional snow above a height, an optional scorched patch, drifting cloud shadows, and the generator's baked crease shading (`COLOR.r`). |
| `shaders/toon_tree.gdshader` | Two-part trees for the generator's `tree` meshes (`round`, `pine`, `palm`): vertex `COLOR.r` picks trunk or foliage and `COLOR.g` a per-piece shade; each instance picks a leaf color from a palette; foliage sways and gets a bright cel rim. |

## Usage

```gdscript
const ProcgenWorldLoader := preload("res://addons/gamecore_procgen/procgen_world_loader.gd")
const BiomeStyler := preload("res://addons/gamecore_toon_biome/biome_styler.gd")

const STYLES := {
	"pine_forest": {"kind": "tree", "leaf_key": "pine_color", "leaf": Color(0.16, 0.52, 0.36), "sway": 0.1, "range": 260.0},
	"meadow_grass": {"kind": "blade", "color_key": "grass_color", "colors": [Color(0.5, 0.86, 0.38)], "sway": 0.12, "shadow": false, "range": 70.0},
	"wildflowers": {"kind": "prop", "palette_key": "flower_palette", "colors": [Color(1, 0.5, 0.5)], "emission": 0.12, "range": 80.0},
}
const FALLBACK := {"kind": "prop", "colors": [Color(0.8, 0.72, 0.68)], "outline": 0.02, "range": 180.0}

func _ready() -> void:
	var styler := BiomeStyler.new(presentation, STYLES, FALLBACK)
	BiomeStyler.set_open_air_globals(water_level, deep_color, sun.global_transform.basis.z)
	var world := ProcgenWorldLoader.load_bundle(self, "res://worlds/overland", {
		"terrain_material": styler.ground({"shore_level": water_level}),
		"layer_settings": styler.layer_settings(),
		"instance_custom_data": true,
	})
	styler.style_scatter(world.root)
	styler.style_props(world.root, {"ruin_column": {"color_key": "stone_color", "colors": [Color(0.74, 0.72, 0.68)]}})
```

Style entry keys: `kind` (`prop`, `blade` or `tree`); `colors`, `color_key`, `palette_key` (a fixed color list, or the name of a `presentation` color or palette that overrides it); for trees `leaf`, `leaf_key`, `leaf_palette_key`, `trunk`, `trunk_key`; and `emission`, `rim`, `outline`, `sway`, `sway_speed`, `shadow`, `range` (draw distance in meters).

## Integration Notes

- **Vendor it beside the toon reef.** This module reuses the reef's prop, blade and outline shaders, its `ReefMaterials` builder and its shader include, and reaches them by relative path. Copy it to `addons/gamecore_toon_biome` next to `addons/gamecore_toon_reef`.
- **Shared shader globals.** The look reads the reef's four globals. `set_open_air_globals()` turns caustics off and sets the water level; only what lies below that level is tinted, so pass a level far below the world when there is no water.
- **Instance custom data.** Pass `instance_custom_data: true` to the loader: trees and props pick palette colors and animation phase per instance from it.
- **Trees render double-sided**, since palm fronds are single strips.
- **No global class names**; scripts are reached by `preload`.

## Consumer Boundary

Kept in the consuming game: which layers exist and how each is styled (the style table), water surfaces, sky, weather, time of day, creatures, the player and camera, audio and gameplay.

## Reuse Suitability Review

Per [module-specialization.md](../../../shared/module-specialization.md#reuse-suitability-review):

```json
{
  "module": "gamecore.godot.toon-biome",
  "responsibility": "Toon materials for open-air arcore_procgen bundles: a ground shader, a two-part shader for the generator's tree meshes, and a styler that maps scatter layers and props to materials from a consumer style table and the bundle's presentation colors.",
  "coupling_findings": [
    "Depends on gamecore.godot.toon-reef by relative path (prop/blade/outline shaders, ReefMaterials, underwater.gdshaderinc); both must be vendored as siblings.",
    "Reads the loader's scene layout (<world>/Scatter/<layer>/<cell>, <world>/Props, procgen_mesh_id meta); this is the procgen loader's documented contract.",
    "No layer ids, palettes, level names or asset paths are built in: styles and colors are data passed by the consumer."
  ],
  "decision": "extract-adapter",
  "reason": "The generator ships a tree mesh kind whose vertex colors nothing upstream could render, and every open-air world needs the same ground and styling plumbing. The shaders and the styler are stable; the style tables stay in the game.",
  "shared_changes": ["3d/godot/toon_biome"],
  "consumer_adapter_paths": ["ShammyGodotSandbox/scripts/levels/baked_level.gd", "ShammyGodotSandbox/scripts/levels/overland_world.gd", "ShammyGodotSandbox/scripts/levels/upper_atmosphere_world.gd"],
  "alternative_use_case": {
    "kind": "synthetic",
    "result": "passed",
    "evidence": "One consumer drives it with two unrelated worlds and style tables: overland-cartoon (14 layers, lake shore band, meadow zone, snow on far peaks) and sky-islands (9 layers, no water, overhang undersides), plus two stand-in terrains built from preview meshes with other palettes. Not a second-game validation."
  },
  "compatibility": "0.1.0: new module. Requires toon_reef 0.3.0 and procgen loader 0.2.0 or later.",
  "checks": ["Rendered in ShammyGodotSandbox on Godot 4.7.2 under Forward+ and Mobile, at three quality presets, by day, dusk and night."],
  "remaining_limits": [
    "No automated Godot test in this repository.",
    "Second-game validation not_run.",
    "The relative paths assume the vendored folder names gamecore_toon_biome and gamecore_toon_reef."
  ]
}
```
