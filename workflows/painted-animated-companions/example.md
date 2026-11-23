# Worked example: ShammyVerse Canvas Cay companions

Consumer: ShammyVerse (Godot 4.7.2, Windows, D3D12, ACES tonemap). Subject: seven painting companions built
from ellipsoids and swept tubes with vertex-coloured regions and 11–20 bone rigs. Date: 2026-11-23. Blender 5.2.3.
This is one consumer's evidence, not a second-game validation.

## What was run

| Stage | In ShammyVerse | Result |
|---|---|---|
| Vendor | `Design/Characters/CanvasCompanions/gamecore_companion_studio/` (+ lock), `game/addons/gamecore_painted_companion/` | Studio 1.0.0 pinned by SHA-256 |
| Sample colours | Reference paintings in `Design/Iterations/<animal>-painting-v001/reference/` | 15–25 named samples per animal |
| Markings | `Design/Characters/CanvasCompanions/paintings.py` | One `painter(T)` per animal |
| Bake | `artist.py` (`Artist.save`) and `RedPanda/versions/v004/build_red_panda.py` | 2048² atlas, 35–57 charts, 68–74% coverage |
| Engine material | `game/shaders/sand_animal_reveal.gdshader` includes the painted lighting | Dominant pigments on screen within about ±15 per channel |
| Rig chains | Tail (red panda, cat, monkey, unicorn), six-bone trunk, mane, lower wings and antennae | Weights normalised |
| Clips | `CanvasCompanions/animate.py`: settings for four seated animals, routines for elephant, unicorn, butterfly | Idle, Walk or Fly, Greet on all seven |
| Clip report | ArcoreAnimate `mocap/clip_report.py` | Table below |
| Captures | `review_painted.gd`, `review_animation.gd`, `record_animation_frames.gd` in the real island scene | Stills, pose sheets, motion previews |
| Model check | `validate-glb`, ModelForge `check_model` | No errors |
| Game tests | `painting_roster_test.gd` (85 assertions), `canvas_painting_demo_test.gd`, greet-flow test | Pass from source |

## Measured walks

Game movement speed is what the catalog gives each animal. Implied speed and slide are from the clip report.

| Animal | Stepper mode | Game speed | Implied speed | Foot slide | Lowest point below floor |
|---|---|---|---|---|---|
| Unicorn | flat-footed | 1.8 | 1.80 | 2% | 0.2% of height |
| Elephant | flat-footed | 1.4 | 1.43 | 6% | 0.2% |
| Cat | pendulum | 1.8 | 1.85 | 13% | 1.0% |
| Red panda | pendulum | 1.8 | 1.80 | 19% | 1.2% |
| Monkey (crawl) | pendulum | 1.8 | 1.81 | 29% | 0 |
| Koala | pendulum | 1.2 | not measured | not measured | 0 |

The koala's steps are too low for the report's automatic foot finder; pass `contacts` to measure it.

Before the stepper existed, the same report on the first hand-tuned walks showed the monkey's crawl implying
almost no forward travel, paws sinking 3.4% of body height, and hind feet on the seated animals sliding at more than
half the walking speed. None of that was visible in the pose sheets that had been reviewed and accepted.

## What the run taught

- The reference painting and the final 2D artwork drawn in the game share colours, so sampling the reference was enough.
- The existing light function multiplied albedo twice and the sky ambient lit tops far more than fronts; both had to be understood before any constant could be tuned. That diagnosis is why `engine-material` is marked frontier-model the first time and algorithmic afterwards.
- Stride length must come from the game's movement speed. Choosing a swing angle by eye produced walks that covered half the ground the game moved them.
- A foot touches the ground below the bone's tail. Sizing the swing to the bone instead of the contact made every paw travel a third too far.
- A stepped capture at 15 frames per second and a five-moment pose sheet are useful for whether a pose reads. They are not evidence about skating, loop closure or speed.

## Not covered by this run

No second engine or second game. No knees or elbows. No captured (video-tracked) motion. The packaged Windows build
was not re-exported during the run, so packaged-build tests were not repeated.
