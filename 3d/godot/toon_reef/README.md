# Toon Reef (`3d/godot/toon_reef`)

Godot 4 presentation module that dresses an [`arcore_procgen`](../../../shared/procgen/README.md) underwater bundle as a three-tone cartoon reef. It pairs with the [bundle loader](../procgen/README.md) and has no assets: every surface, creature and effect is a shader or a few lines of mesh code.

## What It Provides

| File | Role |
| :--- | :--- |
| `toon_reef_world.gd` | Entry point: `build()` loads and styles a bundle, `add_atmosphere()` and `add_life()` add the water volume and creatures, plus ground-height and manifest helpers. |
| `reef_materials.gd` | Maps each scatter layer to a material and draw settings (palette, outline, sway, draw distance). Colors come from `manifest.presentation` when present. |
| `underwater_atmosphere.gd` | Depth-driven fog and light, sun shafts, marine snow, bubbles. Borrows the host scene's `Environment` and sun and blends them back when the camera leaves the water. |
| `fish_school.gd`, `manta_rays.gd` | Fish schools and manta rays, one draw call each, animated in the vertex shader. Manta laps are lifted clear of the terrain they pass over. |
| `jellyfish.gd` | Drifting jellyfish (generated bell and ribbon tentacles), one MultiMesh; pulse, bob and tentacle ripple run in `toon_jelly.gdshader`. |
| `vent_plumes.gd` | Bubble plumes and flickering ember lights on hydrothermal vent chimneys. |
| `shaders/` | Seabed, prop, blade, outline, wood, fish, manta, sun-shaft and bubble shaders sharing `underwater.gdshaderinc` (toon band, caustics, depth tint, swimmer lap path). |

## Usage

```gdscript
const ProcgenWorldLoader := preload("res://addons/gamecore_procgen/procgen_world_loader.gd")
const ToonReef := preload("res://addons/gamecore_toon_reef/toon_reef_world.gd")

func _ready() -> void:
	var reef := ToonReef.build(self, ProcgenWorldLoader, "res://worlds/reef", {"origin": Vector3(160, 0, 170)})
	ToonReef.add_atmosphere(self, reef, world_environment.environment, sun, {"active_radius": 144.0})
	await get_tree().physics_frame   # ground queries need live terrain collision
	await get_tree().physics_frame
	ToonReef.add_life(self, reef)
```

## Integration Notes

- **No project settings needed.** The four shader globals (`uw_water_level`, `uw_deep_color`, `uw_caustic_strength`, `uw_sun_dir`) are registered at runtime; a project that already declares them under Shader Globals keeps its own.
- **No global class names.** Scripts reference each other with relative `preload`, and shaders use a relative `#include`, so the folder works wherever it is vendored.
- **Works inside a larger world.** Pass `origin` to place the reef anywhere, and `active_radius` so the underwater look only applies near it. The host's fog, ambient light and sun are captured once and restored on exit.
- **The loader is passed in**, so this module does not depend on where the procgen loader is vendored.
- **Terrain occlusion.** The seabed shader reads the baked vertex occlusion (`COLOR.r`) that `arcore_procgen` 0.2.0 writes.
- **Per-instance distance fade.** Each scatter instance shrinks away over the last 30% of its layer's `range` (`fade_range` on the prop, blade and outline shaders; `uw_distance_keep` in the include), so nothing pops in by the cell. The batch itself is culled one cell further out. A fifth global, `gc_range_scale`, lets a quality module scale those distances.
- **Wrecks.** Props whose mesh id is in `WRECK_MESH_IDS` (`shipwreck`) get the timber material, which reads the ship mesh's part shade from vertex color.
- **Vents.** Props whose mesh id is in `VENT_MESH_IDS` (`vent_chimney`, from the randomizer's `--vents`) get a basalt material with an ember rim in `presentation.vent_color`, and `add_life()` gives each a bubble plume and light. `add_life()` also takes `jellyfish` (default 24; 0 disables).
- **Ruins.** Props whose mesh id is in `RUIN_MESH_IDS` (`ruin_column`) get a pale stone material (`presentation.stone_color`).
- **Extra reef layers.** `sea_fans`, `anemones`, `tube_worms`, `sea_urchins`, `giant_clams`, `staghorn_thickets`, `starfish`, `vase_sponges`, `sea_whips` and `cabbage_corals` have styles; `fan_palette` and `anemone_palette` in `presentation` recolor them.

## Consumer Boundary

Kept in the consuming game: the water surface, player and camera, audio, gameplay, custom hero props, and how the region is entered.

## Validation Status

- Exercised in two consumers on Godot 4.7.2 (Forward+): `ShammyGodotSandbox` (standalone scene, capture tour) and `ShammyVerse` (Coral Deep region inside the island world, `tests/coral_deep_integration.gd`, 21 checks).
- No automated Godot test runs in this repository.
- Not verified: Compatibility renderer, exported builds, mobile.
