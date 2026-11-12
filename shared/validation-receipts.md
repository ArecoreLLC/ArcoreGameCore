# Source-pinned validation receipts

`tools/capture_validation.py` records consumer-owned check declarations alongside
SHA-256 hashes of selected sources and evidence. Use it for small slices in any
engine, including workspaces without Git. It never executes a supplied command,
imports consumer code, or upgrades a declared status.

Create a JSON array of checks containing `id`, `status`, `command` and `artifacts`
(paths relative to the consumer root). Allowed statuses are `passed`, `failed`,
`blocked`, and `not_run`. Passed checks need a nonempty command and nonempty
evidence files. Choose sources explicitly; do not include credentials or saves.

```powershell
python tools/capture_validation.py --root C:/Projects/Example --source Source --source Config --checks C:/Projects/Example/Docs/checks.json --output C:/Projects/Example/Docs/Evidence/run-001.json
```

Output uses exclusive creation to preserve older receipts. Source and evidence
paths must resolve inside the consumer, including symlink targets. Capture after
checks finish and before editing sources again. A receipt establishes file
identity, not that the declared command actually ran against that baseline;
review its logs. Keep build, automation, rendered play, multiplayer, and packaging
separate. Missing gameplay evidence must remain `not_run` or `blocked`.
