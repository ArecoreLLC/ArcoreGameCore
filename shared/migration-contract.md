# Assisted migration contract

## Inputs

Record the source repository/revision, engine and language versions, target engine/version/platform, 2D or 3D scope, asset ownership/licenses, dependency inventory and one small vertical slice. Pin tool versions per run; do not assume a workflow's documentation is an export compatibility guarantee.

Capture the source behavior before editing: input sequence, expected state transitions, screenshots/video when useful, and frame-time/load-time baselines on named hardware. Agree numeric tolerances before comparison. Use isolated test saves and never overwrite a player's real save.

## Work packet (small context)

Read the selected workflow guide/example and dimension catalog. Then load only the files for the slice, direct dependencies, relevant API contracts and existing tests. Include a path list and acceptance criteria; link bulky logs rather than pasting them into every prompt. Save new decisions with their reason and affected paths. Reopen wider context only when a dependency or failing test requires it.

## Outputs

1. An inventory and source-to-target mapping, including unsupported features and manual rebuilds.
2. One implemented slice in the consuming game's working branch, plus tests and reproducible build commands.
3. A parity report and a decision to expand, revise or stop. The workflow documents alone do not satisfy these outputs.

Example evidence record (illustrative, not an executed result):

```json
{
  "workflow": "phaser-to-godot",
  "source_revision": "record-actual-sha",
  "target_revision": "record-actual-sha",
  "engine_versions": {"source": "record-version", "target": "record-version"},
  "checks": [
    {"id": "jump-parity", "status": "not_run", "command": null, "artifact": null}
  ],
  "decision": "pending"
}
```

Use `passed`, `failed`, `blocked` or `not_run` per check. `passed` needs a command or reproducible manual procedure, actual result and evidence artifact tied to the target revision. A successful build is not a passed playtest. Never label a future or illustrative command as executed.

## Completion gate

All agreed checks must pass on the named target platforms, or the user must explicitly accept the listed exceptions. Track total elapsed time and agent tokens per verified slice, including retries. Do not claim a token reduction without a comparable measured baseline.
