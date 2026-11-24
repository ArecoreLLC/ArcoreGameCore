# Stroke geometry and motion utilities

Version: 0.1.0. Runtime: Godot 4 (validated on 4.7.2). Dependencies: none.

Pure stroke storage and geometry/motion math, extracted from Ink Fury. No autoloads,
scenes, tuning files, global class registrations, or consumer resource paths.
Copy this folder anywhere in a Godot project; all imports are relative.

See [API.md](API.md) for contracts and [REUSE_REVIEW.md](REUSE_REVIEW.md) for boundaries.
From an empty project containing the staged tree at addons/gamecore:

```powershell
godot --headless --path <empty-project> --script res://addons/gamecore/strokes/tests/run_tests.gd
```

Success: `STROKES_0.1.0_PASS 92 checks`, exit 0. Tests require no import or autoloads.
Coverage: lines, circles, arches at 30/60/120/240 Hz; resampling endpoints;
translation/scale invariance; DTW identity; empty inputs; timestamp repair;
window mean/median; nine comparisons against the legacy direct-DFT SPARC reference.
