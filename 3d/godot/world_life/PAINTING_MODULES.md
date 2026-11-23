# Painting coverage, sand reveal and companion following

World-life bundle 0.4.0; individual modules 1.0.0. Godot 4 GDScript. No private art,
models, music, dialogue or fur texture is included. These are reusable logic modules;
the game owns their presentation and gameplay policy.

## Painting coverage

`painting_coverage.gd` is a RefCounted pixel-coverage accumulator, usable with either
2D UI or a 3D painting surface. `configure(Vector2i(width,height), labels, colors)`
copies a flat PackedInt32Array: -1 means paper, other values select palette groups.
Invalid configuration returns false without replacing previous state. Treat exposed
groups, marked, counts and totals as read-only; use the methods to change state.

| Method | Behavior |
|---|---|
| dab(point, color, radius=9) | Marks matching pixels once; returns newly changed indices |
| stroke(from, to, color, radius=9, spacing=3) | Interpolated dabs; returns changed indices without duplicates |
| assist(color, threshold=0.85) | Fills that group's remaining pixels after ceil(total*threshold) are marked |
| percent(color) | Rounded integer percentage; empty/invalid group returns zero |
| is_complete() | All paintable groups filled; a blank canvas never auto-completes |
| reset() | Clears coverage/counts while retaining segmentation |

The adapter paints each changed pixel using the original artwork color. It owns
letterboxing, pointer/touch coordinates, invalid/outside strokes, selected color,
segmentation, texture updates, completion signals and helper wording. Use bounded
canvas-space coordinates: stroke sampling work grows with distance/spacing. This
module does not infer palette groups, detect anatomy or copy colors into a texture.

```gdscript
const Coverage = preload("res://addons/gamecore_world_life/painting_coverage.gd")
var coverage = Coverage.new()
coverage.configure(Vector2i(128, 140), pixel_groups, 5)
for index in coverage.dab(canvas_point, selected_color):
    paint.set_pixel(index % 128, index / 128, source.get_pixel(index % 128, index / 128))
```

## Sand reveal

`sand_reveal.gd.sample(age, model_height, footprint=0.34, shrink_time=1.4,
print_time=3.2, ready_time=5.2, base_offset=-0.08)` returns a pure state dictionary:
progress, printing, clip_enabled, local_height, picture_scale, picture_alpha,
picture_visible, animation_ready and follow_ready. Invalid/degenerate settings
return an empty dictionary. Follow starts strictly after ready_time; animation can
start when printing ends. Settings must put ready_time at or after print completion.

The game applies local_height plus its terrain elevation to its shader's clipping
plane, moves the ring to that local height, and scales/fades the picture. The same
sample drives both picture and companion to prevent duplicate timing logic drifting.
`grain(age,index,count,local_height)` returns position and scale for the original
rising spiral. Invalid indices/counts return empty. Consumers choose count and mesh.
The spiral's radial profile and angular/rising rates are currently fixed artistic
defaults. Reuse the envelope independently; if another game needs a different
spiral, review whether to parameterize these values or supply a game-owned effect
sampler. Do not add species or game-name branches to this shared module.

The shader, material assignment, glow, mesh dimensions, creature height, fur normal,
terrain sampling, animation clips and final reveal wording remain game-owned. This
is not a generic shader replacement or a requirement to stop player movement.

## Companion following

`companion_follow.gd.step(position,yaw,leader,home,delta,offset=Vector3(2,0,1),
leash=22,stop_distance=1.3,speed=1.8,turn_rate=5)` returns position, yaw, moving and
returning_home. It operates in XZ, preserving caller Y. Models face -Z. Offset is
world-space; rotate it in the adapter if a game wants leader-relative placement.

If the desired target is outside the home leash, home becomes the target. Inside
the stop distance it holds position. Movement is capped at the remaining distance,
and yaw uses exponential smoothing. `moving` represents movement intent, so zero
delta can return true with unchanged position (matching the original behavior).
Invalid/nonfinite settings return unchanged position/yaw and false flags.

The caller owns terrain height, flying lift, eligibility after reveal, animation
selection, collisions and navigation. Direct following can cross obstacles; do not
use it as an obstacle-aware pathfinder. A game can replace this step with navigation
while retaining the coverage and reveal modules.

## Consumer and validation

ShammyVerse's painting_brush_canvas.gd, painting_animal_friend.gd and
canvas_painting_demo.gd are adapters. Five-color segmentation, Poofy's 85% helping
threshold, 128×140 working canvas, private assets and species settings stay there.
Constants retain the original defaults. The painting module fixture compares the
extraction with legacy brush/reveal/follow formulas and covers reset, threshold,
invalid input, empty groups, phase boundaries, leash, Y preservation and overshoot.
The seven-animal source/exported roster verifies integration separately.

Install with `python tools/game_music_video.py vendor --module world-life --project <game>`.
Search the hub's `reusable_modules` MCP tool with IDs palette-brush,
sand-print-reveal or companion-follow. They are extracted modules, not candidates.
See [dependency and specialization policy](../../../shared/module-specialization.md).
