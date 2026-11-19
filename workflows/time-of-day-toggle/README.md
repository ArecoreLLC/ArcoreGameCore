# Day, dusk and night

Offer Day, Dusk and Night as a player toggle and a scripted mode, easing the sun, sky and ambient light, with a moon, stars and moonlight, and publishing `KIT.night` so lanterns, fireflies and glowing sea life respond.

A small pipeline in the [ambient-world-life](../ambient-world-life/README.md) family. Its Godot component is
[`time_of_day.gd`](../../3d/godot/world_life/time_of_day.gd) (Node3D), vendored with the world-life kit:
`python tools/game_music_video.py vendor --module world-life --project <game project>`. See the [example](example.md).

## Pipeline

| # | Step | Detail |
|---|---|---|
| 0 | Vendor | Install the world-life module (kit and components) with a SHA-256 lock per file; don't edit the vendored copies |
| 1 | Add | Add `time_of_day.gd` with `world` (or `sun` and `environment`) and an optional `toggle_key`. |
| 2 | React | Night-aware systems read `KIT.night` (0..1): emission on lanterns and jellyfish, fireflies, a glowing wake. |
| 3 | Script | Cutscenes and showcases call `set_mode(mode, instant)`. |
| 4 | Decide | Whether the game gets a full day-night cycle is a design decision; this pipeline stops at a toggle. |
| 5 | Test and review | A headless test drives the component on a fixed clock; the requester reviews it in play or in a [showcase](../game-asset-showcase/README.md) shot |

## Component

`world`, `sun`, `environment`, `toggle_key`, `ease_per_second`, `moon_direction`; `set_mode(mode, instant)`, `cycle()`; signal `mode_changed(mode)`; writes `KIT.night`.

The world contract, clock and helpers are in the [world-life kit README](../../3d/godot/world_life/README.md). The
component is exercised by `3d/godot/world_life/tests/components_test.gd` (`tools/tests/test_world_life_godot.py`,
run with `$GODOT` set).

## Checks

| Check | Kind |
|---|---|
| Night mode sets KIT.night to 1 and day restores the sun | automatic |
| The world stays readable at night | human |

## Known limits

- The ocean or terrain shaders may need their own night parameters; the toggle only drives the light, sky and KIT.night.
