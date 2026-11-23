# Working in ArcoreGameCore

Start with [workflows/index.json](workflows/index.json). Select one workflow and one dimension; read its guide and example, then only the referenced code needed for the task. Do not load every historical design document by default; a workflow's optional `specs` list names the product/design documents to read only when the task concerns them (for example the GameCore Tauri hub and wizards).

- `2d/` and `3d/` organize dimension-specific systems. `shared/` holds engine-neutral contracts. `workflows/` holds assisted migration playbooks, not converters.
- Existing `autoload/`, `scripts/`, `addons/`, and `porting/` are legacy Godot C# implementation. Preserve paths and behavior unless a task explicitly authorizes migration.
- Keep engine-specific runtime implementations separate. Do not assume C# works in a Godot web export or that changing export targets supplies touch controls.
- Read [shared/migration-contract.md](shared/migration-contract.md) before implementation. Record versions, baseline, scope, acceptance tests and evidence.
- Generic examples here must contain no private game source, credentials, signing keys or proprietary assets.
- Before extracting, changing or upgrading a reusable module, perform and record the [reuse suitability review](shared/module-specialization.md#reuse-suitability-review). Keep game policy in consumer adapters; refactor shared code when specialization leaks across that boundary. Record remaining reuse limits rather than claiming untested portability.
- A workflow's `wizard.json` is the single source of truth for its hub wizard, runner stages and ArcoreFlow nodes; read [shared/wizard/README.md](shared/wizard/README.md) before changing one and never duplicate its steps elsewhere.
- Agents register only the GameCore hub MCP; the hub calls ModelForge, SoundCore, Unreal and Flow through the registry in `shared/ecosystem.json` → `mcp`. Don't wire workflows to downstream MCP servers directly, and don't add credentials to the registry or templates.
- Run `python tools/validate_workflows.py`, `python tools/validate_wizards.py`, `python tools/mcp_registry.py` and `python -m unittest discover -s tools/tests -v` for scaffold changes (use `python3` where `python` is not Python 3; on Windows `python3` is usually a Store placeholder). These check documentation/manifest integrity, not game behavior.
- Do not mark a port complete from a checklist alone. Report the exact build/playtest commands, revision and platform, separating passed, failed, blocked and not-run checks.


<!-- BEGIN REPOSITORY ATTRIBUTION POLICY -->
## Commit and pull request attribution

Follow the repository-root `AI_ATTRIBUTION.md` for every commit and pull request. Do not add AI co-author trailers, generated-by footers, agent signatures, promotional links, or session links to commit messages or pull request titles/descriptions. Keep genuine human credits and required legal/license notices. Use the existing authorized Git identity; never invent human authorship. Check the final message and PR text before submission.
<!-- END REPOSITORY ATTRIBUTION POLICY -->
