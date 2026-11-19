# Characters glance at passing life

Let a character turn their head toward whatever just leapt, landed or flew past (any system calls `KIT.ping`), glancing for a couple of seconds and then resting, so ambient life never pins the gaze.

A small pipeline in the [ambient-world-life](../ambient-world-life/README.md) family. Its Godot component is
[`attention_glance.gd`](../../3d/godot/world_life/attention_glance.gd) (RefCounted helper), vendored with the world-life kit:
`python tools/game_music_video.py vendor --module world-life --project <game project>`. See the [example](example.md).

## Pipeline

| # | Step | Detail |
|---|---|---|
| 0 | Vendor | Install the world-life module (kit and components) with a SHA-256 lock per file; don't edit the vendored copies |
| 1 | Pings | Ambient systems call `KIT.ping(at, strength, seconds)` on events worth a glance: a leap, a landing, a cannon, a note. |
| 2 | Update | Each frame the character's rig calls `glance.update(delta, head_transform, forward, available)`. |
| 3 | Apply | Add `glance.offset()` (yaw, pitch) to the neck and head bones, split about 35/65. Blink or raise the brows when `born` changes. |
| 4 | Tune | `reach`, `max_yaw`, `max_pitch`, `glance_seconds`, `rest_seconds`, `weak`/`near` (weak pings count only up close). |
| 5 | Test and review | A headless test drives the component on a fixed clock; the requester reviews it in play or in a [showcase](../game-asset-showcase/README.md) shot |

## Component

`update(delta, head, forward, available)`, `offset()`, `weight`, `look`, `born`, `glances`; tuning fields as above.

The world contract, clock and helpers are in the [world-life kit README](../../3d/godot/world_life/README.md). The
component is exercised by `3d/godot/world_life/tests/components_test.gd` (`tools/tests/test_world_life_godot.py`,
run with `$GODOT` set).

## Checks

| Check | Kind |
|---|---|
| A ping in front turns the head; it rests after a glance | automatic |
| Head turns read as natural in play | human |

## Known limits

- Bone application is rig-specific and stays in the game.
