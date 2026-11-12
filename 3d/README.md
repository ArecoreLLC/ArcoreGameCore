# 3D systems

Home for reusable 3D controllers, cameras, interactions and starter scenes. This folder is a catalog; runtime implementation remains engine-specific.

The [Unreal framework inventory](../framework/UNREAL_INTEGRATION.md) now records ArcoreWorldFramework's existing runtime telemetry, profiles, terrain/geometry helpers and engine validation, together with ArcoreOpenWorld's procedural builders and fixtures. See its [complete file list](../framework/inventory/UNREAL_FILES.md) and [validation runbook](../framework/UNREAL_VALIDATION.md). These are linked external implementations, not engine-neutral controllers or a completed migration.

| Candidate | Contract | Candidate validation |
|---|---|---|
| Character controller | Named actions, coordinate convention, movement modes | Slopes, collisions, camera-relative movement |
| Camera | Target, yaw/pitch, distance and collision rules | Obstruction, input sensitivity, reset |
| Interaction | Actor/target ID and range | Enter/exit range; one-shot activation |
| Combat timing | [CombatWindow](../shared/cpp/CombatWindow.md): engine-neutral active/recovery windows | Standalone C++ boundary tests and consumer-owned Unreal smoke tests; no cross-engine parity claim |

Use [Windows → Android](../workflows/godot-windows-to-android/README.md) for platform adaptation, or [Godot → Unreal](../workflows/godot-to-unreal/README.md) for an assisted engine migration. Both use the [shared migration contract](../shared/migration-contract.md).

Future runtime code belongs in engine-specific subdirectories. Keep story, characters and level-specific logic in the consuming game. Use a small measured vertical slice before extracting a general module.

Asset creation can later use the planned [AssetForge / Blender MCP integration](../tools/integrations/modeling-mcp.md). No live integration is included.

## Portable light-path rule

[LightReflection](../shared/cpp/LightReflection.md) supplies normalized specular reflection math independent of an engine. Consumers own bounded collision traces and receiver state. The initial Unreal consumer is Lumen-Weaver; cross-engine parity and packaged rendering are not yet validated.

## Course placement preflight

[Course placement contract](../shared/course-placement-contract.md) validates full motion envelopes, grid alignment and protected rectangles. Its optional C++ header allows an Unreal consumer to share numeric rules without loading the GameCore checkout at runtime. Engine placement, collision and network acceptance remain consumer-owned.

## Stealth exposure

[ExposureMeter](../shared/cpp/ExposureMeter.md) provides bounded elapsed-time detection and recovery. Consumers own visibility, cover, exposure zones, terminal outcomes and reset. Lumen-Weaver is the initial Unreal consumer; cross-engine parity is unverified.
