# Recorded input replay

Version: 0.1.0. Runtime: Godot 4 (validated on 4.7.2).
Dependency: sibling `../strokes` module, version 0.1.0.

Validated compact stroke encoding/decoding, JSON record parsing, and replay through
a caller-supplied evaluator. No glyphs, tiers, session policy, file discovery,
reporting, autoloads, global class names, or consumer resource paths.

See [API.md](API.md) and [REUSE_REVIEW.md](REUSE_REVIEW.md).
Copy the staged shared/godot tree to addons/gamecore in an empty project:

```powershell
godot --headless --path <empty-project> --script res://addons/gamecore/replay/tests/run_tests.gd
```

Success: `REPLAY_0.1.0_PASS 65 checks`, exit 0. No import required.
Tests cover roundtrips at 24/90/240 Hz, two synthetic evaluators, missing legacy
tilt, malformed arrays/types, nonfinite and storage-overflow values, decreasing
times, atomic failures, invalid JSON, callback validation and explicit errors.
