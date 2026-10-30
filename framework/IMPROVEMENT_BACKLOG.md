# Framework improvement backlog

Initial backlog, 2026-10-30. These are proposed follow-up changes; creating this framework has not refactored ShammyVerse or changed its validation runner. Assign an owner and record results when starting an item.

Priority 1 improves reliable reuse; priority 2 reduces recurring work; priority 3 proves the framework in another game.

| ID | Priority | Improvement | Completion evidence | Status |
|---|---|---|---|---|
| F01 | 1 | Establish a current-state index and active asset registry | One authoritative entry per active asset identifies editable source, runtime file, builder or external-edit path, review state, and current behavior. Historical notes are labeled. | Proposed |
| F02 | 1 | Catalog maintained regression suites | Smoke, save/slots, progression, and active-asset suites have exact commands and prerequisites; obsolete fixtures name their replacements; a selected run records skips and failures. | Proposed |
| F03 | 1 | Track reproducible tool setup outside ignored binaries | A clean checkout can identify required versions/hashes and setup steps, launch the project, and run smoke checks without relying on the original machine's paths. | Proposed |
| F04 | 1 | Formalize source handoffs after external edits | One asset record traces original source, external edits, canonical editable version, valid scripts, and runtime output; preserved properties are checked. | Proposed |
| F05 | 2 | Separate checkpoint selection from broad publication | A reviewed change set excludes unrelated work; validation remains usable without staging or network; publishing reports exactly what it includes. | Proposed |
| F06 | 2 | Maintain visual and audio review debt | Each open issue names a version, observable defect, review scenario, and acceptance criterion; functional passes do not automatically close editorial/art items. | Proposed |
| F07 | 2 | Build a representative performance matrix | Repeatable gameplay scenarios include busy interaction and demanding views; quality tiers have comparable frame-time records on selected hardware. | Proposed |
| F08 | 2 | Define small runtime component contracts | One candidate identifies game-independent inputs/outputs and game-owned rules, with cancellation and persistence boundaries documented. | Proposed |
| F09 | 3 | Select and prove the next engine adapter | An engine decision plus one animated asset, interaction, isolated save round trip, and packaged launch demonstrates the pipeline. | Proposed |
| F10 | 3 | Pilot the framework on a second game | A playable slice uses the templates; a retrospective identifies reused strengths, remaining coupling, and concrete guide revisions. | Proposed |

## Suggested order

Start F01 and F04 with the next asset iteration. Build F02 before describing any command as a comprehensive regression run. Complete F03 before handing the framework to another machine. Resolve the engine decision before F09 implementation, then use F10 to determine which runtime components are worth extracting.

## Review cadence

At each playable milestone, review open items against actual rework and defects. Keep the highest-value next action small enough to complete in one iteration. Move completed items to a dated record with evidence; avoid leaving a growing list of checked boxes without an outcome.
