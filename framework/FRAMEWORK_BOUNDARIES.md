# Framework boundaries and reuse plan

The initial reusable layer is the process and its records. Runtime extraction should follow a second project's needs and prove a component can work without ShammyVerse-specific characters, quest counts, island names, or filesystem paths.

## Reuse categories

| Area | Reuse now | Adapt or implement per game |
|---|---|---|
| Project setup | Folder conventions, recorded tool versions, repeatable launch/validation entry points | Engine, renderer, packaging, installation paths, platform support |
| Asset production | Versioning, source lineage, fixed review views, preservation checks | Skeletons, export settings, materials, shaders, engine import |
| Interaction | Contextual actions, clear availability rules, cancellation checks | Input bindings, UI, abilities, game rules |
| Progression | Stable IDs, prerequisite fixtures, completion/reset scenarios | Quest graph, rewards, counts, difficulty values |
| Persistence | Isolated fixtures, schema validation, backup/recovery, relaunch tests | Serialization adapter, payload schema, migration and slot policy |
| Audio | Source/cue separation, stable track IDs, playback-driven synchronization | Audio backend, bus setup, caption UI, editorial content |
| Performance | Representative scenarios, quality tiers, measured frame times | Budgets, hardware matrix, renderer features and profiling tools |
| Repository maintenance | Validation before publication, explicit change review | Test runner, artifact storage, branch/release conventions |

## Proposed organization for a future game

```text
<Game>/
  README.md                 # Current setup, controls, status, validation
  Docs/
    PROJECT_BRIEF.md
    Decisions/
    Iterations/
    CURRENT_STATE.md
  SourceAssets/             # Original and editable sources with provenance
  Runtime/                  # Engine-native project; adapt this name to its conventions
  Tests/                    # Maintained fixtures and suite registry
  Tooling/                  # Scripts and tracked tool manifest; binaries excluded
```

This is a documentation convention, not a generated project. Keep large binary storage and retention decisions explicit before copying historical asset archives. Retain source notices and do not treat a third-party asset's license as a license for the whole framework.

## Candidates for later extraction

Start with the validation registry and asset metadata because they can support another project without copying game logic. Next evaluate fixture setup, contextual action descriptions, audio/caption data, and save transport.

For each runtime candidate, write down its inputs, outputs, owned state, dependencies, and failure behavior. Keep game-owned rules outside the shared component. Acceptance requires a small demonstration in a second project and checks proving it no longer relies on ShammyVerse paths or state.

The [save implementation](../../ShammyVerse/game/scripts/adventure_save.gd), [interaction workflow](../../ShammyVerse/Design/Workflow/COMPANION_ACTIONS_AND_ISLANDS_WORKFLOW.md), and [music workflow](../../ShammyVerse/Design/Workflow/MUSIC_AND_LYRICS_WORKFLOW.md) are reference implementations and case studies, not drop-in cross-engine modules.

## Engine decision before an executable starter

Record the chosen engine/version, target platforms, rendering baseline, scripting approach, and asset interchange path in a [decision record](templates/DECISION_RECORD.md). If Unreal Engine is selected, first validate a small scene with one animated asset, one interaction, an isolated save round trip, and a packaged launch. Consult the selected version's official documentation when implementing that adapter.

An Unreal implementation must validate its own import, materials, animation, collision, and automated-check pipeline. The existing Godot scripts and shader files do not establish that compatibility. AR functionality, including Google ARCore, remains outside the initial scope unless selected as a project requirement.
