# Godot → Unreal Engine

**Status:** exploratory assisted workflow scaffold. This is a rebuild/validation plan, not a GDScript-to-C++ translator. Prove one small slice before committing to a full migration.

## Inputs

Use the [shared contract](../../shared/migration-contract.md), source project/revision, pinned Godot and Unreal versions, target platform, asset licenses/source files and a reason for migration. Select [2D](../../2d/README.md) or [3D](../../3d/README.md); the example covers 3D. Verify Unreal tooling and platform requirements separately before running builds.

## Mapping

| Godot concept | Candidate Unreal concept | Decision to record |
|---|---|---|
| Scene/node composition | Actors/components and Blueprint classes | Ownership, spawn/despawn and lifecycle |
| Signals | Event dispatchers/delegates | Listener lifetime and event ordering |
| InputMap actions | Enhanced Input actions/mapping contexts | Trigger behavior and context priority |
| Resources/save payloads | Data assets/tables and SaveGame boundary | Stable IDs, serialization/version migration |
| Materials/shaders/animation | Rebuilt materials/animation setup | Visual intent, rig compatibility and cost |

These are conceptual correspondences, not one-to-one replacements. Choose Blueprint, C++ or a mixture per module. Record coordinate axes, handedness and units explicitly during asset conversion; do not assume transforms or physics values transfer unchanged.

## Checklist

- [ ] Establish why Unreal benefits this game and define a stop/go budget.
- [ ] Inventory assets, license constraints, plugins, scripts and unsupported features.
- [ ] Map one slice and rebuild its minimal input, interaction and save behavior.
- [ ] Import original source assets with verified scale/orientation; rebuild materials as needed.
- [ ] Compare behavior and visuals against the Godot baseline with agreed tolerances.
- [ ] Decide whether to expand based on measured cost and remaining incompatibilities.

## Outputs and acceptance

Deliver a mapping ledger, runnable Unreal slice, parity evidence and stop/go decision. Keep the original game operational. Use the [switch-and-door example](example.md); no whole-game migration is implied. Engine installation, license acceptance and publishing require their own applicable approvals.

Reference: [Unreal Engine documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine). Consult the documentation for the pinned version and target platform before implementation.
