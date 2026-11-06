# Start another lightweight Unreal game

Reusable helper, 2026-11-02. Scope: 3D, Windows, Unreal Engine 5.8.4. This is a guide, not an executable template or a completed Godot-to-Unreal migration.

## Ownership and existing workflows

Start with GameCore's [game-project integration workflow](../workflows/game-project-integration/README.md), [example](../workflows/game-project-integration/example.md) and [3D catalog](../3d/README.md). Follow the [shared contract](../shared/migration-contract.md) for version pins, scope and evidence.

GameCore owns entry points and reusable guidance. ArcoreWorldFramework owns reusable implementation, integrity rules, rendering profiles and engine adapters. The consuming game owns gameplay, assets, import adapters and acceptance evidence. Preserve GameCore's existing Godot code.

Reuse the existing ArcoreOpenWorld workflows before inventing new ones. GameCore already indexes them in [UNREAL_INTEGRATION.md](UNREAL_INTEGRATION.md), [UNREAL_VALIDATION.md](UNREAL_VALIDATION.md) and the [source inventory](inventory/UNREAL_FILES.md).

With the standard sibling checkout layout, consult:

| Need | Existing reference |
|---|---|
| Project setup, editor tools and operational boundaries | [OpenWorld README](../../ArcoreOpenWorld/README.md) and [AGENTS](../../ArcoreOpenWorld/AGENTS.md) |
| Immutable source/version pins and model review | [Model review workflow](../../ArcoreOpenWorld/Assets/Review/README.md) |
| Separate asset inspection fixture | [Asset sandbox workflow](../../ArcoreOpenWorld/Assets/Sandbox/README.md) |
| Asset sourcing and recorded batches | [Asset guide](../../ArcoreOpenWorld/Assets/README.md) |
| Terrain changes and vegetation exclusions | [Creek workflow](../../ArcoreOpenWorld/Terrain/Creeks/README.md) |
| Reusable package and plugin integration | [WorldFramework README](../../ArcoreWorldFramework/README.md), [architecture](../../ArcoreWorldFramework/docs/architecture.md) and `docs/workflows/` |

OpenWorld's tools contain project-specific map names, terrain regions, native extension methods and source pins. Adapt their contracts into a consumer-owned workflow; do not run them blindly against another game or copy OpenWorld's large landscape and PCG population as a default starter. Inventory entries and historical passes do not certify a new consumer.

## Language choices

Use C++ for Unreal gameplay, simulation, authoritative networking and native engine access. Use Blueprints for visual behavior, effects, UI and tuning, with data assets for definitions. Rust fits standalone services, asset processing and Tauri application backends; introducing Rust into Unreal gameplay adds a bridge and maintenance burden. This is an engine-integration choice, not a claim that C++ is universally faster or better.

## Consumer layout

```text
NewGame.uproject
Source/NewGame/          C++ runtime module
Source/*.Target.cs      Game and Editor targets
Config/                 Engine, input, game and packaging settings
Content/NewGame/         Maps, materials, imported models and audio
Tools/                  Build, package, content setup and smoke checks
Docs/                   Plan, decisions, evidence and asset workflow
Media/                  Owned source media, licenses and manifests
Builds/Windows/         Generated standalone build
Launch.cmd              Prefer packaged game, optionally development fallback
```

Exclude Binaries, Intermediate, DerivedDataCache, Saved and Builds from source control. Keep editable source media and provenance. Never copy credentials, user caches, signing keys or game-specific assets into a generic template.

## Duplication procedure

1. Define one playable interaction and target hardware. Record the engine patch and source baseline; use hashes when no Git revision exists.
2. Create a new project or copy only the reviewed skeleton. Rename the `.uproject`, module/build/target classes, API macro, `/Script/OldModule` references, content paths, launch scripts and project GUID. Update absolute engine paths for the workstation.
3. Establish inexpensive rendering defaults: disable Lumen, ray tracing, Nanite, virtual shadow maps and motion blur unless the game requires them. These are starting choices, not guaranteed hardware support.
4. Create an authored startup map and explicit default GameMode. Content-generation scripts should create missing assets and preserve existing authored content.
5. Build and test the smallest interaction before adding economy, combat or multiplayer. Keep cosmetic physics separate from authoritative rules.
6. Build the editor target, cook/package the Windows game, then exercise the packaged executable. Include runtime-loaded materials and meshes in cook settings. Test without sibling development checkouts as runtime dependencies.
7. Record build commands, smoke-test results, screenshots, revision/hashes, and named target hardware. Measure frame time and loading in the packaged game. Separate automated checks, visual review, listening review and user playtests.

Unreal's default local Zen cache may fail on a workstation. The demonstrated fallback is `-ddc=InstalledNoZenLocalFallback` with `UE-LocalDataCachePath` set to a consumer-owned cache directory; diagnose the local issue rather than silently changing global engine settings.

## Asset services

- **ModelForge MCP:** discover live tool schemas, search existing models before creating, inspect licenses and geometry, preserve donor IDs/versions, and use its modeling/Blender bridge. Store derivative versions, source hashes, units, pivot and import evidence. A preview is not production approval.
- **SoundCore MCP:** call `get_capabilities`, read `soundcore://workflows/project-assets`, search `search_assets(asset_type=audio)`, and inspect `get_asset` licenses. Prepare via `apply_edit_recipe` or `render_edit`, using the returned `asset_id`. Read existing project dependencies and save the complete ID list with `save_project_manifest`. Request `deliver_sounds`; copy audio, licenses and metadata into a new project-owned media folder, verify bytes/hashes, then `acknowledge_delivery`. Never automatically replace saved media. Unheard candidates remain not-auditioned.
- **SonicAlchemist:** intended sound engineering/adaptive music lab. Verify its actual capabilities and integration before relying on it. Do not confuse it with SoundCore's catalog or assume it is already wired to a game.

Keep connection credentials in existing app settings or local environment variables. Authoring services are not runtime dependencies for players.

## Multiplayer boundary

Begin with local gameplay. If needed, use server-authoritative player-hosted sessions: validate ownership, costs, destinations and order rates on the host. Define disconnect behavior and test two clients. Online services and matchmaking do not supply free dedicated simulation hosting. Dedicated-server packaging is separate infrastructure work.

## Demonstrated pilot and remaining limits

The local `SandboxKingdoms` pilot used Unreal 5.8.4, a native runtime module, primitive scenery, an overhead camera and a three-toy squad. Editor and Windows Development packaging succeeded. Runtime smoke checks passed screen-based selection, movement orders, arrival, boundary clamping and reset; both editor-hosted and packaged screenshots were inspected. Evidence is consumer-owned under `SandboxKingdoms/Saved`, not bundled here.

This helper does not promote the game's code into a reusable library. Minimum hardware, child usability, economy, obstacle navigation and multiplayer were not established by those checks. New projects must run their own acceptance checks. Read the existing OpenWorld/WorldFramework workflows for asset and world validation beyond this small pilot.
