# Procedural World Generation Example

Recorded on Windows with `rustc 1.99.1` / `cargo 1.99.1` against [`3d/procgen/recipes/underwater-basin.json`](../../3d/procgen/recipes/underwater-basin.json) and [`3d/procgen/recipes/canyon-arch.json`](../../3d/procgen/recipes/canyon-arch.json).

## 1. Unit & Integration Tests

```powershell
cargo test --offline --manifest-path shared/procgen/rust/Cargo.toml
```

Result: **passed** (`12` unit tests + `12` integration tests in `tests/pipeline.rs`, covering Surface Nets watertightness/winding, thread-count determinism, primitive culling equivalence, SDF glide/tunnel collision, raycast, scatter density/slope/zone gating, baked vertex occlusion, randomized reef dressing, generated shipwreck placement, GLB validity, and shipped recipe validation).

## 2. Validate & Bake Starter Recipes

```powershell
cargo run --release --offline --manifest-path shared/procgen/rust/Cargo.toml -- validate 3d/procgen/recipes/underwater-basin.json 3d/procgen/recipes/canyon-arch.json
cargo run --release --offline --manifest-path shared/procgen/rust/Cargo.toml -- bake 3d/procgen/recipes/underwater-basin.json --out shared/procgen/rust/out/underwater-basin --quality medium
cargo run --release --offline --manifest-path shared/procgen/rust/Cargo.toml -- bake 3d/procgen/recipes/canyon-arch.json --out shared/procgen/rust/out/canyon-arch --quality high
```

### Measured Output (`underwater-basin`, `--quality medium`)

- `field`: `36.9 ms` (`193×57×193` samples, `39.1%` solid)
- `surface`: `30.9 ms` (`52,380` vertices, `103,936` triangles)
- `cells`: `8.3 ms` (`64` of `64` cells occupied)
- `parametric`: `0.1 ms` (`3` meshes)
- `scatter`: `5.5 ms` (`1,763` instances, `2` props)
- Artifacts: `terrain.glb` (`2,664,788` bytes), `meshes.glb` (`13,988` bytes), `instances.json` (`302,753` bytes), `manifest.json`

### Measured Output (`canyon-arch`, `--quality high`)

- `field`: `12.5 ms` (`129×49×129` samples, `31.3%` solid)
- `surface`: `10.7 ms` (`23,394` vertices, `46,212` triangles)
- `cells`: `3.6 ms` (`16` of `16` cells occupied)
- `parametric`: `0.0 ms` (`2` meshes)
- `scatter`: `1.0 ms` (`279` instances, `1` prop)
- Artifacts: `terrain.glb` (`1,163,376` bytes), `meshes.glb` (`9,536` bytes), `instances.json` (`52,072` bytes), `manifest.json`

### Measured Output (`arcore_procgen` 0.2.0, randomized `underwater-cartoon`, seed `20261123`, `--quality medium`, 20 threads)

Same terrain as the 0.1.0 run of this recipe (`field 43 ms`, `surface 28 ms`, `cells 7 ms`, `scatter 5 ms`, 1,894 instances, no occlusion):

- `field`: `~10 ms` (`193×57×193` samples; primitive culling + banded detail noise)
- `surface`: `~9 ms` (`55,221` vertices, `109,628` triangles, including vertex occlusion)
- `cells`: `~3 ms`
- `parametric`: `0.2 ms` (`9` meshes)
- `scatter`: `~4 ms` (`9,009` instances in `9` layers, `2` props)

The per-recipe timings above this section were recorded with 0.1.0 and have not been re-measured.

## 3. Remaining Unverified Steps

- Godot 4 runtime loading of `3d/godot/procgen/procgen_world_loader.gd`: verified only through the `ShammyGodotSandbox` consumer (Godot 4.7.2); no automated Godot test in this repository.
- Unreal 5.x Interchange glTF import + HISM population: `not_run` (consumer-owned).
