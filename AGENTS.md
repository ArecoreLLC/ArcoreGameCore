# Working in ArcoreGameCore

Start with [workflows/index.json](workflows/index.json). Select one workflow and one dimension; read its guide and example, then only the referenced code needed for the task. Do not load every historical design document by default.

- `2d/` and `3d/` organize dimension-specific systems. `shared/` holds engine-neutral contracts. `workflows/` holds assisted migration playbooks, not converters.
- Existing `autoload/`, `scripts/`, `addons/`, and `porting/` are legacy Godot C# implementation. Preserve paths and behavior unless a task explicitly authorizes migration.
- Keep engine-specific runtime implementations separate. Do not assume C# works in a Godot web export or that changing export targets supplies touch controls.
- Read [shared/migration-contract.md](shared/migration-contract.md) before implementation. Record versions, baseline, scope, acceptance tests and evidence.
- Generic examples here must contain no private game source, credentials, signing keys or proprietary assets.
- Run `python3 tools/validate_workflows.py` and `python3 -m unittest discover -s tools/tests -v` for scaffold changes. These check documentation/manifest integrity, not game behavior.
- Do not mark a port complete from a checklist alone. Report the exact build/playtest commands, revision and platform, separating passed, failed, blocked and not-run checks.
