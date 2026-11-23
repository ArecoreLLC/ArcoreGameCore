# GameCore dependencies, specialization and forks

## Dependency model

GameCore is the canonical source and development toolchain. Runtime helpers are
vendored into a game's addons directory, with source path, module/version and SHA-256
recorded in its lock file. The game exports those local files. Players do not need
the GameCore repository, hub, MCP server or a network connection for these modules.
Offline gameplay builds can use the pinned copies; updating them and running
GameCore production tools still requires the development toolchain.

## Specialization order

1. **Parameters/data/callbacks:** tune brush size, assist threshold, reveal timing,
   leash/spacing, terrain callbacks or animation policy through documented APIs.
2. **Game adapter/composition:** own UI, textures, shaders, models, story, navigation,
   dialogue and input in the consuming game. Keep reusable logic independently testable.
3. **Shared enhancement:** if several games need a change, evolve the GameCore API
   compatibly where possible, test it and deliberately vendor the new version.
4. **Explicit game fork:** when the behavior cannot sensibly be expressed above,
   copy the module to a game-owned path (for example scripts/specialized/), update
   the game's imports, and record its origin and divergence. Keep the pristine
   vendor copy available as an upgrade/comparison baseline.

Do not silently edit addons/gamecore_* files. The vendor tool checks their recorded
hashes and refuses to overwrite edits unless explicitly forced. That refusal is an
upgrade safeguard, not a reason to discard game changes. Avoid --force as a routine
upgrade step; first move deliberate customizations into an adapter or explicit fork.

## Reuse suitability review

Perform this review before a new extraction, a shared API change, a consumer
specialization or an upstream upgrade. Repeat it when a second consumer exposes
assumptions. This is a required engineering review, not an extra user approval.

1. **State the reusable responsibility.** Describe inputs, outputs, lifecycle and
   engine/dimension constraints without naming a game, character, quest or asset.
2. **Inspect coupling.** Check imports and call sites for private asset paths,
   scene-tree names, global singletons, story flags, fixed species/palette counts,
   UI wording, terrain assumptions and timing tied to one song. Document supported
   constraints; don't mistake an explicit Godot/XZ contract for accidental coupling.
3. **Try a different use case.** Exercise different data and settings, such as a
   different canvas size/palette, reveal duration or follow offset. Use a small
   synthetic adapter when no second game exists. Label it as synthetic evidence,
   never as a second-game validation.
4. **Choose and explain the boundary.** Keep stable math/state in GameCore and
   presentation/story/navigation in the game. Use parameters for values, data for
   content, and narrow callbacks or composition for external services. If a change
   needs game-name branches, unrelated feature flags, or repeated consumer patches
   to vendor code, refactor the shared boundary before adding more special cases.
   Split independent responsibilities when their policies or lifecycles differ.
5. **Verify and publish the decision.** Record tests, compatibility impact, version,
   consumer adapter/fork paths and remaining limits. Update the API guide, registry
   and pinned consumer lock together when code changes. Run module and consumer
   regressions; presentation changes still need visual review.

Choose `retain`, `parameterize`, `extract-adapter`, `split-module` or `game-fork`.
A single consumer is enough for a useful extraction, but not proof of broad reuse.
Avoid speculative extension frameworks: add only the smallest boundary supported
by actual requirements and test cases. If behavior remains intrinsically game-only,
keep it in the game and register it as a candidate, not an extracted generic module.

Include this record in the slice's validation report:

```json
{
  "module": "module-id",
  "responsibility": "Game-independent input/output contract",
  "coupling_findings": [],
  "decision": "extract-adapter",
  "reason": "Presentation and story remain consumer-owned",
  "shared_changes": [],
  "consumer_adapter_paths": [],
  "alternative_use_case": {"kind": "synthetic", "result": "not_run", "evidence": null},
  "compatibility": "Record API and behavioral impact",
  "checks": [],
  "remaining_limits": ["Second-game validation not_run"]
}
```

Registry/MCP discovery is not a reuse certification. Automated checks can verify
files, contracts and alternate configurations; a human or coding-agent review must
still assess responsibility and coupling. Save the reasoning so future changes
can revisit it without repeating the full source audit.

## Fork record

Keep a tracked `GameCoreOverrides.json` in the consumer, with entries like:

```json
{
  "schema": "gamecore.consumer-forks.v1",
  "forks": [{
    "local_path": "game/scripts/specialized/my_companion_follow.gd",
    "upstream_path": "3d/godot/world_life/companion_follow.gd",
    "upstream_module": "gamecore.godot.world-life-kit",
    "upstream_bundle_version": "0.4.0",
    "upstream_file_version": "1.0.0",
    "base_sha256": "copy-the-actual-source-hash-from-the-vendor-lock",
    "reason": "Game-specific movement policy",
    "differences": ["Describe deliberate behavior changes"],
    "tests": ["Name the consumer regression command"],
    "upgrade_policy": "manual three-way comparison"
  }]
}
```

This is a documented record convention, not a new implemented fork-manager CLI.
No forks were necessary for the current painting extraction: the games specialize
through adapters and parameters. Forks outside the vendor destination are not
overwritten by vendoring, but are also not automatically updated by it.

## Upgrade procedure

Read upstream changes, preserve the current lock and base revision, vendor into a
review branch/worktree, run module tests and consumer source/exported tests, then
review changed visuals. For a fork, compare its pinned base, the current fork and
new upstream source. Record what was merged or intentionally retained. Never infer
behavior compatibility from matching API names or a successful export alone.
