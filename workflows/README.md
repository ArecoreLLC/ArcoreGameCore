# Assisted workflows

Choose a use case, then the [2D](../2d/README.md) or [3D](../3d/README.md) catalog. These are reviewable playbooks with worked examples, not automatic converters or completed game ports.

| Use case | Guide | Example | Status |
|---|---|---|---|
| Phaser → Godot | [Guide](phaser-to-godot/README.md) | [Coin-and-jump room](phaser-to-godot/example.md) | Scaffold |
| Godot Windows → Android | [Guide](godot-windows-to-android/README.md) | [Touch exploration room](godot-windows-to-android/example.md) | Scaffold |
| Godot → Unreal | [Guide](godot-to-unreal/README.md) | [Switch-and-door room](godot-to-unreal/example.md) | Exploratory scaffold |

The machine-readable [index](index.json) lists the minimal entry files. All guides use the [shared migration contract](../shared/migration-contract.md). Prefer the first two workflows for initial validation; the Unreal workflow needs a separately validated pilot before expansion.

Validate this scaffold with `python3 tools/validate_workflows.py` from the repo root. This does not build engines, export games or execute the example acceptance tests.
