# Recoverable checkpoints

Version: **0.1.0**. Godot 4 GDScript, no autoloads, global class registration,
consumer resource paths, or game model dependencies. Entry point: `checkpoint_store.gd`.

## Contract

Preload the script relative to your adapter and construct it with a path prefix.
Call `load_value(validate)` before saving an existing prefix. It returns the restored
value or `null`. `save_value(value, encode, validate)` returns a verified-write boolean.
Callbacks are passed per operation (bind application context as needed):

- `encode(value)` returns JSON-compatible data. Sanitization belongs to the adapter.
- `validate(parsed_json)` returns the restored value, or **null** to reject it.
  False, zero, and empty containers are valid restored values. Callbacks should be
  deterministic, synchronous, and free of side effects; callback errors are not caught.

Files are `<prefix>.a.json` and `<prefix>.b.json`. The envelope contains positive
integer `sequence`, JSON text `payload`, and the payload's SHA-256 `checksum`.
Existing InkFury run checkpoints require no migration. Bounds: 262144 UTF-8 bytes
per envelope, sequence 1 through 1000000000. Equal sequences prefer A.
`read_entry(slot, validate)` exposes `{value, sequence}` or `{}`.

`load_value` resets `sequence` and `active_slot`, then picks the highest valid
sequence. `status` is `new` (neither file exists), `unreadable` (files exist, none
valid), `restored`, or `recovered` (valid value plus an invalid existing slot).
Saving does not change this load status. The first save targets A; subsequent saves
overwrite the inactive slot. Flush, close, checksum verification, and callback
validation must succeed before active state advances. Failures return false and
leave the active slot untouched. Oversize writes and exhausted sequences fail
before opening a destination. Parent directories are not created.

## Standalone test

From the InkFury repository root in PowerShell, copy the entire staged Godot tree
into a new disposable empty project (no game assets or autoloads needed):

```powershell
$fixture = Join-Path (Get-Location) ('build/checkpoints-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force "$fixture/addons/gamecore" | Out-Null
Copy-Item tools/gamecore-contribution/staged/shared/godot/* "$fixture/addons/gamecore" -Recurse
$userDir = ($fixture + '/userdata').Replace('\', '/')
@"
config_version=5
[application]
config/name="CheckpointsFixture"
config/use_custom_user_dir=true
config/custom_user_dir="$userDir"
[rendering]
renderer/rendering_method="gl_compatibility"
"@ | Set-Content "$fixture/project.godot" -Encoding utf8
& 'X:/Projects/ShammyVerse/tools/godot/Godot_v4.7.2-stable_win64_console.exe' --headless --path $fixture --log-file "$fixture/test.log" --script res://addons/gamecore/checkpoints/tests/test_checkpoints.gd
```

Expected marker: `CHECKPOINTS_STANDALONE_PASS (74 checks)` and exit 0.
The test uses synthetic dictionaries and writes only below the fixture's `res://`.
It covers alternation, restart, truncated/invalid JSON, checksum and type failures,
validator rejection, sequence bounds/ties, UTF-8 limits, recovery followed by save,
open failure, state preservation, and non-null falsy callback results.
Check logs for script errors even when Godot returns zero.

## Limits

Single writer only; no locking, concurrent-writer coordination, transaction across
files, or automatic discovery on save. Call load first when reopening an existing
prefix. Checksums detect accidental damage, not malicious edits (sequence is not
checksummed). Flush/readback is not a power-loss durability guarantee or OS fsync.
A failed save may damage the inactive slot; only the active valid generation is
protected. Validation rejection is tested; actual disk-full/short-write/power-cut
faults are not injected. No automatic pruning, migration, encryption, or null-valued
payload restoration. Tested on Godot 4.7.2; other Godot 4 versions are unverified.
