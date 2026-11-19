# Arrival celebrations

Fire a short confetti salute (three volleys and a synthesised boom) when the player arrives somewhere special, docks, or finishes a task.

A small pipeline in the [ambient-world-life](../ambient-world-life/README.md) family. Its Godot component is
[`celebration_burst.gd`](../../3d/godot/world_life/celebration_burst.gd) (Node3D), vendored with the world-life kit:
`python tools/game_music_video.py vendor --module world-life --project <game project>`. See the [example](example.md).

## Pipeline

| # | Step | Detail |
|---|---|---|
| 0 | Vendor | Install the world-life module (kit and components) with a SHA-256 lock per file; don't edit the vendored copies |
| 1 | Cannons | Place the node and call `add_cannon(position, direction)` per cannon (dock ends, a stage). |
| 2 | Trigger | Call `fire()` on the event (the vehicle's state changing to docking at that port, a quest completing). |
| 3 | Tune | `colors`, `volleys`, `interval`, `boom_db`, `with_barrels`. |
| 4 | Spoilers | Celebrate arrivals and small wins; keep story reveals for the story. |
| 5 | Test and review | A headless test drives the component on a fixed clock; the requester reviews it in play or in a [showcase](../game-asset-showcase/README.md) shot |

## Component

`colors`, `volleys`, `interval`, `boom_db`, `with_barrels`; `add_cannon(at, direction)`, `fire()`; signal `volley(index)`; `fired`.

The world contract, clock and helpers are in the [world-life kit README](../../3d/godot/world_life/README.md). The
component is exercised by `3d/godot/world_life/tests/components_test.gd` (`tools/tests/test_world_life_godot.py`,
run with `$GODOT` set).

## Checks

| Check | Kind |
|---|---|
| fire() produces the volleys and then stops | automatic |
| The boom sits well under the music | human |

## Known limits

- Confetti only; fireworks or streamers are separate effects.
