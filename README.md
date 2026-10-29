# ArcoreGameCore

AI-assisted game-development framework organized by dimension and migration use case.

## Start here: assisted workflows

- [Workflow catalog](workflows/README.md): Phaser → Godot, Godot Windows → Android, and exploratory Godot → Unreal.
- [2D systems](2d/README.md), [3D systems](3d/README.md), and [shared contracts](shared/README.md).
- [Agent guidance](AGENTS.md) and [scaffold validation tools](tools/README.md).

The new folders provide guides and illustrative work packets, not automatic converters or completed runtime modules. Existing Godot 4 / C# code below is preserved in place as the legacy foundation. Its historical docs and CLI are not proof of current build/export readiness. The configured Boot scene is absent; run-specific game validation is still required. No language migration is performed by this scaffold.

## Docs

| Document | Purpose |
|----------|---------|
| [docs/README.md](docs/README.md) | Framework overview — autoloads, adapters, structure |
| [docs/PHASER_TO_GODOT.md](docs/PHASER_TO_GODOT.md) | Complete Phaser → Godot mapping reference |
| [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | Generic port phases checklist |
| [porting/README.md](porting/README.md) | AI-assisted porting system — CLI usage and workflow |
| [docs/EXPORT_SETUP.md](docs/EXPORT_SETUP.md) | Windows, Android, Web export setup and build guide |

## Quick start — porting a game

```bash
# See overall port progress
node porting/cli/port-query.js status

# Get ordered list of what to port next
node porting/cli/port-query.js next

# Generate a full AI porting brief for any component
node porting/cli/port-query.js context <component-id>

# Mark a component done
node porting/cli/port-query.js set <component-id> done
```

By default the CLI reads `../PlumpyAdventures/porting/port-manifest.json`.
Point it at any game with `--manifest=<path>`.

## Framework components

**Autoloads** (singleton nodes, auto-registered via plugin)
- `GameState` — score, lives, pause, chapter tracking
- `SaveManager` — slot-based JSON save/load with cloud delegation
- `AudioManager` — BGM player + 16-slot SFX pool
- `InputManager` — named action constants, gamepad detection
- `PlatformBridge` — achievement/stat/cloud API, auto-selects adapter at boot
- `SceneRouter` — scene transitions with fade overlay

**Platform adapters** (auto-selected, swap without touching game code)
- `LocalPlatformAdapter` — desktop, persists locally
- `SteamPlatformAdapter` — GodotSteam stub
- `WebPlatformAdapter` — JavaScriptBridge + localStorage
- `DebugPlatformAdapter` — logs all calls, no side effects

**Visual utilities**
- `ScreenTransition` — fade-to-black overlay used by SceneRouter
- `CameraShake` — trauma-based shake on Camera2D
- `DamageNumber` — floating score labels with tween
- `ParallaxBackground` — infinite auto-scroll layer

**Resource definitions** (`[GlobalClass]`, editable in Godot inspector)
- `CharacterDefinition` `EnemyDefinition` `LevelDefinition`
- `AbilityDefinition` `AchievementDefinition` `GameBalanceProfile`
