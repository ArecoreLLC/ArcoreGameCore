# Escorts that follow a vehicle

Have followers (a dolphin pod, small ships, gulls) ride in loose formation around a moving vehicle, join from behind when it gets under way and peel away when it stops.

A small pipeline in the [ambient-world-life](../ambient-world-life/README.md) family. Its Godot component is
[`escort_formation.gd`](../../3d/godot/world_life/escort_formation.gd) (Node), vendored with the world-life kit:
`python tools/game_music_video.py vendor --module world-life --project <game project>`. See the [example](example.md).

## Pipeline

| # | Step | Detail |
|---|---|---|
| 0 | Vendor | Install the world-life module (kit and components) with a SHA-256 lock per file; don't edit the vendored copies |
| 1 | Followers | Instance the followers and list leader-local slots (+Z forward), clear of the hull. |
| 2 | State | Set `active` from game state (for example ship speed above 2.5 m/s, more than 30 m from the berth). |
| 3 | Surface and land | Give `surface` (sea height) and `allowed` (hide over land); `yaw_override` for vehicles that roll. |
| 4 | Extras | Add leaps (`sea_breach.gd`) and splashes (`splash_pool.gd`) per follower; `arrive_now()` for scripted shots. |
| 5 | Test and review | A headless test drives the component on a fixed clock; the requester reviews it in play or in a [showcase](../game-asset-showcase/README.md) shot |

## Component

`leader`, `followers`, `slots`, `join_seconds`, `leave_seconds`, `join_from`, `leave_to`, `wander`, `height`, `active`, `blend`, `yaw_override`, `surface`, `allowed`; `frame()`, `arrive_now()`.

The world contract, clock and helpers are in the [world-life kit README](../../3d/godot/world_life/README.md). The
component is exercised by `3d/godot/world_life/tests/components_test.gd` (`tools/tests/test_world_life_godot.py`,
run with `$GODOT` set).

## Checks

| Check | Kind |
|---|---|
| Followers join while active and hide after leaving | automatic |
| Slots stay clear of the hull and land | human |

## Known limits

- Followers are placed kinematically; they do not collide or avoid each other.
