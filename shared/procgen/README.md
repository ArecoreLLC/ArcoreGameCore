# Procedural World Generation (`shared/procgen`)

Engine-neutral procedural world generation contracts and Rust pipeline modules for ArcoreGameCore.

## Pipeline Architecture

Every world bake executes seven deterministic stages in order:

```text
recipe ─► field ─► surface ─► cells ─► parametric ─► scatter ─► export
  (0)      (1)       (2)       (3)         (4)          (5)       (6)
```

| Stage | Module | Responsibility |
| :--- | :--- | :--- |
| 0. Recipe | `recipe.rs` | Parse and validate `arcore.procgen.world-recipe.v1` JSON (bounds, noise, CSG primitives, zones, parametric meshes, scatter layers, props). |
| 1. Field | `stages/field.rs` | Evaluate 3D density grid (`density > 0` solid, `< 0` open) from base height, 2D/3D fBm noise, and smooth CSG primitives (sphere, box, cylinder, capsule, torus). Primitives are culled per sample by bounding sphere, and detail noise is only evaluated in a narrow band around the surface (solid/open classification stays exact). Multi-threaded over Z-slabs with identical output for any thread count. |
| 2. Surface | `stages/surface.rs`, `stages/occlusion.rs` | Extract closed, indexed, outward-normal triangle meshes using Surface Nets (multi-threaded, thread-count independent), then bake per-vertex ambient occlusion from the density field into a grayscale vertex color (`1.0` = open). |
| 3. Cells | `stages/cells.rs` | Partition terrain geometry into a regular XZ cell grid (`cell_<x>_<z>`) for frustum culling, streaming, or per-cell batching. |
| 4. Parametric | `stages/parametric.rs`, `stages/tree.rs` | Build code-generated reusable meshes (`rock`, `lathe`, `blade`, seeded `branch` for corals/bushes, `ship` hull/deck/masts with seeded wreck damage, `tree` in `round`/`pine`/`palm` styles with trunk/foliage vertex colors) with zero external model files. |
| 5. Scatter & Props | `stages/scatter.rs` | Area-weighted triangle scatter gated by slope, height, zone include/exclude, and clustering noise; per-`(layer, cell)` deterministic RNG streams. Ground-snapped props via SDF raycast, with optional `roll_deg` lean. |
| 6. Export | `export/glb.rs`, `export/bundle.rs` | Emit deterministic glTF 2.0 binary (`terrain.glb` with `COLOR_0` occlusion, `meshes.glb`), `instances.json` (`arcore.procgen.instances.v1`), and `manifest.json` (`arcore.procgen.bake-manifest.v1`) with SHA-256 provenance. |
| Runtime (optional) | `runtime/collision.rs` | Stepped sphere-vs-SDF `glide()` and `raycast()` queries for swim/fly controllers without a physics engine. |

## Randomizer Themes

`arcore-procgen randomize --theme <theme>` (`randomize.rs`, `biomes.rs`) turns a seed plus a few knobs into a valid recipe:

| Theme | World |
| :--- | :--- |
| `underwater-cartoon` | Reef basin: mesas, arches, tunnels, glowing grotto, kelp, corals, sponges, sea fans, anemones, optional shipwreck (`--shipwreck`) and hydrothermal vent field with tube worms (`--vents N`). |
| `underwater-basin` | Same layout with the atmospheric palette. |
| `canyon-arch` | Dry desert canyon with arches. |
| `overland-cartoon` | Rolling hills, a lake fed by a meandering river (`water_level` 0), rocky outcrops with caves, arches, pine forest, oak groves, birch stands, wildflower meadow, reeds, mushrooms. |
| `sky-islands` | Floating islands in open air (`base_height` far below the bounds), each a flat top on a hanging rock root, with satellite boulders, stone rings, trees, hanging vines and crystals. |

Every themed world also gets a landmark of weathered stone columns unless `--no-ruins` is passed (sunken ruins on the reef, a standing-stone ring overland, a temple ring on the main sky island).

Scatter instances are stored in random order within each cell, so the per-cell cap thins evenly and a consumer can draw any prefix of a cell as a lower level of detail (the sandbox's quality presets do exactly this).

Zones may set `clear: true` to keep every scatter layer out (craters, plazas, landing pads); `--crater` adds an impact crater with a skid trench and a cleared zone to `overland-cartoon`.

`bake --mesh-detail 1|2` adds tessellation to library meshes large enough to show it and also writes each changed mesh's recipe-level twin as `<id>__lod`, so a consumer can draw the heavy mesh nearby only (the Godot loader's `lod_distance`). A `--density-scale` above 1 lifts per-cell caps with it, for denser high-end bakes of the same layout.

A scatter layer may set `min_density_scale` so it is only placed in bakes at or above that density scale; the `grass_carpet` layers (mesh kind `tuft`, a clump of blades) use it, so one recipe serves a lean bake and a dense one.

### Linked stacks and previews

- `arcore-procgen stack --seed <N> --out-dir <dir>` writes reef, overland and sky recipes generated together in one XZ frame: the overland lake sits at the origin anchor and the first sky islands float over the overland's hills (`link_center` and `island_hints` on `RandomizeConfig`). `<dir>/stack.json` records the anchors.
- Every bake also writes `preview.json` (`arcore.procgen.preview.v1`, `export/preview.rs`): a 96 x 96 grid of top and underside heights. A neighboring level can draw it as one low-poly mesh, so transitions between generated worlds have real geometry to show without loading the other bundle.

## Coordinate System & Units

- **glTF 2.0 convention:** `+Y` up, right-handed, meters.
- **Rotations:** unit quaternions in `[x, y, z, w]` order.
- **Density sign:** `> 0` solid, `< 0` open (water/air), `0` surface.

## Workspace & Commands

The Rust workspace lives in [rust/Cargo.toml](rust/Cargo.toml) (`arcore_procgen` library + `arcore-procgen` CLI).

```powershell
# Run unit and integration tests
cargo test --manifest-path shared/procgen/rust/Cargo.toml

# Validate recipes
cargo run --release --manifest-path shared/procgen/rust/Cargo.toml -- validate 3d/procgen/recipes/underwater-basin.json 3d/procgen/recipes/canyon-arch.json

# Bake a world bundle (quality: low=0.25, medium=0.5, high=1.0)
cargo run --release --manifest-path shared/procgen/rust/Cargo.toml -- bake 3d/procgen/recipes/underwater-basin.json --out shared/procgen/rust/out/underwater-basin --quality medium
```

## Consumer Boundary

- **Shared (`shared/procgen`):** deterministic math, SDF/CSG evaluation, Surface Nets, cell splitting, scatter placement, collision queries, and glTF/JSON export.
- **Consumer-owned:** shaders, materials, lighting, fog/underwater optics, audio synthesis/stems, gameplay loops, input/camera controllers, and hero external meshes (`"external": true`). The recipe's `presentation` object is copied opaquely into `manifest.json` and never interpreted by `arcore_procgen`.

## Engine Adapters & Workflows

- Recipes catalog: [3d/procgen/README.md](../../3d/procgen/README.md)
- Godot 4 bundle loader: [3d/godot/procgen/README.md](../../3d/godot/procgen/README.md)
- Unreal 5.x integration guide: [3d/unreal/procgen/README.md](../../3d/unreal/procgen/README.md)
- End-to-end workflow guide: [workflows/procedural-world-generation/README.md](../../workflows/procedural-world-generation/README.md)

## Reuse Suitability Review

Per [module-specialization.md](../module-specialization.md#reuse-suitability-review):

```json
{
  "module": "arcore-procgen",
  "responsibility": "Engine-neutral deterministic 3D world generation from JSON recipes (SDF/CSG density field, Surface Nets mesh, XZ cell chunks, parametric meshes, area-weighted scatter, SDF glide/raycast, glTF 2.0 + JSON bundle export).",
  "coupling_findings": [
    "No engine, window, GPU, audio or private game-asset dependencies.",
    "Theme/look data is isolated in opaque recipe.presentation; hero external assets use mesh keys with external=true."
  ],
  "decision": "extract-adapter",
  "reason": "Keep deterministic geometry/scatter math in shared/procgen/rust and keep shaders, materials, audio and gameplay in engine-specific adapters under 3d/godot/procgen and 3d/unreal/procgen.",
  "shared_changes": [
    "shared/procgen/rust/crates/arcore_procgen",
    "shared/procgen/rust/crates/arcore_procgen_cli"
  ],
  "consumer_adapter_paths": [
    "3d/godot/procgen/procgen_world_loader.gd",
    "3d/unreal/procgen/README.md"
  ],
  "alternative_use_case": {
    "kind": "synthetic",
    "result": "passed",
    "evidence": "3d/procgen/recipes/canyon-arch.json validates and bakes alongside 3d/procgen/recipes/underwater-basin.json with zero biome-specific code paths."
  },
  "compatibility": "0.2.0: schemas unchanged (arcore.procgen.world-recipe.v1, arcore.procgen.instances.v1, arcore.procgen.bake-manifest.v1). Additive: `branch` and `ship` mesh kinds, prop `roll_deg`, randomizer `--shipwreck`, terrain `COLOR_0` vertex occlusion, richer randomized underwater layers. Output hashes differ from 0.1.0 for the same recipe.",
  "checks": [
    "cargo test --manifest-path shared/procgen/rust/Cargo.toml"
  ],
  "remaining_limits": [
    "Godot 4 runtime loader is exercised by the ShammyGodotSandbox consumer (Godot 4.7.2, Forward+); there is no automated Godot test in this repository.",
    "Unreal 5.x C++ / Interchange import adapter is documented as a guide; no compiled UE plugin yet.",
    "Second-game production validation is not_run."
  ]
}
```
