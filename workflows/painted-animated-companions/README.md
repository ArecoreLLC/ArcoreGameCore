# Painted, animated companions

Status: scaffold; 3D consumers. One consumer so far (ShammyVerse, seven animals, then seven more built model-first on 2026-11-25); see the [worked example](example.md).

Take a part-built, vertex-coloured character with a simple rig and a reference painting, and bring it to a
painted, animated, checked and archived game asset: a texture that matches the painting, clips that walk at the
game's speed without skating, numbers and captures that prove both, and a versioned library entry.

This workflow starts **after** the 2D side. The reference painting, its palette groups and the drawing lesson come
from the [Drawing Atelier animal pipeline](../../tools/drawing-studio/ANIMAL_PIPELINE.md); building the model's
shapes is the consumer's own builder script. Neither is repeated here.

## What GameCore provides

| Piece | Where | Role |
|---|---|---|
| Painting engine | [`3d/blender/companion_studio/painterly.py`](../../3d/blender/companion_studio/README.md) | Charts, atlas, per-texel colour, pigment wash, contact pooling, fibre handling, GLB-ready material |
| Reference renderer | [`3d/blender/companion_studio/reference.py`](../../3d/blender/companion_studio/README.md) | Model-first painting reference: picture, stroke regions and drawing guides projected from the master |
| Motion engine | [`3d/blender/companion_studio/motion.py`](../../3d/blender/companion_studio/README.md) | Pose/Animator, shared tail wave, planted-foot stepper, seated-animal Idle/Walk/Greet |
| Engine lighting | [`3d/godot/painted_companion/`](../../3d/godot/painted_companion/README.md) | Shader include that keeps on-screen colour close to the painted colour |
| Pipeline tool | [`tools/companion_pipeline.py`](../../tools/README.md) | `vendor` (copy with hash lock), `stages`, `validate-glb`; standard library only |
| Review tool | [`tools/companion_review.py`](../../tools/README.md) | `sample`, `palette`, `compare`, `sheet`, `gif`, `paper`; needs numpy and Pillow (`.venv-vision`) |
| Stage list | [`stages.json`](stages.json) | Every stage with inputs, outputs, check and the kind of automation it suits |

The consumer keeps what is its own: the builder, the markings file, per-animal motion settings and any species
routine, the capture scripts that run in its real scene, its gameplay tests, and its engine material.

## Stages

Run `python tools/companion_pipeline.py stages` for the current list. In order:

1. **Vendor** the studio into the game: `python tools/companion_pipeline.py vendor --target <blender scripts folder>/gamecore_companion_studio --godot <game>/addons/gamecore_painted_companion`. Re-run to upgrade; `--check` reports drift.
2. **Sample colours** from the reference: `companion_review.py sample` at named points and `palette` for clusters. Use these values as display sRGB in the markings.
3. **Author markings** as `painter(T)`: functions of rest position that return colour. Place each marking relative to the *model's* landmarks, not the painting's pixels.
4. **Bake** in the build: `painterly.bake(name, version, parts, out_dir, painter, fibers, ellipsoids)` before saving the Blender master and exporting. The image is embedded in the GLB as `painted_albedo`.
4a. **Model-first reference** (optional, when the model exists before any painting): `reference.render(master, out, spec)` in Blender, then `companion_review.py paper colour.png reference.png`. The picture, its drawing guides and its stroke regions all come from the model, so steps 2 and 3 only choose colours and markings for the model itself. A person still approves the look.
4b. **Shape-sketch polish** (after 4a): look at the construction overlay and edit the guide list, then re-render. The code places shapes; this pass decides which shapes teach the drawing. See the table in the [studio README](../../3d/blender/companion_studio/README.md#referencepy).
5. **Engine material**: multiply the texture into albedo and use the painted lighting include. Capture in the real scene and run `companion_review.py compare reference.png render.png --box ...`; tune the include's uniforms until the dominant pigments are within about ±15 per channel.
6. **Rig chains** for tails, trunks, manes and wings where the archetype wants them.
7. **Clips**: `motion.seated_clips(Animator(rig), style, tail)` for seated animals; `Stepper` plus your own routine for others. Give the **game's movement speed**; the stride is derived from it.
8. **Clip report** on the exported GLB (ArcoreAnimate through the hub: `animation_production` → `animate_app` `{"action":"clip_report","path":"<glb>","ground_speed":<speed>}`, or `python mocap/clip_report.py` in the ArcoreAnimate checkout).
9. **Captures**: stills (front, close, three-quarter, back, mid-effect), a pose sheet per clip, a stepped motion preview. `companion_review.py sheet` and `gif` assemble them.
10. **Model check**: `companion_pipeline.py validate-glb <glb> --clips Idle,Walk,Greet --loops Idle,Walk`, and ModelForge `open_model` → `check_model` through the hub.
11. **Game tests** from source, then against the packaged build before release.
12. **Archive** the Blender master and GLB in ModelForge (`import_project_folder`, `update_model`, `verify_file_integrity`); keep status at review.
13. **Approval** by a person.

## Acceptance thresholds

| Check | Pass |
|---|---|
| Painted colour on screen (`compare`) | Each dominant pigment found; worst channel difference ≤ 15, ≤ 20 for the darkest tones |
| Looping clips (`validate-glb`, clip report) | First and last pose equal (gap < 0.5°) |
| Walking speed (clip report `implied_ground_speed`) | Within 5% of the game's movement speed |
| Foot slide (clip report `slide_percent_of_speed`) | ≤ 10% for flat-footed walkers; ≤ 30% for one-bone pendulum limbs, with the reason recorded |
| Ground contact (`lowest_point_below_floor`) | ≤ 1.5% of model height |
| Pops | None in looping clips; each one in a one-shot clip looked at |
| Structure (`validate-glb`, `check_model`) | No errors; expected clips present; every material textured |

These came from one consumer. Tighten or loosen them with evidence from the next.

## What needs which kind of intelligence

`stages.json` is the source; this is the summary. Full reasoning is in each stage's `why`.

| Kind | Stages | Why |
|---|---|---|
| **Procedural** (deterministic code) | sample-colours, bake, model-reference, rig-chains, clip-report, captures, model-check, game-tests, archive | Same inputs, same outputs. No model in the loop. |
| **Algorithmic search** (measure, adjust, repeat) | engine-material, once the shader has the right terms | The palette comparison is a metric, so tuning light, fill and ambient is a search. |
| **Local model is enough** | clips-archetype | Filling settings for an existing routine; the clip report catches bad values. |
| **Frontier multimodal model or a person** | reference, geometry, markings, guide-polish, engine-material the first time, clips-new-motion, visual-review | Reasoning from a posed 2D picture into 3D code, designing motion that does not exist yet, and diagnosing why a render is wrong. |
| **Person** | approval | Publication. |

Three lessons that decide where a frontier model is and is not worth its cost:

- **Measure; do not trust a model's eyes for brightness or motion.** During the first consumer run a frontier model read a rendered face as bright gold when it measured mid-tan, and judged walks from stills that the clip report later showed skating and sinking. Colour goes through `compare`; motion goes through the clip report. Vision is for placement and silhouette.
- **Markings are the expensive stage.** Each animal took a frontier model two to three look-and-fix rounds. A local vision model can list what markings exist; it did not place them correctly on a model whose proportions differ from the painting.
- **Motion design is cheap to check and costly to invent.** Once an archetype exists, a new animal is settings. A new archetype (a crawl, a trunk, wings that trail) is design work.

## Integrations

Agents register only the GameCore hub. Through it:

- **ModelForge** (`model_production`): `blender_run` for builds when the app is open (it finds a project-local Blender), `open_model` + `check_model` for the readiness report, and the archive calls. Start the app with ModelForge's `scripts/ensure-agent.ps1` when it is closed.
- **ArcoreAnimate** (`animation_production`): `animate_app` with `action: "clip_report"` for the numeric clip review. It needs no open case. Use Animate's video-to-rig route when motion should look captured rather than authored.

## Limits

- Evidence is one consumer and one art style (soft watercolour plush). The painting engine assumes part-built meshes with a `Color` attribute; the motion engine assumes one bone per limb under a `Body` bone.
- One-bone limbs have no knees or elbows. The flat-footed stepper keeps standing animals within a few percent of true planting; short pendulum limbs still slide.
- Captures and colour calibration must run in the consumer's real scene; nothing here replaces that.

Use the [shared contract](../../shared/migration-contract.md) for source revisions and acceptance evidence, and the [integration workflow](../game-project-integration/README.md) for asset versions and ownership.
