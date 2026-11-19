# Boost gates along a route

Place striped gates along a travel route (peppermint wind lanes, ring courses); passing through one sparkles and fires `passed(index)` so the game can give a burst of speed.

A small pipeline in the [ambient-world-life](../ambient-world-life/README.md) family. Its Godot component is
[`route_gates.gd`](../../3d/godot/world_life/route_gates.gd) (Node3D), vendored with the world-life kit:
`python tools/game_music_video.py vendor --module world-life --project <game project>`. See the [example](example.md).

## Pipeline

| # | Step | Detail |
|---|---|---|
| 0 | Vendor | Install the world-life module (kit and components) with a SHA-256 lock per file; don't edit the vendored copies |
| 1 | Route | Choose the route's ends (for example two harbours) and `allowed(point)` (deep water at the centre and both posts). |
| 2 | Build | Set `spacing`, `margin`, `half_width`, colours, then `build(from, to)`. |
| 3 | Boost | Connect `passed(index)` to the vehicle: a short speed multiplier that decays (ShammyVerse: `ship_voyage.gd` `boost`), a whoosh and a ping. |
| 4 | Weather | Optionally add lane weather (snow, ribbons) while inside the route. |
| 5 | Test and review | A headless test drives the component on a fixed clock; the requester reviews it in play or in a [showcase](../game-asset-showcase/README.md) shot |

## Component

`spacing`, `margin`, `half_width`, `post_height`, `stripe_a`, `stripe_b`, `view_range`, `vehicle_position`, `allowed`; `build(from, to) -> count`; signal `passed(index)`; `passes`.

The world contract, clock and helpers are in the [world-life kit README](../../3d/godot/world_life/README.md). The
component is exercised by `3d/godot/world_life/tests/components_test.gd` (`tools/tests/test_world_life_godot.py`,
run with `$GODOT` set).

## Checks

| Check | Kind |
|---|---|
| Passing a gate fires once, then cools down | automatic |
| The boost feels fair and does not skip the route's content | human |

## Known limits

- Straight routes between two points; curved courses need several `build` calls.
