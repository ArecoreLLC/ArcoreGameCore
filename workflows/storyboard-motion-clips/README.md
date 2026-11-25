# Storyboard to animation clips

Status: scaffold; 3D consumers. One consumer so far (ShammyVerse, Poofy's four swim clips); see the [worked example](example.md).

Take a rigged, versioned character and a storyboard of moves it has no clips for, and bring it to a new model
version that carries those clips, a controller in the game that plays them, and numbers and captures that show
both. It is for moves with no reference video to read back: looping cycles (swim, hover, climb, idle variants) and
poses far from any frame the motion-capture path was seeded on.

The clips are authored by ArcoreAnimate (`docs/MOTION_PACKS.md` in its checkout) as a **motion pack**: the
moves stated on the rig's own joints as waves and keys. GameCore routes to it; the pack format, the limits check
and the reviews are Animate's and are not repeated here. Motion captured from video stays on Animate's tracking
path; walks that must plant feet stay with the [painted companions](../painted-animated-companions/README.md)
stepper.

## What each system owns

| Piece | Owner | Role |
|---|---|---|
| Motion pack, storyboard beside it | ArcoreAnimate `motions/<name>/` | The source of the clips |
| `author_clips`, `pose_sheet`, `clip_report` | ArcoreAnimate, through the hub's `animation_production` → `animate_app` | Build the model with clips; draw it; review it in numbers |
| Joint-limit profile | ArcoreAnimate, beside the case that calibrated it | The angle ranges the build is held to |
| Model versions | ArcoreModelForge, through `model_production` | The new GLB as the next version, with its evidence |
| Controller, effects, tests, captures | The game | When each clip plays, at what speed, and what proves it |

## Stages

1. **Read the storyboard into moves.** One clip per panel: name, loop or one-shot, what each part of the body does,
   and what the game will do with it (which state plays it, at what speed). Decide what the clip carries and what the
   controller adds: a swimmer's attitude in the water belongs in the clip; climbing or turning belongs to the game.
2. **Find the latest model** in ModelForge (`list_models`, `get_model`) and confirm the game ships the same file by
   SHA-256. Author on that file, never on a copy of unknown origin.
3. **Learn the rig's axes** from its existing clips before writing angles: which axis flaps a wing, which bends a
   knee, how far the authored clips already go.
4. **Write the pack** and **build**: `animate_app` `{"action":"author_clips","pack":…,"path":<model>,"out":<next version>}`.
   The build is refused while any joint leaves its limits; fix the pack, do not widen the limits to pass.
5. **Look**: `{"action":"pose_sheet","path":<out>,"out":<png>}` against the storyboard, panel by panel.
6. **Measure**: the build report, or `{"action":"clip_report","path":<out>,"heading":[tail joint, head joint]}` for
   swimmers (`"ground_speed"` for walkers). Loops must close; a stroke meant to propel must push forward.
7. **Game controller**: load the new version, map states to clips, set playback from the game's speeds, add what the
   storyboard asks of the world (bubbles, wake, camera). Keep the old clips and controls working.
8. **Game tests** from source: every state reaches its clip, limits hold (depth, respawn, floor), land behaviour
   is unchanged. Run the game's existing suites that touch the same controller.
9. **Captures** in the real scene with the game's shaders: one still per panel and a motion preview.
10. **Archive** the new GLB in ModelForge as the next version with a note naming the pack and its parent version;
    record the clip checks as evidence. Keep status at review.
11. **Approval** by a person, on the motion preview.

## Acceptance thresholds

| Check | Pass |
|---|---|
| Joint limits (build report `problems`) | None; the build wrote the file without `--allow-problems` |
| Looping clips (`closes_as_loop`, `loop_gap`) | Gap 0.0° for clips made of whole cycles |
| Pops | None in looping clips |
| Propelling strokes (`water.forward_share`) | Clearly positive; a negative share is rowing backward and is a defect |
| Existing clips | Present and unchanged in the new version; mesh and skin unchanged (same triangle count, same joints) |
| Game states | Each storyboard panel's clip is reached by play, shown by a test |
| Existing behaviour | The game's suites that touch the controller still pass |

These came from one consumer. Tighten or loosen them with evidence from the next.

## What needs which kind of intelligence

| Stage | Suits |
|---|---|
| Storyboard into moves; what the clip carries and what the game adds | Judgment, with the person who drew the storyboard |
| Rig axes, pack numbers, build, reports | An agent with the Animate tools; deterministic once written |
| Pose sheet against the storyboard | An agent that can read images, then a person |
| Controller and tests | An agent working in the game's code |
| Whether it feels right in motion | A person, on the preview |

## Limits

A motion pack is waves and keys on joint angles: no inverse kinematics, contact or collision solving. The swimming
review is pressure drag only and is for comparing clips, not for predicting speed. Nothing here approves an
animation; it produces the evidence a person approves on.
