# Idle fidgets and visitors for still characters

Give a character who stands still something to do (look around, stretch, yawn …) and, after a while, a small visitor (a butterfly on the snout, a bird that lands and stares, a crab at their feet), so held shots and idle play never look frozen.

A small pipeline in the [ambient-world-life](../ambient-world-life/README.md) family. Its Godot component is
[`idle_scheduler.gd`](../../3d/godot/world_life/idle_scheduler.gd) (RefCounted helper), vendored with the world-life kit:
`python tools/game_music_video.py vendor --module world-life --project <game project>`. See the [example](example.md).

## Pipeline

| # | Step | Detail |
|---|---|---|
| 0 | Vendor | Install the world-life module (kit and components) with a SHA-256 lock per file; don't edit the vendored copies |
| 1 | Lists | Name the fidgets (with durations) and visitors the game can play. |
| 2 | Update | Each frame call `idle.update(delta, still)`; it returns this frame's starts (`fidget`, `visitor`). |
| 3 | Play | Play the fidget's motion using `progress()` (0..1); spawn the visitor's short scene. Moving cancels the fidget. |
| 4 | Tune | `fidget_after`, `fidget_gap`, `visitor_after`, `visitor_gap`. |
| 5 | Test and review | A headless test drives the component on a fixed clock; the requester reviews it in play or in a [showcase](../game-asset-showcase/README.md) shot |

## Component

`fidgets`, `fidget_seconds`, `visitors`, timing fields; `update(delta, still) -> {fidget, visitor}`, `progress()`, `current`.

The world contract, clock and helpers are in the [world-life kit README](../../3d/godot/world_life/README.md). The
component is exercised by `3d/godot/world_life/tests/components_test.gd` (`tools/tests/test_world_life_godot.py`,
run with `$GODOT` set).

## Checks

| Check | Kind |
|---|---|
| A fidget starts after standing still and moving cancels it | automatic |
| Visitors read clearly in a close-up | human |

## Known limits

- The scheduler only times things; the motions and visitor scenes are game code.
