# Assisted workflows

Keep GameCore workflows focused on inputs, system handoff, returned evidence and game integration. Complex domain processing belongs to its owning system; link its canonical workflow instead of duplicating its steps or code here.

Choose a use case, then the [2D](../2d/README.md) or [3D](../3d/README.md) catalog. These are reviewable playbooks with worked examples, not automatic converters or completed game ports.

| Use case | Guide | Example | Status |
|---|---|---|---|
| Phaser â†’ Godot | [Guide](phaser-to-godot/README.md) | [Coin-and-jump room](phaser-to-godot/example.md) | Scaffold |
| Godot Windows â†’ Android | [Guide](godot-windows-to-android/README.md) | [Touch exploration room](godot-windows-to-android/example.md) | Scaffold |
| Godot â†’ Unreal | [Guide](godot-to-unreal/README.md) | [Switch-and-door room](godot-to-unreal/example.md) | Exploratory scaffold |
| Logo sting / splash video | [Guide](logo-sting-video/README.md) | [AreCore V3 Pro at 1.5x](logo-sting-video/example.md) | Scaffold |
| Gameplay music videos / trailers | [Guide](game-music-video/README.md) | [ShammyVerse soundtrack](game-music-video/example.md) | Scaffold |
| Game asset showcase / demo video | [Guide](game-asset-showcase/README.md) | [ShammyVerse world-life demo](game-asset-showcase/example.md) | Scaffold |
| Ambient world life | [Guide](ambient-world-life/README.md) | [ShammyVerse world life](ambient-world-life/example.md) | Scaffold |
| Hair, fur and card textures | [Guide](hair-fur-textures/README.md) | [Short fur, 16 shells](hair-fur-textures/example.md) | Exploratory |
| Recorded music â†’ vocals + MIDI instruments | [Guide](music-reconstruction/README.md) | [Recorded game theme](music-reconstruction/example.md) | Exploratory |

The machine-readable [index](index.json) lists the minimal entry files; an optional `specs` list points to product/design documents such as the [GameCore hub and wizard design](../docs/GAMECORE_HUB_AND_WIZARD_DESIGN.md), whose first no-AI wizard is the logo sting. All guides use the [shared migration contract](../shared/migration-contract.md). Prefer the first two workflows for initial validation; the Unreal workflow needs a separately validated pilot before expansion.

Validate this scaffold with `python3 tools/validate_workflows.py` (`python` on Windows) from the repo root. This does not build engines, export games or execute the example acceptance tests.
