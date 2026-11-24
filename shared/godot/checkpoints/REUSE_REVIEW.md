# Reuse review - checkpoints 0.1.0

## Extraction boundary

`checkpoint_store.gd` owns only envelope I/O, bounded reads/writes, SHA-256,
alternating generations, readback validation, and recovery state. It references no
RunState, Profile, InkFury classes, or consumer resource paths. It needs no plugin
registration. `game/addons/gamecore/checkpoints/checkpoint_store.gd` is a byte-identical
vendored copy; change both copies together. Tests and review documentation remain staged.

`game/core/storage/run_save_store.gd` is the game adapter. It inherits the generic
store via a relative extends path and injects RunSaveCodec.snapshot and
RunSaveCodec.restore bound to the current combat configuration. The old constructor,
path(), MAX_BYTES, prefix, sequence, active_slot, status, load_run(), save_run(), and
_read() run-key result remain available. The existing disk envelope is unchanged.
Preflight size/sequence rejection now avoids destroying an inactive generation for
a write that the old implementation would write and then reject during readback.

## SampleStore compatibility decision

`game/core/telemetry/sample_store.gd` is intentionally unchanged. Its static API
uses main, .tmp, then .bak in that priority order, with a `sha256` key and no sequence;
it creates parent directories, sanitizes telemetry, rejects empty dictionaries,
copies the main file to backup, and renames the temporary file into place. Replacing
this with alternating slots would change both legacy on-disk compatibility and
recovery selection (a valid main intentionally wins over a newer temporary file).
Those semantics require a separately scoped migration or separate protocol component.

## Evidence and integration gate

Read existing test_run_saves.gd, test_story_samples.gd, test_telemetry.gd, and the
headless runner before extraction. Existing run tests cover battle/Forge/Camp/retry
restoration, invalid schemas, alternating slots, corruption, write failure, and new
runs. Existing story sample tests cover main corruption recovering the backup.
The new standalone fixture exercises generic persistence without any game types.

Full game tests are deliberately deferred to the parent until concurrent agents
converge. Run `tools/test-game.ps1` then, with workspace-local user data configured
if external writes are prohibited. No external GameCore registry, installation,
publication, or commits are part of this extraction.
