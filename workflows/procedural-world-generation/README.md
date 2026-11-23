# Procedural World Generation Workflow

Generate deterministic, engine-neutral 3D world bundles from JSON recipes using [`shared/procgen`](../../shared/procgen/README.md) (`arcore_procgen` Rust pipeline), then import them into Godot 4 or Unreal Engine 5.

## When to Use

- Lightweight 3D mini-games or exploration zones (e.g. underwater basins, canyons, grottos) where you want small source footprints, fast iteration, and reproducible builds.
- Shared world geometry/scatter across Godot and Unreal without duplicating terrain authoring.

## Pipeline Stages

1. **Author or randomize a recipe** (`arcore.procgen.world-recipe.v1`) under `3d/procgen/recipes/` (or in the consumer project):
   ```powershell
   cargo run --release --manifest-path shared/procgen/rust/Cargo.toml -- randomize --seed 20261123 --theme underwater-cartoon --out <out_dir>/recipe.json --external-prop hero_shipwreck
   ```
2. **Validate** bounds, CSG primitives, zones, mesh references, and scatter constraints:
   ```powershell
   cargo run --release --manifest-path shared/procgen/rust/Cargo.toml -- validate 3d/procgen/recipes/underwater-basin.json
   ```
3. **Bake** the deterministic bundle (`terrain.glb`, `meshes.glb`, `instances.json`, `manifest.json`):
   ```powershell
   cargo run --release --manifest-path shared/procgen/rust/Cargo.toml -- bake 3d/procgen/recipes/underwater-basin.json --out <out_dir> --quality medium
   ```
4. **Bind custom 3D assets (GLB / Blender / ModelForge)** using `"external": true` on any scatter layer or prop entry. The Rust pipeline computes placement, slope/zone gating, ground snapping, and cell assignment without loading external binaries; the engine adapter resolves the `mesh` key to a consumer `.glb` / `.tscn` / Static Mesh.
5. **Load in the target engine** and apply consumer-owned shaders, lighting, audio, and gameplay:
   - Godot 4: [3d/godot/procgen/README.md](../../3d/godot/procgen/README.md)
   - Unreal 5.x: [3d/unreal/procgen/README.md](../../3d/unreal/procgen/README.md)

## References

- Engine-neutral pipeline contract & reuse review: [shared/procgen/README.md](../../shared/procgen/README.md)
- Starter recipes: [3d/procgen/README.md](../../3d/procgen/README.md)
- Migration & evidence contract: [shared/migration-contract.md](../../shared/migration-contract.md)
- Example run & measured timings: [example.md](example.md)
