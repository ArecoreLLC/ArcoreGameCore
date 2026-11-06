# 3D systems

Home for reusable 3D controllers, cameras, interactions and starter scenes. This folder is a catalog; runtime implementation remains engine-specific.

The [Unreal framework inventory](../framework/UNREAL_INTEGRATION.md) now records ArcoreWorldFramework's existing runtime telemetry, profiles, terrain/geometry helpers and engine validation, together with ArcoreOpenWorld's procedural builders and fixtures. See its [complete file list](../framework/inventory/UNREAL_FILES.md) and [validation runbook](../framework/UNREAL_VALIDATION.md). These are linked external implementations, not engine-neutral controllers or a completed migration.

| Candidate | Contract | Candidate validation |
|---|---|---|
| Character controller | Named actions, coordinate convention, movement modes | Slopes, collisions, camera-relative movement |
| Camera | Target, yaw/pitch, distance and collision rules | Obstruction, input sensitivity, reset |
| Interaction | Actor/target ID and range | Enter/exit range; one-shot activation |

Use [Windows → Android](../workflows/godot-windows-to-android/README.md) for platform adaptation, or [Godot → Unreal](../workflows/godot-to-unreal/README.md) for an assisted engine migration. Both use the [shared migration contract](../shared/migration-contract.md).

Future runtime code belongs in engine-specific subdirectories. Keep story, characters and level-specific logic in the consuming game. Use a small measured vertical slice before extracting a general module.

Asset creation can later use the planned [AssetForge / Blender MCP integration](../tools/integrations/modeling-mcp.md). No live integration is included.
