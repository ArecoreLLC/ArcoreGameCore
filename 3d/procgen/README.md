# 3D Procedural World Generation (`3d/procgen`)

Starter recipes and 3D conventions for the [procedural world generation workflow](../../workflows/procedural-world-generation/README.md) powered by [`shared/procgen`](../../shared/procgen/README.md).

## Starter Recipes

| Recipe | Biome / Purpose | Bounds & Voxel | Highlights |
| :--- | :--- | :--- | :--- |
| [underwater-basin.json](recipes/underwater-basin.json) | Underwater explorer mini-game slice (inspired by `Noniv/abyssal-garden`, MIT) | `192 × 56 × 192 m`, `1.0 m` voxel, `24 m` cells | West mesa, east ridge, central rock arch, swim tunnel, grotto basin, clustered kelp blades, grotto barrel sponges, seabed boulders, external `hero_shipwreck` anchor. |
| [canyon-arch.json](recipes/canyon-arch.json) | Synthetic terrestrial validation case | `128 × 48 × 128 m`, `1.0 m` voxel, `32 m` cells | Capsule canyon cut, sandstone arch, slope-gated talus rocks, canyon-floor scrub, grounded cairn prop. |

## Engine Adapters

- **Godot 4:** [3d/godot/procgen/README.md](../godot/procgen/README.md) — loads `terrain.glb`, `meshes.glb`, and `instances.json` into `Node3D` + per-cell `MultiMeshInstance3D` batches.
- **Unreal 5.x:** [3d/unreal/procgen/README.md](../unreal/procgen/README.md) — imports glTF chunks via Interchange and populates `HISM` / Niagara from `instances.json`.
