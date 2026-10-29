# 2D systems

Home for reusable 2D controllers, cameras, interactions, starter scenes and engine-specific adapters. This initial scaffold contains a catalog, not implemented new modules.

| Candidate | Contract | Candidate validation |
|---|---|---|
| Character controller | Named movement/jump actions; explicit units and physics tick | Grounded jump, collision and replay test |
| Camera | Follow target, bounds and optional shake | No jitter; limits and shake reset |
| Interaction | Actor/target ID and action event | One event per interaction; disable/re-enable |

Start with the [Phaser → Godot example](../workflows/phaser-to-godot/example.md). Common migration rules live in [shared](../shared/migration-contract.md). Existing C# visual utilities remain at `scripts/visual/`; this directory does not relocate or reimplement them.

Place future implementations under an engine-named subdirectory (for example `godot/`) only when a real consumer and test exist. Do not duplicate the shared contracts for each engine.
