# Shared module and common workflow pilot

Implemented and validated November 11, 2026. Baseline GameCore revision:
`be8748519106250dee0adc70d0aedbfa1a9d9983`, plus existing working-tree additions
and modifications retained in place. Environment: Windows, Python 3.14.0,
Unreal 5.8.4 CL 58902052, Win64 Development Editor targets.

## Changes

- Cataloged 12 existing portable headers in `shared/modules.json` with initial
  versions, SHA-256, documentation, test references and known consumers.
- Added explicit dependency installation, local-edit protection, version-change
  review and offline installed-byte checking.
- Added one structured Unreal runner for preflight, build, automation and smoke,
  including bounded execution and fresh source/evidence receipts.
- Migrated Dungeon Dash Market's StockLedger from sibling source inclusion to a
  locked local header. Migrated Critter Contraptions' ProductionClock to the same
  lockfile and workflow. Both native Build.cs rules check local dependency hashes.
- Preserved the pilot Build/Test script entry points and Critter's rendered/SDK
  switches. No game rules, save schemas or production assets were changed.

See [usage and contracts](../shared/module-registry.md) and the
[machine-readable pilot evidence](module-workflow-pilot.json). That record includes
exact native commands, per-run receipt paths/hashes, test names and elapsed times.
Receipts retain source/config/script/content hashes and original logs in each game.

## Executed game checks

Commands were invoked from each game's root:

```powershell
./Scripts/Build.ps1
./Scripts/Test.ps1
```

| Pilot | Editor build | Automation | Headless gameplay smoke |
|---|---|---|---|
| Dungeon Dash Market | passed | StockTransactions and SaveRoundTrip passed | combat, loot, restock, sale, disk reload, upgrade rejection, defeat/retry passed |
| Critter Contraptions | passed | AutonomousTenItems and ProductionClock passed | CRITTER_SMOKE PASS observed; no fail marker |

The first Dungeon build failed because direct System.Text.Json use in Build.cs
required an assembly outside UBT's rules references. Both pilots now use
EpicGames.Core.JsonObject. The successful rebuild and original failed receipt are
retained; the failure is not hidden or reclassified.

Framework checks: workflow validator, wizard validator, MCP registry structure,
and Python regression discovery. The final local log directory is referenced in
`module-workflow-pilot.json`. New regressions cover dependency drift, unmanaged
files, local edits, version changes, path escapes, cycles, empty/failed/missing
automation, smoke failure markers and fresh retained failure receipts.

## Not run / next milestones

No packaged build, visual acceptance, audio audition, controller-hardware or
multiplayer tests were run for this change. No asset-provider calls were made.
The two games still use distinct rules; this is validation of common dependency
delivery and execution, not proof that one gameplay API fits both games.

Build before testing after source changes. The runner does not rebuild implicitly.
Existing outputs and historical validation records are preserved. Elapsed times
are run measurements, not a claimed speedup against an unmeasured baseline.
