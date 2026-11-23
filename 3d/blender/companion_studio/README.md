# Companion studio (Blender Python)

Module `gamecore.blender.companion-studio` 1.0.0. Two files that run inside Blender's Python during a
character build. Part of the [painted-animated-companions workflow](../../../workflows/painted-animated-companions/README.md).
Vendor them into a game with `python tools/companion_pipeline.py vendor --target <folder>`; do not import them from this checkout at build time.

## painterly.py

Bakes one painted albedo atlas for a character made of separate parts.

```python
from gamecore_companion_studio import painterly
texture = painterly.bake('Monkey', 'v004', parts, out_dir, painter=my_painter, fibers=fiber_parent, ellipsoids=forms)
```

- `parts`: mesh objects, each with one material and a POINT colour attribute named `Color`. Objects flagged `ob['chart'] = 'sphere'` keep their own UVs; everything else gets a two-sided planar chart across its thinnest axis.
- `painter(T)`: returns display-sRGB colour per texel, or `None` to keep the authored colour. `T` has `name`, `kind` (`fur`, `skin`, `eye`, `nose`, `silk`, read from the material name), `P`/`x`/`y`/`z`, `N`, `base`, the part's bounding `c` and `r`, `seed`, and `k` (set it to scale the pigment wash).
- Helpers for painters: `H` (hex to colour), `S` (smoothstep), `lerp`, `ellipse`, `pool` (pigment at the edge of a wash), `jag` (ragged fur edge), `vnoise`, `wash`.
- `fibers`: `{fibre object name: surface object or None}`. Fibres keep vertex colour, painted from the surface they grow on, and point at a white texel, so `texture × vertex colour` is right for both.
- `ellipsoids`: `(object, centre, radii, name)` of large forms; pigment pools where they meet. `crease_skip` names forms to leave out.
- `size` (default 2048), `detail(object)` for texel density.
- Returns `{image, size, charts, texels_per_unit, coverage}`. The image is saved as `painted_albedo.png`, packed into the `.blend` and wired as `texture × colour attribute` into Base Colour.

## motion.py

Keyframes clips on an armature from pose functions.

```python
from gamecore_companion_studio import motion
an = motion.Animator(rig)                                  # 30 fps, keys from frame 0, NLA tracks
motion.seated_clips(an, {'speed': 1.8, 'pitch': 30, 'greet_arms': 'LR'}, tail={'side': 3.2, 'lag': .1})
an.rest_pose()
```

- Poses are in armature axes (X side, −Y forward, Z up, degrees). `Pose.r/m/s` accumulate rotation, translation and scale per bone; missing bones are skipped.
- `tail_wave(pose, t, chain, ...)`: one travelling wave for any tail, mane or similar chain; the settings are the personality.
- `Stepper(an, limbs, pitch, lift, step_height, max_swing, foot_radius, flat_feet)`: planted feet for one-bone limbs under a `Body` bone. `stride_half(speed, seconds, stance)` gives the reach from the game's movement speed. `flat_feet=True` centres the stride where the foot rests flat (standing animals); `False` swings like a pendulum (short plush limbs).
- `seated_clips(an, style, tail)`: Idle, Walk and Greet for a seated animal with `Body`, `Head`, `Arm.L/R`, `Foot.L/R` and optional `Eye.*`, `Ear.*`, `Tail(.n)`. `SEATED_DEFAULTS` lists every setting; `idle_extra(pose, t)` adds a species gesture.
- `quadruped_legs(...)`: drive four legs from phases (trot or four-beat walk).

The math (`stride`, `stride_half`, `limb_geometry`, `planted`, timing helpers) imports without Blender and is unit-tested in `tools/tests/test_companion_pipeline.py`.

## Reuse review (2026-11-23)

- **Responsibility:** per-texel painted albedo for part-built meshes; pose-function clip baking with shared tail and planted-step behaviours. Inputs are mesh parts, a painter, a rig and settings; outputs are an image, materials and NLA clips. Blender 5.2 Python.
- **Coupling inspected:** no game names, asset paths, species or palettes in either file. Assumptions that are contracts, not accidents: a `Color` attribute, material kind read from the material name, bones named `Body`, `Head`, `Arm.*`, `Foot.*`, `Eye.*`, `Ear.*`, `Tail(.n)`, animals facing −Y.
- **Different use tried:** the unit tests exercise the stepper and packing with synthetic limbs and sizes. That is synthetic evidence, not a second game.
- **Boundary:** engine here; markings, per-animal settings, species routines (elephant, unicorn, butterfly in the first consumer), builders and capture scripts stay in the game.
- **Decision:** `extract-adapter`. Consumer adapter: ShammyVerse `Design/Characters/CanvasCompanions/` (`painterly.py`, `animate.py`, `paintings.py`).
- **Limits:** one consumer, one art style, one-bone limbs, Blender 5.2.3 only.
