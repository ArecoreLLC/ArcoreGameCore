# Scaffold tools

Requires Python 3.9+; standard library only. From the repository root:

```sh
python3 tools/validate_workflows.py
python3 -m unittest discover -s tools/tests -v
```

The validator checks required workflow IDs, statuses, dimensions, referenced files, repository-contained paths and local Markdown link targets in the new scaffold and root README. It emits a compact JSON result and exits nonzero on errors. It does not check external URLs, heading anchors, engine APIs, game behavior or export compatibility.

Tests cover a valid scaffold and invalid manifests/paths/links. No packages, engines or SDKs are installed by these commands. Historical documents remain outside link-validation scope except when linked from the scaffold.

For agent context, select the workflow from [index.json](../workflows/index.json), then read its guide/example and one dimension catalog. Full context generation and engine test runners are future tools, not implemented here. The older [porting CLI](../porting/README.md) remains separate.

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
