# Animal pipeline v1 validation — 2026-11-22

Baseline: GameCore HEAD `ab904061ef1969765480e173e6c394024525fec2`, with existing
uncommitted Drawing Atelier/MCP changes preserved. New code is an uncommitted working
tree increment. Platform: Windows, Python 3.14; consumer game Godot 4.7.2. Scope is
CLI/MCP orchestration and one consumer manifest, not an interactive guide UI.

| Check | Result | Evidence / command |
|---|---|---|
| Animal runner regression suite | passed, 19 tests | `python -m unittest discover -s tools/drawing-studio -p test_animal_pipeline.py -q` |
| Drawing production compatibility | passed, 7 tests | `python -m unittest discover -s tools/drawing-studio -p test_production.py -q` |
| Workflow integrity | passed | `python tools/validate_workflows.py` |
| Wizard integrity | passed, 14 templates | `python tools/validate_wizards.py` |
| Registry structure | passed | `python tools/mcp_registry.py` |
| Scaffold regression suite | passed, 163 discovered, 1 skipped | `python -m unittest discover -s tools/tests -v`; optional Godot world-life component test skipped without GODOT env |
| Hub Rust tests | passed, 15 tests | `cargo test --manifest-path hub/src-tauri/Cargo.toml` |
| Deployable debug MCP executable | passed | `cargo build --manifest-path hub/src-tauri/Cargo.toml --bin gamecore-library` |
| Actual hub discovery/validation/status | passed | drawing_production animal_guide, animal_validate and animal_status through built gamecore-library.exe --mcp |
| Actual hub async resume | passed | Unicorn map generation passed, stopped at reference-review; repeat resume left state bytes unchanged |
| Companion, full capture and archive through new manifest | not_run | Later stages intentionally require fresh artifact-bound reviews; ModelForge provider was unreachable at discovery; no GPU-reset bypass |
| User-facing circle/oval editor | not_run | Interaction design documented; game UI not implemented |

Runner tests cover reviews, changed inputs/adapters, corrupt outputs, queued receipts,
command failure, timeout, live/stale locks, forward dependency rejection, path escape,
async worker completion and conservative downstream invalidation. Tests use temporary
synthetic fixtures; their review approvals are not production artwork approvals.

Consumer evidence stays in ShammyVerse `.gamecore/animals/unicorn/` with immutable
attempt logs, state and jobs. The delivered manifest remains at reference-review;
no prior owner or agent review was retroactively claimed as a new approval.

Elapsed durations are stored per command. Actual token usage is unavailable from
this runner and is not estimated or represented as measured savings.
