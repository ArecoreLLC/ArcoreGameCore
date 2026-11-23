# Animal pipeline v1 — manifest, resume and review

Implemented: Python CLI and GameCore drawing_production MCP operations. Scope:
trusted local orchestration of consumer adapters. No automatic anatomy, in-game
upload UI or publication. The existing video wizard/Flow stages are unchanged.

See [validation evidence](ANIMAL_PIPELINE_VALIDATION.md) for executed checks and
explicitly untested consumer stages.

## Manifest contract

Required: `schema: gamecore.animal.v1`, slug `animal_id`, absolute existing
`workspace`, ordered `stages`. Optional: workspace-relative `state_dir` and a
`toolchain` version record. Paths resolve from workspace, never the current shell.
Each stage has a unique `id`, `kind` (command/review), and explicit input file paths.
Include adapter code, shared helpers, exact song and relevant runtime settings.
Undeclared dependencies cannot be detected automatically.

Commands specify `argv` (string array), required `outputs`, optional `cwd` and
`timeout` (1–14400 seconds; default 1800). Substitutions: `{python}`, `{workspace}`,
`{animal}`. No shell interpolation. Pin executable paths/versions; include tool
binaries as inputs when their byte changes must invalidate results.

Outputs are `{path, kind: file}` or `{path, kind: json, expect: {status: passed}}`.
Every output must exist and be nonempty; JSON must parse, and declared top-level
expectations must match. Adapters must await external jobs: a queued receipt is not
completion. Output/state/cwd paths stay within workspace; read inputs may be external.
Commands are trusted project code, not sandboxed by these path checks.

Review stages specify `gate`, evidence in `inputs`, and `instructions`. Exactly
three gates occur in this order:

1. `reference-guides`: reference identity, authored guides, palette/paper masking.
2. `companion`: study progression, matching 3D proportions, animation and reveal.
3. `payoff`: actual gameplay and song/video, sound, movement, readability.

Generate review evidence before its gate. Never consume a later stage's output.
Record the true reviewer; do not attribute an agent inspection to the owner. Tests
never grant visual approval. For personal art, the first gate can explicitly review
the choice to skip shapes. This full animal schema still requires all three gates;
an art-only manifest is a future narrower contract.

## CLI and MCP

```powershell
python tools/drawing-studio/animal_pipeline.py validate C:/MyGame/animals/fox.json
python tools/drawing-studio/animal_pipeline.py status C:/MyGame/animals/fox.json
python tools/drawing-studio/animal_pipeline.py resume C:/MyGame/animals/fox.json --through maps
python tools/drawing-studio/animal_pipeline.py review C:/MyGame/animals/fox.json --stage reference-review --decision approve --reviewer artist --notes "Inspected reference and overlay; head/body align and pale fur is retained."
python tools/drawing-studio/animal_pipeline.py resume C:/MyGame/animals/fox.json
```

CLI resume runs synchronously until the next review/failure/completion. Exit zero
can mean needs_review; inspect JSON status. Reject with `--decision reject` and
actionable notes. No approve-all or GPU-bypass option exists.

Register only GameCore hub. Discover `drawing_production` with operation tools/list,
then animal_guide. All calls use `{operation, arguments}`:

| Operation | Arguments | Result |
|---|---|---|
| animal_validate | manifest | Structural check, no execution |
| animal_status | manifest | Rechecked stage hashes, next action, evidence/log paths |
| animal_resume | manifest, optional through | Background worker receipt or current gate/status |
| animal_review | manifest, stage, decision, reviewer, notes | Artifact-bound review and updated status |

Example: `{"operation":"animal_resume","arguments":{"manifest":"C:/MyGame/animals/fox.json"}}`.
Poll animal_status with the same manifest. States include pending, running, passed,
failed, interrupted, invalid_artifacts, needs_review, blocked_dependency; overall
completion is complete. A job's finished worker can still have a needs_review result.
On an early launch failure inspect returned job_file and adjacent worker.log.

Manifests execute local code. Inspect trusted configuration before resume. Never
execute an uploaded artwork file as a manifest. Keep secrets out of argv/config/logs.
Provider operations use the hub registry; no direct downstream MCP registration.

## Resume guarantees and limits

The fingerprint includes runner code/version, animal, declared toolchain, stage
config, input SHA-256 hashes and the previous verified result/review. Skip only if
the key and every output hash match. Corrupt/missing outputs rerun; missing inputs
stop with their path. A changed reference invalidates its review and downstream work.
This is a conservative linear pipeline, not a minimal-invalidation dependency graph.

Review records retain reviewer, notes, timestamp and artifact fingerprint. Approval
is never imported from old prose or filenames. Each execution preserves configuration,
log, elapsed time and result under runs/. Writes are atomic; locks prevent concurrent
writers. Dead locks recover, but a recorded live child process blocks restart.
Adapters spawning grandchildren own cancellation/recovery; check provider jobs before
retrying externally interrupted work. The runner stops at failures without endless retries.

Elapsed time is measured. Token usage is not inferred from log size; per-stage token
telemetry remains future work. Drive uploads, reference generation, model authoring,
automatic QA packets and minimal invalidation are also outside this first increment.

## Consumer example

ShammyVerse's unicorn manifest covers timed maps, hub drawing studies, validation of
existing companion assets, source-game tests, protected capture and hub ModelForge
archive checks. Model authoring remains manual; changed model/reference hashes require
fresh validation and appropriate review captures. Private assets stay in the consumer.
See the [assisted shapes design](../../workflows/game-music-video/assisted-shapes.md)
for the user-facing walkthrough; the game UI is not implemented by this command.
