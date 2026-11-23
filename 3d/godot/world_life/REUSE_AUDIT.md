# ShammyVerse reusable procedures audit — 2026-11-22

Scope: Godot 4 / 3D, ambient-world-life workflow, plus adjacent art and capture
utilities. Static procedure inventory is consumer-owned; no private models, drawings,
music or character dialogue are copied into GameCore. Existing modules are reused,
not reimplemented. Other-engine parity is not claimed.

The machine-readable [reuse registry](../../../shared/reusable-modules.json) is
available through the GameCore hub's `reusable_modules` MCP tool. Filter by query,
id or status. `extracted` means reusable source is installed and exercised by the
consumer; `existing` means previously shared; `candidate` means still consumer code,
with extraction work required. It does not mean every catalog entry is portable.

## Butterfly findings and extraction

Before this audit, the consumer's butterfly_species.gd held a 12-entry GDScript
array of names, origin dialogue, base/edge/spot colors and five pattern styles.
The ambient creatures are 3D GLB instances, not Sprite2D nodes. A separate painted
butterfly companion uses a skinned model; it is not the ambient species system.

The species array now lives in the consumer's `game/data/butterfly-species.json`.
Names, ordering, text, colors and Glasswing alpha are preserved. JSON uses schema
`gamecore.wing-species.v1`: `species` entries require name/from, base/edge/spot as hex
or four RGBA channels, and integral pattern 0..4. Species dialogue and educational
claims remain game-owned; this extraction does not fact-check that wording.

| Shared file | Contract | Consumer usage |
|---|---|---|
| wing_patterns.gd | Load/validate JSON and apply parameterized materials to WingL/WingR and Body; five visual patterns | Species adapter passes game-owned data and model |
| flutter_motion.gd | Deterministic swarm/orbit positions, burst/glide amplitude, approach-perch-depart path | Sky swarm, beach insects and close visitor |
| flutter_swarm.gd | Spawn fixed count once with caller scene/RNG/paint callback; update visibility, position, heading and flap | Five island groups, six butterflies each; placement and attention pings remain game-owned |
| timed_stroke_track.gd | Validate sorted finite [seconds,u,v] samples; binary-search interpolation, pen-up gap hold | Sand painting maps normalized coordinates into its own world transform |

All four are in world-life 0.3.0, installed with the existing vendor command and
per-file hash lock. Source implementations use relative sibling preloads and contain
no private resource paths. Existing functions keep their default numeric behavior.
Wing flapping still uses the existing kit helper; there is no competing flap system.

## Install and use

```powershell
python tools/game_music_video.py vendor --module world-life --project C:/MyGame/game
```

```gdscript
const SWARM = preload("res://addons/gamecore_world_life/flutter_swarm.gd")
const PATTERNS = preload("res://addons/gamecore_world_life/wing_patterns.gd")
var catalog = PATTERNS.read_catalog("res://data/my-species.json")
var flies = SWARM.spawn(self, my_scene, 6, rng,
    func(node, index): PATTERNS.paint(node, catalog[index % catalog.size()]))
# On the caller's clock; hide far-away groups without respawning them:
SWARM.update(flies, center, phase, elapsed, near_camera)
```

Validate nonempty catalog before spawning. Include non-resource JSON explicitly in
Godot export filters. Scene root must be Node3D; wings are named WingL/WingR. These
helpers do not provide obstacle avoidance, collisions, ecology, a full lifecycle
pool manager or skeletal retargeting. For beach rigs, use the motion samples with
the consumer's existing bone poses. Spawn count and asset complexity are caller-owned.

## Other procedures found

Update: [remaining candidate review](REMAINING_REUSE_REVIEW.md) extracts terrain
ring sampling and timed cue observation in 0.5.0. Save rotation, wing correction
and character authoring remain reviewed game-owned candidates with explicit
revisit conditions. [Module search](../../../shared/module-discovery.md) now
federates procedure and portable module discovery without merging installers.

Already shared: merged primitive meshes/material caching, terrain/water placement,
attention pings and glance/rest timing, idle scheduling, beat dance, proximity notes,
escort formations, day/night, chatter, route gates, celebrations, pooled splashes,
music-video clock/camera guard, capture lighting and Drawing Atelier jobs/manifests.
These have registry entries pointing at their existing implementations and guides.

The palette coverage, sand-print envelope and companion follow logic have since been
extracted in world-life 0.4.0; see [painting modules](PAINTING_MODULES.md). The shader,
UI and navigation policy remain consumer-owned. The original findings below describe
the boundaries; consult the live registry for current extraction status.

Original candidate findings:

- Palette paint coverage: separate pixel grouping/brush accumulation from the panel,
  animal labels and difficulty tuning; retain touch and completion behavior tests.
- Sand-print reveal: extract timing/height envelope and effect hooks; inject shader,
  textures, species bounds and movement policy. The current shader uses private fur.
- Companion following: supply target/terrain callbacks, leash/spacing and animation
  events; define obstacle handling before calling it a general navigation controller.
- Reef route clearance: parameterize sampled paths, creature radii and terrain depth;
  current island coordinates and quality selection remain game-owned.
- Lyric-to-world cues: separate word/cue rules, cooldown and effect ownership; do not
  transfer story beats or permit effects to hijack movement/progression.
- Validated save rotation: separate schema validation and slot UX from temp/backup
  writes and recovery. Preserve corrupted-primary recovery and isolated test saves.
- Flight wing clearance: keep candidate status; wing-bone conventions, hinge math and
  sweep limits are rig-dependent and cannot safely be universal defaults.
- Reference-led Blender helpers: geometry/skin/export utilities may be shared later;
  species designs, private reference paths and Poofy's shading stay in the game.

## Evidence and limits

Synthetic headless tests check numeric trajectory parity, visit boundaries, fixed
spawn count/reuse, JSON/alpha parsing, material assignment and track edge cases.
Consumer tests cover species/dialogue preservation, world-life integration and all
seven painting choices. See the consumer validation record for exact commands/results.
This is one real consumer plus synthetic fixtures, not validation in a second game.
No new visual/GPU capture is claimed following the earlier driver-reset issue.
