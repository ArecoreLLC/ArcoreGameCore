# Musical stones and chimes

Turn objects (standing stones, bells, flowers) into an instrument: each sings a pentatonic note when the player passes, and several in a row sing a chord.

A small pipeline in the [ambient-world-life](../ambient-world-life/README.md) family. Its Godot component is
[`proximity_notes.gd`](../../3d/godot/world_life/proximity_notes.gd) (Node3D), vendored with the world-life kit:
`python tools/game_music_video.py vendor --module world-life --project <game project>`. See the [example](example.md).

## Pipeline

| # | Step | Detail |
|---|---|---|
| 0 | Vendor | Install the world-life module (kit and components) with a SHA-256 lock per file; don't edit the vendored copies |
| 1 | Objects | Place the objects (an arc along a shore works well) and list them in `objects`. |
| 2 | Notes | Leave `notes` empty for C-major pentatonic, or set frequencies. Sounds are synthesised at load time. |
| 3 | Feedback | Connect `sang(index)` to a glow or ring and `chord_played()` to a bigger effect. |
| 4 | Tune | `radius`, `cooldown`, `chord_count`, `chord_window`, `volume_db`. |
| 5 | Test and review | A headless test drives the component on a fixed clock; the requester reviews it in play or in a [showcase](../game-asset-showcase/README.md) shot |

## Component

`player`, `objects`, `notes`, tuning fields; `sing(i)`, `chord()`; signals `sang(index)`, `chord_played()`; `played`, `chords`.

The world contract, clock and helpers are in the [world-life kit README](../../3d/godot/world_life/README.md). The
component is exercised by `3d/godot/world_life/tests/components_test.gd` (`tools/tests/test_world_life_godot.py`,
run with `$GODOT` set).

## Checks

| Check | Kind |
|---|---|
| Passing three objects quickly plays a chord | automatic |
| Notes and chord sound pleasant at the effects volume | human |

## Known limits

- One scale per group; harmony beyond a single chord is game code.
