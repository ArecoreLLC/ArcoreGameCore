# Terrain clearance and timed cue cursor

World-life bundle 0.5.0; both modules 1.0.0, Godot 4 GDScript.
Install using `python tools/game_music_video.py vendor --module world-life --project <game>`.
Use MCP `module_search` with keys `procedures:reef-clearance` or
`procedures:lyric-world-cues` and `details: true` to inspect canonical entries.

## Terrain ring clearance

`terrain_ring_clearance.gd.clear(home, radius, margin, height_at, samples=32)`
returns whether a horizontal ring and its center clear a sampled height field.
`height_at(x,z)` is a caller-owned Callable returning a finite number. The ring's
radius is radius+margin, and terrain must be at or below home.y-margin along the
ring, strictly below at the center. This asymmetric equality preserves the original
behavior. Invalid inputs or nonnumeric/nonfinite heights return false. A callback
that throws a script error is not caught; caller code must be valid.

This is discrete sampling, not swept collision detection: obstacles between
samples or inside the ring can be missed. It does not check a water surface or
animal bounds. The consumer owns margins, sample density, surface clearance,
island coordinates, species, placement attempts and visibility/quality rules.
ShammyVerse's reef adapter preserves the original 32 samples and species margins.

```gdscript
const Clearance = preload("res://addons/gamecore_world_life/terrain_ring_clearance.gd")
var usable = Clearance.clear(Vector3(0, 5, 0), 4.0, 0.2, world.height_at, 8)
```

## Timed cue cursor

`timed_cue_cursor.gd` owns only `last_key` and `last_seconds`.
`observe(track: String, seconds, cues: Array, rewind_tolerance=0.5)` returns the
first active new cue index or -1. Cue dictionaries need finite numeric `start` and
`end`, with end>start; other fields are opaque. Intervals include start and exclude
end. Malformed rows are skipped; array order wins overlaps. Changing cue content
under the same track/index requires `reset()` because content is not its identity.

A backward clock jump greater than the tolerance clears duplicate suppression.
Track IDs distinguish cues; a reset clears both fields. Observe every eligible
playing frame, including during cooldown: an observed cue is consumed even if
the game declines to dispatch it. No retry, seek catch-up, clock advancement or
cooldown timer is included. Large forward seeks only observe the current interval.
Callers pause observation when their clock is stopped or presentation is forbidden.

```gdscript
var cursor = preload("res://addons/gamecore_world_life/timed_cue_cursor.gd").new()
var index = cursor.observe("tutorial", elapsed, tutorial_cues)
if index >= 0 and may_show_hint:
    show_hint(tutorial_cues[index])
```

ShammyVerse owns lyric keywords, cooldown durations, actor/story gates, region
checks, effect ownership and cleanup. The helper never moves the player or camera.

## Review and evidence

Both decisions are `extract-adapter`. Pure sampled geometry and interval identity
have clear reusable contracts; game policy does not enter either module.
`tests/route_cue_test.gd` checks 150 old/new terrain comparisons, an elevated ring
with alternate density, invalid samplers, boundary equality, tutorial intervals,
overlap, rewind, track changes and consumption during cooldown. Consumer effects
and real reef tests validate the adapters separately. No second-game or rendered
validation is implied. See [remaining review](REMAINING_REUSE_REVIEW.md).
