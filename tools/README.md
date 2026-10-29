# Scaffold tools

Requires Python 3.9+; standard library only. From the repository root:

```sh
python3 tools/validate_workflows.py
python3 -m unittest discover -s tools/tests -v
```

The validator checks required workflow IDs, statuses, dimensions, referenced files, repository-contained paths and local Markdown link targets in the new scaffold and root README. It emits a compact JSON result and exits nonzero on errors. It does not check external URLs, heading anchors, engine APIs, game behavior or export compatibility.

Tests cover a valid scaffold and invalid manifests/paths/links. No packages, engines or SDKs are installed by these commands. Historical documents remain outside link-validation scope except when linked from the scaffold.

For agent context, select the workflow from [index.json](../workflows/index.json), then read its guide/example and one dimension catalog. Full context generation and engine test runners are future tools, not implemented here. The older [porting CLI](../porting/README.md) remains separate.

See [MCP modeling integration](integrations/modeling-mcp.md) for the planned local modeling-tool boundary.

[SoundCore catalog integration](integrations/sound-catalog.md) records the companion game-sound catalog boundary; no live integration is included.
