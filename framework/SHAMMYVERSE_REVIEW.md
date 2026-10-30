# ShammyVerse process review

The strongest reusable result is the development loop: preserve evidence, implement a bounded change, inspect real output, test affected behavior, and record what remains uncertain. The next improvement is to make current state and validation coverage easier to find.

This is an initial review of selected repository evidence, dated 2026-10-30. Reported outcomes below are historical results from the cited records, not newly executed checks.

## How development progressed

Git history begins with the initial project commit on October 25 and includes character, expression, and song-start work that day; swimming and environment polish on October 27; Tsunami, dialogue, wet coats, and music work on October 28; and further Tsunami and model-quality passes on October 30. Some design records describe work preceding the initial commit, so commit dates are checkpoints rather than exact feature start dates.

The [character workflow](../../ShammyVerse/Design/Workflow/CHARACTER_WORKFLOW.md) captures the original asset loop. [Companion actions and islands](../../ShammyVerse/Design/Workflow/COMPANION_ACTIONS_AND_ISLANDS_WORKFLOW.md) extends it into progression, contextual interaction, and development checkpoints. [Autosave](../../ShammyVerse/Design/Iterations/autosave-v001/DESIGN_LOG.md) adds persistence and isolated fixtures. Later [quality passes](../../ShammyVerse/Design/Iterations/quality-pass-v005/DESIGN_LOG.md) review active assets and procedural geometry together.

## Strengths to reinforce

| Observed practice | Evidence and outcome | Reusable practice |
|---|---|---|
| Versioned, editable assets | The [character workflow](../../ShammyVerse/Design/Workflow/CHARACTER_WORKFLOW.md) retains source scenes, builders, manifests, and fixed review views. | Keep a complete review package for each accepted asset version. |
| Preservation verified beyond filenames | [Tsunami's log](../../ShammyVerse/Design/Characters/Tsunami/DESIGN_LOG.md) records geometry/color hashes and animation comparisons across revisions. | Define the properties that must remain unchanged and verify those properties after export and import. |
| Real renders catch problems structural checks miss | [Quality pass v005](../../ShammyVerse/Design/Iterations/quality-pass-v005/DESIGN_LOG.md) records an inverted-looking ray wing found in rendered review and corrected winding/mirroring. | Pair numerical audits with representative in-engine views and motion. |
| Small collision proxies preserve responsiveness | The [character workflow](../../ShammyVerse/Design/Workflow/CHARACTER_WORKFLOW.md) reports replacing a 2,050-point sphere hull with analytic collision, reducing measured contact steps from 20–40+ ms to about 0.1 ms in that case. | Profile sustained collision contact; keep render meshes and collision design independent. |
| Reproducible gameplay access | [Companion checkpoints](../../ShammyVerse/Design/Workflow/COMPANION_ACTIONS_AND_ISLANDS_WORKFLOW.md) prepare prerequisite state, including a nearly complete fishing challenge. | Provide fixtures for the start, boundary, and completion of each progression feature. |
| Player data protected during testing | [Save implementation](../../ShammyVerse/game/scripts/adventure_save.gd) disables ordinary persistence for script/smoke/capture fixtures without an explicit override. [Autosave tests](../../ShammyVerse/Design/Iterations/autosave-v001/DESIGN_LOG.md) exercise separate write/read processes. | Use isolated saves and test recovery and relaunch, not just an in-memory round trip. |
| Performance claims have context | The [performance budget](../../ShammyVerse/Design/PERFORMANCE_BUDGET.md) and [plush workflow](../../ShammyVerse/Design/Workflow/PLUSH_CHARACTER_WORKFLOW.md) distinguish hardware-specific measurements from minimum-spec guarantees. | Record hardware, renderer, scenario, quality, resolution, caps, and frame-time distribution. |
| Audio source and editorial status are explicit | The [music workflow](../../ShammyVerse/Design/Workflow/MUSIC_AND_LYRICS_WORKFLOW.md) preserves lyrics and recordings, hashes runtime audio, and separates ASR drafts from listening verification. | Keep functional synchronization and editorial correctness as separate acceptance criteria. |
| Provenance survives adaptation | The [asset manifest](../../ShammyVerse/game/assets/licenses/asset_provenance.json) records original sources, notices, modifications, and hashes. | Carry source records with each derivative and review them before reuse in another game. |

## Friction and improvement opportunities

| Finding | Evidence | Proposed improvement |
|---|---|---|
| Current state is hard to distinguish from history | The [README](../../ShammyVerse/README.md) describes swimming and autosave near the top but retains older statements that swimming and persistence are unimplemented. It also lists multiple character versions as current in different sections. | One concise current-state page; dated history elsewhere; active versions in a registry. |
| The default check command covers a small subset | [maintain_project.py](../../ShammyVerse/scripts/maintain_project.py) lists four suites. The reviewed tree contains 156 `test*.gd` files under `Design`, including historical variants. | Register maintained suites and their purpose; distinguish active, superseded, and archived fixtures. Do not run every historical file blindly. |
| Tests can preserve obsolete assumptions | [Quality pass v003](../../ShammyVerse/Design/Iterations/quality-pass-v003/DESIGN_LOG.md) documents replaced quest assumptions and save prerequisites. [v005](../../ShammyVerse/Design/Iterations/quality-pass-v005/DESIGN_LOG.md) narrows body-mesh assertions to exclude new droplets. | Tie tests to intended behavior; document fixture replacements and scope structural assertions to their actual subject. |
| A builder may no longer represent the latest source | [Tsunami v011–v013](../../ShammyVerse/Design/Characters/Tsunami/DESIGN_LOG.md) includes external ModelVault edits not reproduced by the original procedural builder. | Record the canonical editable source, parent version, external edits, and which scripts can safely operate on it. |
| Portable local tools are not yet a tracked bootstrap | `tools/installed-versions.json` exists locally, while [.gitignore](../../ShammyVerse/.gitignore) excludes `tools/`; the manifest is not tracked in the reviewed checkout. | Store the tool manifest outside ignored binaries and verify setup from a clean checkout. |
| Publishing selects all changes | [maintain_project.py](../../ShammyVerse/scripts/maintain_project.py) uses `git add --all` in publish mode. This working tree already has unrelated asset work. | Keep validation separate; make the intended change set visible and explicitly selected before a checkpoint. |
| Save and progression code know game-specific state | [adventure_save.gd](../../ShammyVerse/game/scripts/adventure_save.gd) validates named quests, bounded game counts, and world modules. | Extract save transport and recovery only after defining game-owned payload boundaries. Avoid copying ShammyVerse rules into a generic service. |
| Remaining quality issues can outlive passing checks | [v005](../../ShammyVerse/Design/Iterations/quality-pass-v005/DESIGN_LOG.md) retains flipper/contact limitations despite passing topology and motion-preservation checks. Working-tree v019 addresses some of them with stated flat-ground limits. | Track visual debt separately and add a review scenario that directly exposes the defect. |

## First process experiments

1. Use one iteration record for the next change, including its canonical source and behaviors to preserve. Success: another contributor can identify the correct starting asset without searching historical prose.
2. Catalog the maintained smoke, save, progression, and active-asset suites. Success: one documented selection explains what was tested and what was skipped.
3. Keep a one-page current-state summary with links to history. Success: it contains no conflicting current versions or obsolete control descriptions.

These improvements are tracked with completion criteria in the [backlog](IMPROVEMENT_BACKLOG.md).
