# Godot world-life kit

`world_life_kit.gd` (version 0.1.0) and `sea_breach.gd` are the Godot 4 runtime of the
[ambient-world-life workflow](../../../workflows/ambient-world-life/README.md): the shared helpers under a game's
ambient creatures, weather and props. A game writes its own modules (which creatures, where, when) on top of the kit.

Install them with `python tools/game_music_video.py vendor --module world-life --project <game project>`. That
copies both files to `addons/gamecore_world_life/` with a SHA-256 lock per file. Don't edit the vendored copies;
change GameCore and vendor again.

## World contract

Every placement helper takes the game's world node:

| Member | Required | Meaning |
|---|---|---|
| `height_at(x, z) -> float` | Yes | Terrain height; water lies below 0 |
| `wave_at(Vector2, seconds) -> float` | No | Sea surface offset; without it the sea is flat at y = 0 |
| `ocean_elapsed: float` | No | The clock `wave_at` uses; defaults to `KIT.time` |

The game owns one root node that advances `KIT.time` in `_process` (so the clock follows game time, also under
Movie Maker), calls `KIT.reset()` on load, and may set `KIT.effects_volume` to a Callable that returns the effects
volume (0–1, or negative while sounds are off). Static members outlive the scene: clear `effects_volume` in the
root's `_exit_tree()` (a callable that holds scene nodes otherwise crashes Godot on exit).

## What the kit provides

| Area | Members |
|---|---|
| Meshes | `merge([[Mesh, Transform3D, Color], …])` bakes primitive parts into one vertex-coloured mesh (one draw call per creature part); `xf()`, `sphere_mesh()`, `box_mesh()`, `cyl_mesh()`, `instance()`, `quiet()` (no shadows, visibility range) |
| Materials | `mat()` and `vcol()` (cached; transparent ones draw after a transparent sea with `render_priority` 2), `shader()` cache, `flutter_material()` (cloth pinned at UV.x = 0: flags, bunting, sails, towels, kite tails) |
| Placement | `surface()`, `deep()`, `shore(world, center, angle, inland)` (march out from an island centre to the waterline), `camera()`, `ahead(camera, distance, angle)` |
| Attention | `ping(at, strength, seconds)` when something worth a glance happens; `best_ping(from, forward, reach)` returns the strongest recent ping in front. Characters turn their heads toward it; glance for about 2.5 s, then rest, so ambient life never pins a gaze |
| Night | `KIT.night` (0 day … 1 night), set by the game's time-of-day node; lanterns, fireflies and glowing sea life read it |
| Beat clock | `beat_phase`, `beat_index`, `on_beat`, `bpm`; the game sets them from the playing song and a [beat map](../../../tools/song_beats.py). `song_clock(id, seconds)` lets a recorder drive them from the video clock |
| Sound | `tone(freqs, seconds, decay, gain, noise)` synthesises a one-shot (notes, drums, chimes, cannon booms) at load time; `play_at(node, stream, at, db, pitch)` plays it positionally at the effects volume |
| Birds | `bird(body, wing, size)` builds a bird with wing pivots; `flap(node, t, amount, speed)` flaps it, or any model with `WingL`/`WingR` parts |
| Leaps (`sea_breach.gd`) | `porpoise_height()`, `arc_point()`, `pitch_for()`, `yaw_for()` for anything that jumps out of the sea |

## Conventions for modules built on the kit

- **Near the camera, not everywhere.** Keep a small active set within about 80 m of the camera and hide the rest.
- **Nonblocking.** No collision with the player or vehicles.
- **Spoiler-safe.** Ambient life never shows rewards, finished objectives or story characters out of place.
- **A `stage(kind)` method** puts the module's event in front of the camera now. Recorders call it for held
  shots, beats and lyric cues; tests call it too.
- **`set_quality(level)`** trims the costly parts at low quality.

## Validation

`tools/tests/test_game_music_video.py` checks the world-life vendoring and its lock. The GDScript is exercised by the
consuming game's tests (ShammyVerse `game/tests/world_life_test.gd`). There is no GameCore-side Godot test project.
