# Six interaction extractions: validation and reuse review

Reviewed 2026-11-24 on Windows, Python 3.14 and Godot 4.7.2 stable.
Workflow: game-project-integration; scope: 2D consumer and engine-independent
math/state helpers. Consumer baseline: InkFury
`b475b9e06aed8481a9b7465d5a1b70633786d3e5` plus the six pending extractions.
Version 0.1.0 for all modules; exact shared source bytes are pinned in
`shared/interaction-modules.json` and the consumer's
`GameCore.interaction.lock.json`. No authored assets, player data or credentials
are included in this publication.

## Boundary decisions

All six use **extract-adapter**. Stable helpers are shared; game policy remains
in the consumer. No vendor forks are required.

| Module | Shared responsibility | Consumer-owned policy / adapter |
| --- | --- | --- |
| verified-art-admission | Hash/path/layout validation and staged publication | Art selection, project paths, render policy in tools/install-rendered-batch.py and tools/validate-articulated-batch.py |
| recoverable-checkpoints | Validated alternating save slots and recovery | Run schema and migration in game/core/storage/run_save_store.gd |
| stroke-analysis | Geometry, DTW, point-cloud comparison, motion math | Glyphs, score thresholds and rewards in game/core/scoring; capture adapters in game/core/capture |
| turn-simulation | Value-state preview/commit, bounded simulation and counters | Combat rules, damage and enemy intent in game/core/combat/battle_state.gd and battle_tactics.gd |
| pen-contact-tracking | Contact bookkeeping and recovery calculations | Hardware routing, palm policy and signals in game/autoload/input_router.gd |
| recorded-input-replay | Portable stroke records and replay callbacks | Scoring and telemetry presentation in game/core/telemetry/telemetry_codec.gd and game/tools/replay_telemetry.gd |

Shared GDScript uses relative preloads and no game autoloads or assets. Reducer
callbacks and caller-supplied hardware values are explicit boundaries, not a
second game implementation. Per-module READMEs and REUSE_REVIEW files describe
API constraints and synthetic alternate-use fixtures. The combat adapter needed
explicit bool declarations after dictionary-based reduction replaced typed calls;
this repair does not alter combat policy.

## Executed checks

- **Passed:** InkFury `./tools/test-game.ps1`, including import and
  `godot --headless --path game --script res://tests/run_tests.gd`:
  106 tests, 3,629 checks, no failures or script errors.
  Local evidence: `build/gamecore-full-tests.log` in the consumer.
- **Passed with one skip:** `python -m unittest discover -s
  tools/gamecore-contribution/staged/tools/tests -v` with `GODOT` set:
  20 tests run, one Windows symlink privilege test skipped. This includes all
  five GDScript fixture suites imported/run in a temporary empty project and
  installer tests for changed copies, source tampering and reviewed upgrades.
  Local evidence: `build/gamecore-module-tests.log` in the consumer.

- **Passed:** ArcoreGameCore `python -m unittest discover -s tools/tests -v`
  with `GODOT` set: 208 tests run, one Windows symlink test skipped.
  Consumer-local evidence: `build/gamecore-upstream-tests.log`.
- **Passed:** GameCore `python tools/validate_workflows.py`,
  `python tools/validate_wizards.py`, and `python tools/mcp_registry.py`.
- **Passed:** `python tools/check-gamecore.py` in InkFury and
  `python tools/interaction_modules.py check --project X:/Projects/InkFury`
  in GameCore: six modules and 13 pinned files. InkFury's test wrapper now
  checks the lock before import. Shared source checkout line endings are LF;
  the four legacy-encoded API/review documents were converted to UTF-8.

## Remaining limits

Second-game integration, new Fire-tablet playtesting, Android export, iOS,
cross-engine behavior and performance measurements were **not run** in this
repair. Existing consumer regressions and synthetic alternate settings establish
only bounded reuse evidence. Checkpoint and art installation are single-writer;
input recovery fixtures cannot certify hardware drivers. The Windows symlink
escape test needs a host with symlink privileges. No portability or speedup claim
is made from registry publication or successful source compilation.
