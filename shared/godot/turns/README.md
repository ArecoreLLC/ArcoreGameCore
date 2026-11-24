# Turns 0.1.0

Dependency-free Godot 4 value-state turn helpers. No autoloads, global class names,
consumer resource paths, RNG, clocks, or battle policy. Copy this directory into
`addons/gamecore/turns`. Both scripts extend the engine's `RefCounted` directly.

## API

Preload `cooldowns.gd` and `turn_driver.gd` relative to your consumer script.

- `remaining(counters, key) -> int`: missing keys return zero; keys are opaque.
- `committed(counters, armed = {}) -> Dictionary`: subtract one from existing
  counters, remove nonpositive results, then replace counters with positive armed
  durations. Zero/negative armed durations are ignored, not cancellation requests.
  Inputs are untouched. Invoke only for accepted turns; eligibility, duration caps,
  and which actions consume turns belong to the consumer.
- `preview(state, action, reducer) -> Dictionary` and `commit(...)`: identical pure
  evaluations. Reducer receives deep-copied dictionaries and returns
  `{"next": Dictionary, "resolution": Dictionary}` or `{}` for rejection.
  The result is also detached. Commit does not mutate the caller: adopt `next`
  explicitly. Reducers own validation, transitions, and any counter updates.
- `choose_best(candidates, scorer, fallback = null)`: strict highest score;
  preserves first candidate on ties. Empty/all -INF/NaN returns fallback.
  Scorer receives the candidate directly and must not mutate it.
- `simulate(initial, chooser, reducer, terminal, max_steps = 100)`: bounded replay.
  Chooser receives state and returns an action dictionary. Terminal receives state
  and returns bool. Both receive isolated snapshots. Returns `state`, `trace`
  (action/resolution pairs), and `reason` (`terminal`, `rejected`, `limit`).
  Terminal is checked before choosing and after the budget; zero/negative budgets
  commit nothing. Rejection stops immediately. No implicit retries or random seed.

## Integration and limits

InkFury BattleState uses this driver for its common preview/cast evaluation and
committed counters after acceptance. BattleTactics uses stable candidate selection.
InkFury owns all eligibility, power, damage, elements, statuses, phase changes,
cooldown caps, and tactical score weights. Preview intentionally excludes InkFury's
post-commit phase/status bookkeeping, preserving its existing public behavior.

State/action/result trees must contain value data only. Deep duplication does not
isolate Objects/Resources or callback-captured external state. Callbacks must be
deterministic and must not change external state. Malformed reducer results are
programmer errors, not silently accepted turns. Full-state copies trade allocation
cost for isolation; this is intended for bounded turn games and balance fixtures,
not high-frequency physics. No registry publication or external dependency needed.

## Standalone verification

Copy `staged/shared/godot` to `addons/gamecore` inside an otherwise empty project
with a `project.godot` containing `config_version=5`. No InkFury data or classes
are needed. From that project directory run (substitute your Godot executable):

```powershell
& 'X:/Projects/ShammyVerse/tools/godot/Godot_v4.7.2-stable_win64_console.exe' --headless --path . --script res://addons/gamecore/turns/tests/test_turns.gd
```

Expected: exit 0 and `PASS gamecore.turns 0.1.0 (22 checks)`, with no script errors.
Tests cover a warehouse station rotation and a separate budget planner: isolation,
preview/commit parity, counter timing, expiry/rearming, rejection, deterministic
replay, bounded/terminal runs, stable ties, and empty/nonfinite score fallback.
