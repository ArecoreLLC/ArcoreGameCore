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
| 1. Field | `stages/field.rs` | Evaluate 3D density grid (`density > 0` solid, `< 0` open) from base height, 2D/3D fBm noise, and smooth CSG primitives (sphere, box, cylinder, capsule, torus). Multi-threaded over Z-slabs with identical output for any thread count. |
| 2. Surface | `stages/surface.rs` | Extract closed, indexed, outward-normal triangle meshes using Surface Nets. |
| 3. Cells | `stages/cells.rs` | Partition terrain geometry into a regular XZ cell grid (`cell_<x>_<z>`) for frustum culling, streaming, or per-cell batching. |
| 4. Parametric | `stages/parametric.rs` | Build code-generated reusable meshes (`rock`, `lathe`, `blade`) with zero external model files. |
| 5. Scatter & Props | `stages/scatter.rs` | Area-weighted triangle scatter gated by slope, height, zone include/exclude, and clustering noise; per-`(layer, cell)` deterministic RNG streams. Ground-snapped props via SDF raycast. |
| 6. Export | `export/glb.rs`, `export/bundle.rs` | Emit deterministic glTF 2.0 binary (`terrain.glb`, `meshes.glb`), `instances.json` (`arcore.procgen.instances.v1`), and `manifest.json` (`arcore.procgen.bake-manifest.v1`) with SHA-256 provenance. |
| Runtime (optional) | `runtime/collision.rs` | Stepped sphere-vs-SDF `glide()` and `raycast()` queries for swim/fly controllers without a physics engine. |

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
  "compatibility": "Initial 0.1.0 release; schema arcore.procgen.world-recipe.v1, arcore.procgen.instances.v1, arcore.procgen.bake-manifest.v1.",
  "checks": [
    "cargo test --manifest-path shared/procgen/rust/Cargo.toml"
  ],
  "remaining_limits": [
    "Godot 4 runtime loader has not yet been executed inside a live Godot 4 headless/rendered project in this workspace.",
    "Unreal 5.x C++ / Interchange import adapter is documented as a guide; no compiled UE plugin yet.",
    "Second-game production validation is not_run."
  ]
}
```
