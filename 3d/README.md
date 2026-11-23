# 3D systems

The [reusable procedure registry](../shared/reusable-modules.json) records source,
consumer references and extraction status. Search it through the hub MCP tool
`reusable_modules`. The [ShammyVerse reuse audit](godot/world_life/REUSE_AUDIT.md)
covers butterfly spawning/flight, JSON wing types and other candidate procedures.

## Godot gameplay music-video recorder

[music_video](godot/music_video/README.md) is the Godot 4 runtime of the
[game-music-video workflow](../workflows/game-music-video/README.md). It provides a frame-counted video clock,
camera-relative scripted movement, a camera guard, cuts on caption starts and generic shots. Games vendor it with
`tools/game_music_video.py vendor` and add their own adapter and shot lists.

## Godot asset showcase

`asset_showcase.gd`, beside the recorder in [music_video](godot/music_video/README.md), is the Godot runtime of the
[game-asset-showcase workflow](../workflows/game-asset-showcase/README.md): one titled shot per new asset, as
screenshots (`tools/game_music_video.py showcase`) or a demo video (`record`).

## Godot world-life kit

[world_life](godot/world_life/README.md) is the Godot 4 runtime of the
[ambient-world-life workflow](../workflows/ambient-world-life/README.md): merged primitive meshes, cached materials and
a flutter shader, shore and water placement, an attention registry, night and beat clocks, synthesised sounds, birds
and leap arcs, plus ten components for the small pipelines (beat-synced dance, attention glance, idle fidgets, escort
formation, musical stones, time of day, ambient chatter, route gates, arrival celebrations, splashes). Games vendor it with `tools/game_music_video.py vendor --module world-life`.

## Procedural world generation

[3d/procgen](procgen/README.md) holds starter JSON recipes (including `underwater-basin.json` and `canyon-arch.json`) for the [procedural world generation workflow](../workflows/procedural-world-generation/README.md), paired with the [Godot 4 bundle loader](godot/procgen/README.md) and [Unreal 5.x integration guide](unreal/procgen/README.md).

## Painted, animated companions

[companion_studio](blender/companion_studio/README.md) (Blender Python) and [painted_companion](godot/painted_companion/README.md) (Godot shader include)
are the runtime-side pieces of the [painted-animated-companions workflow](../workflows/painted-animated-companions/README.md): a per-texel painted
albedo atlas for part-built characters, pose-function clips with a shared tail wave and a planted-foot stepper, and lighting that keeps painted colour
on screen. Games vendor them with `tools/companion_pipeline.py vendor`.

## Unreal game feel

[GameFeel](unreal/GameFeel.md) catalogs reusable buffered input and feedback envelopes
in the Unreal runtime provider. Consumers own action eligibility, tuning and presentation.

Home for reusable 3D controllers, cameras, interactions and starter scenes. This folder is a catalog; runtime implementation remains engine-specific.

The [Unreal framework inventory](../framework/UNREAL_INTEGRATION.md) now records ArcoreWorldFramework's existing runtime telemetry, profiles, terrain/geometry helpers and engine validation, together with ArcoreOpenWorld's procedural builders and fixtures. See its [complete file list](../framework/inventory/UNREAL_FILES.md) and [validation runbook](../framework/UNREAL_VALIDATION.md). These are linked external implementations, not engine-neutral controllers or a completed migration.

| Candidate | Contract | Candidate validation |
|---|---|---|
| Character controller | Named actions, coordinate convention, movement modes | Slopes, collisions, camera-relative movement |
| Camera | Target, yaw/pitch, distance and collision rules | Obstruction, input sensitivity, reset |
| Interaction | Actor/target ID and range | Enter/exit range; one-shot activation |
| Combat timing | [CombatWindow](../shared/cpp/CombatWindow.md): engine-neutral active/recovery windows | Standalone C++ boundary tests and consumer-owned Unreal smoke tests; no cross-engine parity claim |

Use [Windows â†’ Android](../workflows/godot-windows-to-android/README.md) for platform adaptation, or [Godot â†’ Unreal](../workflows/godot-to-unreal/README.md) for an assisted engine migration. Both use the [shared migration contract](../shared/migration-contract.md).

Future runtime code belongs in engine-specific subdirectories. Keep story, characters and level-specific logic in the consuming game. Use a small measured vertical slice before extracting a general module.

Asset creation can later use the planned [AssetForge / Blender MCP integration](../tools/integrations/modeling-mcp.md). No live integration is included.

## Portable light-path rule

[LightReflection](../shared/cpp/LightReflection.md) supplies normalized specular reflection math independent of an engine. Consumers own bounded collision traces and receiver state. The initial Unreal consumer is Lumen-Weaver; cross-engine parity and packaged rendering are not yet validated.

## Course placement preflight

[Course placement contract](../shared/course-placement-contract.md) validates full motion envelopes, grid alignment and protected rectangles. Its optional C++ header allows an Unreal consumer to share numeric rules without loading the GameCore checkout at runtime. Engine placement, collision and network acceptance remain consumer-owned.

## Stealth exposure

[ExposureMeter](../shared/cpp/ExposureMeter.md) provides bounded elapsed-time detection and recovery. Consumers own visibility, cover, exposure zones, terminal outcomes and reset. Lumen-Weaver is the initial Unreal consumer; cross-engine parity is unverified.

## Unreal beam presentation

[BeamMesh](unreal/BeamMesh.md) is a versioned Unreal-only adapter for pooled,
noncolliding cylinder segments. Lumen-Weaver validates alignment, visibility,
obstruction and reset in engine automation. Materials and gameplay remain
consumer-owned; packaged deployment and a second consumer remain unverified.

## Unreal interaction targeting

[InteractionTrace](unreal/InteractionTrace.md) shares a first-blocking-surface
query between consumer prompts and actions. Supports a wider preview range and
an inclusive action reach, with finite-input validation and optional ignored actor.
Lumen-Weaver owns native focus and occlusion tests; gameplay eligibility stays
consumer-owned. No network authority or cross-engine behavior is implied.
