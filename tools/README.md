# Scaffold tools

The [shared module registry and Unreal runner](../shared/module-registry.md) now
provide `modules`, `sync`, `check`, `doctor`, `build`, `automation`, `smoke` and
`test` through `python tools/gamecore.py`. Dungeon Dash Market and Critter
Contraptions are the initial consumers. This runner is separate from the planned
hub/MCP wizard execution system.

Requires Python 3.9+; standard library only. Commands below use `python3`; on Windows use `python` (`python3` is usually a Store placeholder there). From the repository root:

```sh
python3 tools/validate_workflows.py
python3 tools/validate_wizards.py
python3 -m unittest discover -s tools/tests -v
```

The validator checks required workflow IDs, statuses, dimensions, referenced files, repository-contained paths and local Markdown link targets in the new scaffold and root README. It emits a compact JSON result and exits nonzero on errors. It does not check external URLs, heading anchors, engine APIs, game behavior or export compatibility.

`mcp_setup.py` opens a local checklist page of the apps the hub talks to (ModelForge, SoundCore, the Unreal editor, Flow). Tick the ones to use and it shows each one's live status. Connections are found automatically: the environment variables the registry names come first, then the file each app writes for local clients (ModelForge's `~/.modelvault/settings.json`, SoundCore's `service.json`). Tokens stay in the script's memory; the page sees status only, and the selection is saved as server ids in `.gamecore/mcp-selection.json` (gitignored).

`mcp_registry.py` checks the MCP registry in `shared/ecosystem.json`. `--probe` performs MCP initialize and tools/list against each downstream server, using the same connection lookup, and never calls a tool. `--selected` probes only the apps ticked in the checklist.

`validate_wizards.py` checks every `wizard` template listed in the index against [the wizard schema](../shared/wizard/README.md) and its cross-reference rules.

Tests cover a valid scaffold and invalid manifests/paths/links. No packages, engines or SDKs are installed by these commands. Historical documents remain outside link-validation scope except when linked from the scaffold.

For agent context, select the workflow from [index.json](../workflows/index.json), then read its guide/example and one dimension catalog. Full context generation remains future work; the bounded Unreal pilot runner is documented above. The older [porting CLI](../porting/README.md) remains separate.

`game_music_video.py` runs the [gameplay music-video workflow](../workflows/game-music-video/README.md): `vendor` (copy the Godot recorder into a game with a SHA-256 lock), `dry-run` (headless, per song), `vendor --module music-video|world-life` (the recorder with the asset-showcase base, or the world-life kit), `record` (Movie Maker capture, exact-song mix, MP4, sharing preview and contact sheet), `showcase` (asset showcase: one PNG per shot, windowed without a movie, tiled into sheets of eight), `sheet`, and `motion` (flags dead shots: shots whose mean frame-to-frame change stays under a threshold, usually a still subject over an empty background). It needs Godot 4 and FFmpeg for the last three; its unit tests do not.

See [MCP modeling integration](integrations/modeling-mcp.md) for the modeling-tool boundary and reviewed external Unreal consumer.

## Unreal source inventory

`inventory_unreal.py` uses Python 3.10+ and the standard library to catalog the external ArcoreWorldFramework and ArcoreOpenWorld checkouts without importing their code. Scope, exclusions, selected historical receipts and known limits live in [unreal-sources.json](../framework/inventory/unreal-sources.json). The [integration guide](../framework/UNREAL_INTEGRATION.md) explains ownership and the [suite registry](../framework/inventory/unreal-validation-suites.json) distinguishes procedural builders, actual tests and historical evidence checkers.

```sh
python3 tools/inventory_unreal.py --check
# After reviewing intentional source changes, regenerate the JSON and Markdown:
python3 tools/inventory_unreal.py
```

The check fails on missing sources and added, changed or removed files, plus metadata or generated-document drift. It does not run engines, scripts, imports or asset approval. Binary assets, generated build/cache directories and capture history stay outside the source inventory. Inventory regression tests are included in the existing `tools/tests` discovery command above.

[SoundCore catalog integration](integrations/sound-catalog.md) records the companion game-sound catalog boundary; no live integration is included.

## Consumer validation receipts

`capture_validation.py` writes append-only receipts with selected source and
evidence hashes, including for consumers without Git. See the
[receipt contract](../shared/validation-receipts.md). It validates declaration
shape and file identity; it does not run commands or certify gameplay.

`tools/synthesize_tone.py` writes deterministic original stereo PCM cues with bounded duration, harmonic count, peak gain and echo. Call `write_tone(path, frequencies, ...)`; the game owns note selection and engine import. Sources are generated without external samples. Tests validate finite inputs, clipping bounds, silent endpoints and repeatability. Listening and runtime mix approval remain separate.

`song_beats.py` estimates each song's tempo (BPM) and first-beat offset for beat-synced game life (dances, drums,
stomps) and writes JSON or a GDScript constant. It is part of the [ambient-world-life](../workflows/ambient-world-life/README.md)
and [game-music-video](../workflows/game-music-video/README.md) workflows. It needs FFmpeg; its unit tests do not.

`tests/test_world_life_godot.py` runs the world-life components' headless Godot test when `GODOT` is set (for example
`GODOT=<Godot_console.exe> python -m unittest tools.tests.test_world_life_godot`); it is skipped otherwise.
