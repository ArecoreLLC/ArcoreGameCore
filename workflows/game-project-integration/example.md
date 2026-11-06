# Example: a new 3D Unreal strategy prototype

Illustrative generic consumer configuration:

```json
{
  "schema_version": 1,
  "project_id": "strategy-prototype",
  "dimension": "3d",
  "engine": {"id": "unreal", "version": "5.8.4", "project_file": "StrategyPrototype.uproject"},
  "platforms": ["Win64"],
  "integrations": ["gamecore", "world-framework", "openworld", "model-forge", "sound-core"]
}
```

The engine project path is relative to the consumer root (the parent of Config). Consumer-specific paths and evidence remain in that game. For Godot use engine id `godot`, a verified version and `project.godot`; never infer a working Godot build from an Unreal check.

First slice: one camera, selectable unit, resource source and delivery point. Collect model and sound candidates with immutable identity and honest review status. Build the selected engine project, import one model with measured units, audition one cue, and run an isolated interaction test. Networking is a separate slice with its own provider setup and two-client test.

Acceptance states start at not_run. File discovery is not live MCP connectivity, build success, game parity or production approval.
