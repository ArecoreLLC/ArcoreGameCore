# Sea leaps and splashes

Make anything leap out of the sea convincingly (dolphins porpoising, fish flipping, flying fish skipping, a diving bird) with a pooled splash on every exit and entry.

A small pipeline in the [ambient-world-life](../ambient-world-life/README.md) family. Its Godot component is
[`splash_pool.gd`](../../3d/godot/world_life/splash_pool.gd) (Node3D (with sea_breach.gd)), vendored with the world-life kit:
`python tools/game_music_video.py vendor --module world-life --project <game project>`. See the [example](example.md).

## Pipeline

| # | Step | Detail |
|---|---|---|
| 0 | Vendor | Install the world-life module (kit and components) with a SHA-256 lock per file; don't edit the vendored copies |
| 1 | Arcs | `sea_breach.gd`: `porpoise_height(u, depth, height, leap)` for cycles, `arc_point(from, dir, length, height, u)` for single leaps, `pitch_for`/`yaw_for` to orient. |
| 2 | Splashes | Add one `splash_pool.gd`; call `spawn(at, size)` when the arc crosses the surface (size 1 for a dolphin re-entry, about .4 for a small fish). |
| 3 | Scale | Check model sizes in engine first: a 0.5 m dolphin reads as a speck next to a 9 m ship. |
| 4 | Draw order | On a transparent sea, splashes need `render_priority` above the water (the pool uses 2). |
| 5 | Test and review | A headless test drives the component on a fixed clock; the requester reviews it in play or in a [showcase](../game-asset-showcase/README.md) shot |

## Component

`splash_pool.gd`: `pool_size`, `sound`, `view_range`; `spawn(at, size, with_sound)`; `spawned`. `sea_breach.gd`: `porpoise_height`, `arc_point`, `pitch_for`, `yaw_for`.

The world contract, clock and helpers are in the [world-life kit README](../../3d/godot/world_life/README.md). The
component is exercised by `3d/godot/world_life/tests/components_test.gd` (`tools/tests/test_world_life_godot.py`,
run with `$GODOT` set).

## Checks

| Check | Kind |
|---|---|
| A splash spawns at each surface crossing | automatic |
| Leaps read at 10–30 m in play | human |

## Known limits

- Splashes are particles and a ring; no water displacement.
