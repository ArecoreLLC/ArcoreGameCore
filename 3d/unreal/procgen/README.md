# Unreal Engine 5 Procedural World Integration (`3d/unreal/procgen`)

Integration guide for consuming [`arcore_procgen`](../../../shared/procgen/README.md) bundles inside Unreal Engine 5.x (e.g. UE 5.8.4 Win64).

## Recommended Path: Offline Bake + Interchange glTF Import

1. Bake the recipe with `arcore-procgen`:
   ```powershell
   cargo run --release --manifest-path shared/procgen/rust/Cargo.toml -- bake 3d/procgen/recipes/underwater-basin.json --out <Game>/Content/Procgen/UnderwaterBasin --quality medium
   ```
2. Import `terrain.glb` and `meshes.glb` via Unreal **Interchange glTF** (Unreal handles the glTF `+Y` up, meters → UE `+Z` up, centimeters axis/unit conversion automatically on mesh import).
3. Parse `instances.json` (`arcore.procgen.instances.v1`) in a consumer `AActor` / Editor Utility script:
   - Convert each instance transform from glTF (`+Y` up, meters, right-handed) to Unreal (`+Z` up, cm, left-handed).
   - Populate one `UHierarchicalInstancedStaticMeshComponent` (HISM) per `(layer, cell)` for rocks/sponges/corals, or feed dense foliage/kelp transforms into **Niagara**.
   - Bind `"external": true` props (e.g. `hero_shipwreck`) to consumer Static Meshes or Blueprint actors.
4. Apply consumer-owned Unreal Materials (Beer-Lambert underwater post-process, Exponential/Volumetric Fog, vertex-animated foliage WPO, caustics) using `manifest.json` (`water_level`, `zones`, `presentation`).

## Optional Runtime Path: C-FFI (`extern "C"`)

If a project needs runtime-seeded worlds or SDF `glide()` collision in C++:
- Add a thin `cdylib`/`staticlib` crate alongside `arcore_procgen` exporting C-ABI buffer queries (`positions`, `normals`, `indices`, `glide`, `raycast`).
- Load it from a consumer Unreal module to populate `UDynamicMeshComponent` + `HISM`.

## Validation Status

- Offline glTF + JSON bundle generation is verified by `cargo test` in `shared/procgen/rust`.
- Unreal Editor import and smoke execution are `not_run` (consumer-owned).
