# Companion studio (Blender Python)

Module `gamecore.blender.companion-studio` 1.1.0 (1.1.0 added `reference.py`). Three files that run inside Blender's Python during a
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

## reference.py

Renders a finished master as the picture a player paints, so the painting and the character cannot disagree.

```python
from gamecore_companion_studio import reference
reference.render('Lion_v001.blend', 'out/lion', {
    'guides': [{'name': 'head', 'stage': 0, 'match': [r'^Big cat head']},
               {'name': 'leg', 'stage': 1, 'mode': 'each', 'match': [r'^Cat leg', r'^Big paw']},
               {'name': 'tail gesture', 'stage': 0, 'mode': 'chain', 'match': [r'^Tail\.']}],
    'regions': [(r'^Crest', 'head')], 'hide': [r'^REVIEW_'], 'azimuth': 35})
```

- Writes `colour.png` (transparent film, soft light), `regions.png` (each part filled by its drawing-order region: ears, head, face, body, tail, paws) and `projection.json` (camera, model height and radius, the region of every part, and the guides in 0..1 picture coordinates).
- Guide modes: `ellipse` (one outline round all matching parts), `each` (one per bone carrying matching parts, or `by='side'` / `by='part'`), `bones` (one outline per bone group of a one-piece mesh: feet, arms, beads down a tail), `chain` (a line along matching bones: tails, wing spines), `axis` (a line between two groups), `cross` (face centre line and eye line curved over the head, which fixes a three-quarter view).
- Shape options: ellipses fit the shape's area moments by default, so they hug a torso instead of reaching its furthest corner (`fit='extent'` for the old bounds, `grow` to scale); `corners=N` draws a wedge (beak, crest, tail fan, bat wing); `under=[...]` keeps only what hangs below another group, so legs start at the belly line; `far_light` marks limbs on the side away from the camera and `light` marks any guide, as `"light": true` in `projection.json` for the consumer to draw faintly.

What the code does and what is left for a second look (from the ShammyVerse shape-sketch review, 2026-11-25):

| Procedural (in `reference.py`, driven by the guide list) | Second-pass polish (frontier model or person looking at the overlay) |
|---|---|
| Tight fit of every oval to its parts | Deciding a correct oval is still too big for the lesson and trimming it (`grow`) |
| Face cross-lines for head tilt | Choosing which small features are worth a shape at all |
| Legs cut at the belly line, separate paw or foot circles | How far each leg should climb, a slight front/hind slant, nudging a far leg apart so two ovals do not merge |
| Wing spines along the bones; wing, beak, crest and fan wedges | Whether a wedge reads as that thing (a bat wing with scalloped edge, a swept-back fan) and how many corners it needs |
| Shapes for feet, arms and tail beads on a one-piece mesh; bone chains drawn as one smooth curve | Dropping a shape that is hidden behind another (a tail bead behind a hip) |
| Far-side limbs and step 1 marked light | Order of drawing within a step; what to leave out when shapes knot together |
| Re-render after any change | Approval |
- Regions: `REGION_RULES` matches part names; a spec's `regions` are tested first against `name|material|dominant bone`, which is how a model not built from named ellipsoids (ShammyVerse's NightLight dragon) is classified.
- `region_lookup(regions.png)` returns `region(u, v)` for stroke timing; it and the constants import without Blender.
- `python tools/companion_review.py paper colour.png reference.png --seed N` adds the watercolour paper finish and keeps model pixels below paper white, so palette builders do not read pale fur as bare paper.
- Evidence: seven ShammyVerse animals on 2026-11-25. After the move from the game into this module, four of seven references were byte-identical to the game's own version; the other three had been rebuilt in between. Not tried: another engine's consumer, non-Blender masters, perspective views.

The math (`stride`, `stride_half`, `limb_geometry`, `planted`, timing helpers) imports without Blender and is unit-tested in `tools/tests/test_companion_pipeline.py`.

## Reuse review (2026-11-23)

- **Responsibility:** per-texel painted albedo for part-built meshes; pose-function clip baking with shared tail and planted-step behaviours. Inputs are mesh parts, a painter, a rig and settings; outputs are an image, materials and NLA clips. Blender 5.2 Python.
- **Coupling inspected:** no game names, asset paths, species or palettes in either file. Assumptions that are contracts, not accidents: a `Color` attribute, material kind read from the material name, bones named `Body`, `Head`, `Arm.*`, `Foot.*`, `Eye.*`, `Ear.*`, `Tail(.n)`, animals facing −Y.
- **Different use tried:** the unit tests exercise the stepper and packing with synthetic limbs and sizes. That is synthetic evidence, not a second game.
- **2026-11-25 addition:** `reference.py` holds no game names; guide groups, overrides and camera come from the consumer's spec (ShammyVerse `CanvasCompanions/wild_specs.py`). The default `REGION_RULES` words (mane, pom, plume) grew from that one roster and are data, replaceable with `rules`.
- **Boundary:** engine here; markings, per-animal settings, species routines (elephant, unicorn, butterfly in the first consumer), builders and capture scripts stay in the game.
- **Decision:** `extract-adapter`. Consumer adapter: ShammyVerse `Design/Characters/CanvasCompanions/` (`painterly.py`, `animate.py`, `paintings.py`).
- **Limits:** one consumer, one art style, one-bone limbs, Blender 5.2.3 only.
