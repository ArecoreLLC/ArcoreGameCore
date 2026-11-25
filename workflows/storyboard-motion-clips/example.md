# Worked example: Poofy and Plumpy swim in ShammyVerse's Coral Deep

Consumer: ShammyVerse (Godot 4.7.2, Windows). Subjects: Poofy, the hero (36 joints, five clips, 94,329 triangles), and
his shoulder companion Plumpy (18 joints, two clips). Date: 2026-11-23. Two storyboards of four panels each. This is
one consumer's evidence, not a second-game validation, and no person has approved the motion yet.

## What was run

| Stage | In ShammyVerse and ArcoreAnimate | Result |
|---|---|---|
| Storyboard into moves | Poofy: plunge, wing strokes, doggy-paddle, glide. Plumpy: grip, paddle, bubble helmet, shake-off | Seven clips; the shake-off stayed the game's existing additive shake |
| Latest model | ModelForge `get_model` for Poofy and Plumpy | Poofy version 30 and Plumpy version 12 matched the game's files by SHA-256 |
| Rig axes | Poofy's `Flight` clip sampled in model axes | Wings flap about model Y, -34° to +46° on the left wing; Plumpy's bones all share the model's axes |
| Packs | `ArcoreAnimate/motions/poofy-swim/pack.json`, `motions/plumpy-ride/pack.json` | Poofy held to his joint-limit profile plus pack limits for wings, tail and feet; Plumpy to pack limits only |
| Build | `author_clips` | Poofy v014 (about 4 s) and Plumpy v007; Poofy's rebuild was byte-identical |
| Pose sheets | `pose_sheet` | Four clips at six moments in about 9 s |
| Game | `hero_swim.gd`, `poofy_swim_bubbles.gd`, `plumpy_swim_ride.gd` and small changes to `hero.gd` and Plumpy's scripts | Ctrl dives, Space swims up, letting go glides; Plumpy's beat follows Poofy's state |
| Game tests | `game/tests/poofy_dive_test.gd` | 71 checks pass headless |
| Existing suites | Full fresh route (`gameplay_end_to_end.gd`), Coral Deep, camera polish, wing clearance, sea life | 356, 33 and 18 checks with 0 failures; the last two pass |
| Captures | Stills per panel and a 27 s preview recorded with Godot's movie writer | `Design/Levels/CoralDeep/poofy-swim/` |
| Archive | ModelForge `import_files`, `create_design_iteration`, `record_quality`, `verify_file_integrity` | Poofy version 32, Plumpy version 13, hashes verified |

## Measured clips

From the build reports. Share and speed are the swimming review's; Plumpy rides, so his clips have none.

| Clip | Length | Loop gap | Pops | Fastest joint | Forward share | Implied swim speed |
|---|---|---|---|---|---|---|
| Poofy `SwimDive` | 1.2 s | 0.0° | 0 | arm, 456°/s | 2% | 0.11 units/s |
| Poofy `SwimStroke` | 1.6 s | 0.0° | 0 | wing, 185°/s | 12% | 0.43 units/s |
| Poofy `SwimPaddle` | 1.5 s | 0.0° | 0 | forearm, 397°/s | about 0 | 0 |
| Poofy `SwimGlide` | 3.0 s | 0.0° | 0 | tail tip, 30°/s | about 0 | 0 |
| Plumpy `RideGrip` | 0.8 s | 0.0° | 0 | wing, 236°/s | | |
| Plumpy `RidePaddle` | 0.8 s | 0.0° | 0 | wing, 679°/s | | |
| Plumpy `RideBubble` | 3.0 s | 0.0° | 0 | head, 41°/s | | |

Both new models hold everything their parent version held, byte for byte: meshes, skin, joints and existing clips.

## What the checks caught

| Check | What it caught | What was done |
|---|---|---|
| Joint limits | An arm in the plunge at 552°/s against a 520°/s pack limit; Plumpy's paddling limbs past 760°/s | Amplitudes lowered; both builds had been refused |
| Swimming review | The first wing stroke rowed Poofy backward: the wing twist had the wrong sign | Twist reversed; the share went from negative to +12% |
| Swimming review | The doggy-paddle pushes about nothing: his paws are small beside his wings | Kept as drawn ("frantic"), and the game moves it slower than the wing stroke |
| Tracks left at rest | Poofy's toes: the walk curls them, the swim clips did not touch them, so a walking toe pose would have stayed through the swim in Godot | Toes animated in all four clips; v014 rebuilt |
| Pose sheet | Plumpy's eyes bulged before his blink: the key curve overshot between two long holds | Animate's key curves made overshoot-free |
| Game test | The glide never happened: the hero's ground braking stopped him in a fraction of a second | The dive keeps its own momentum |
| Game test | Diving in the shallow sea overshot the depth limit and respawned him | Braking before the floor |
| Captures | The surface paddle sat on top of the water: the clip turns him about his middle, the game floated his feet | The game lowers the paddling body by 0.5 m; a test checks head out, chest under |
| Captures | Turning the game camera for a still also turned the direction the held keys steered | Captures use a camera of their own |

## What it showed about the workflow

- Agree where the clip turns the body before writing the controller. Clips that carry their own attitude must
  turn about the middle of the game's collision shape, and the game must then turn any extra lean about the same
  point; otherwise the body swings off its capsule or floats at the wrong height.
- A controller built for the ground has assumptions a swimmer breaks (braking, a floor to stand on, a fixed
  respawn height). Tests for each state found them faster than play did.
- The numbers earned their place on the cases a still cannot show: a stroke rowing backward, a pose that would
  leak across a clip change.
- A small rider only reads close up. Plan the preview camera around the companion's beats, not just the hero's.

## Not done

- No person has reviewed the motion. Status in ModelForge stays `wip`.
- Poofy's arms can pass through Plumpy in the plunge; wings can pass through arms. Nothing solves contact.
- No swimming sounds beyond the existing splash and Plumpy's chirps; no air limit.
- Exported builds were not made; the new GLBs follow the same import settings as their parents.
- The second storyboard was given in conversation and is not stored beside its pack.
