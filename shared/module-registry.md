# Portable module registry and pilot runner

Implemented scope: portable C++ header installation and Unreal 5.8.4 Win64
Editor build, automation and smoke execution. This is the 3D
[game-project integration workflow](../workflows/game-project-integration/README.md).
It does not create projects, package releases, import assets, or implement the planned MCP wizard runner.

## Discover and install

`modules.json` is the canonical catalog of portable rules. Entries
include stable IDs, initial `0.1.0` versions, source SHA-256, documentation, dependencies,
test source references and known consumers. `pilot` maturity and listed test files
are not a claim of fresh test execution or proven second-consumer adoption.

From the GameCore root:

```powershell
python tools/gamecore.py modules
python tools/gamecore.py sync --project X:/Projects/Games/Dungeon-Dash-Market
python tools/gamecore.py check --project X:/Projects/Games/Dungeon-Dash-Market
python tools/gamecore.py doctor --project X:/Projects/Games/Critter-Contraptions
```

The consumer owns `Config/GameCore.project.json`: project identity, exact engine
version, Editor target, selected module IDs/versions/destinations, named required
automation tests, and smoke map/flag/pass/fail markers. It contains no arbitrary
shell commands. Paths are relative to the game; module destinations must be headers
under `Source/`. Dependency modules must be selected explicitly.

Bounded scenarios can set optional `smoke.game_mode` to a native class such as
`/Script/HauntAndHaul.LanternGameMode`. The runner appends a validated `?game=`
override to the smoke map only, preserving the donor's default map/game mode.
Arbitrary URL options, Blueprint paths and command-line fragments are rejected.
Portable canonical headers use LF checkout bytes via `.gitattributes` so Windows
line-ending conversion does not silently invalidate their registry hashes.

`sync` validates registry structure/dependency cycles and selected source hashes,
references and destinations before writing
local headers and `Config/GameCore.modules.lock.json`. Existing byte-identical
headers can be admitted. Different unmanaged files and locally edited installed
headers are never overwritten, including with `--update`. Preserve and reconcile
local edits first. Individual files are atomically replaced and the lock is written
last; an interrupted multi-file update fails the next hash check.

An unrelated module under development does not block admission of pinned selected
modules. `modules` still audits every canonical source. Explicitly selected
dependencies receive the same hash checks; missing dependency selections fail.

For an intentional upgrade, review the canonical source and tests, update the
registry version and hash, select that exact version in the consumer, and run
`sync --update`. The registry currently holds one available version per module;
older installed copies continue to build from their lockfiles. Restore a matching
historical framework revision to reinstall an older release. Removed selections
are not automatically deleted from the game.

Adding modules with `sync --update` can retain historical installed releases when
the entire previous dependency set stays selected at the same versions and paths.
Their installed hashes are checked before any write; those bytes are kept rather
than copied from the current registry. This does not reinstall a missing release,
move its header, accept local edits, or infer historical dependency changes.
New modules still undergo current-registry hash/dependency admission. Clockwork
Courier exercises this path when adopting timing, input and presentation modules
while retaining its original attachment and objective rules. Regression tests in
`tools/tests/test_gamecore.py` cover explicit update, preservation and rejection.

`check` validates installed bytes and selected versions without consulting canonical
framework headers. Normal builds never automatically sync. Both pilots also check
installed hashes inside their native Unreal Build.cs rules, so direct UBT builds
need neither Python nor a sibling GameCore checkout. The convenience runner itself
still requires Python and its GameCore installation.

## Build and test

```powershell
python tools/gamecore.py build --project X:/Projects/Games/Dungeon-Dash-Market
python tools/gamecore.py test --project X:/Projects/Games/Dungeon-Dash-Market
python tools/gamecore.py build --project X:/Projects/Games/Critter-Contraptions
python tools/gamecore.py test --project X:/Projects/Games/Critter-Contraptions
```

`test` runs automation, then a headless gameplay smoke. `automation` and `smoke`
are independently available. Build first after source changes: test commands do
not rebuild binaries, and their source snapshots alone do not prove binary provenance.
`smoke --rendered` runs offscreen rendering; it does
not establish human visual acceptance. The existing pilot `Scripts/Build.ps1` and
`Scripts/Test.ps1` delegate to this runner. Critter's `-Rendered` and
`-SkipSDKSetup` switches remain supported. The old Critter `GameCorePin.json` is
historical; the common lockfile now controls its build and test entry points.

Use `--engine-root` or `ARCORE_UNREAL_ROOT` to select an installation. The runner
checks the exact engine patch version and uses bundled .NET/UBT, retaining UBT's
build mutex. This initial adapter targets the installed UE 5.8 layout and .NET 10.0.
Pilot PowerShell scripts accept `-EngineRoot`; `ARCORE_GAMECORE_ROOT` locates the
runner when the standard sibling layout is unavailable.

Each action gets a unique `Saved/GameCore/<UTC timestamp>-<id>-<action>/` directory:
console and engine logs, automation report when applicable, and `receipt.json`.
Receipts include commands, engine build identity, source/config/script/content
hashes, runner hashes, exit status, elapsed time and artifact hashes. Source changes
during execution invalidate the run. Reports from previous runs cannot satisfy a
new run. Automation must contain every named required test, all matching tests
must succeed without errors, and smoke requires a positive marker with no failure
marker. The existing games retain their disposable test-save behavior.

Timeout defaults to 1,800 seconds per action; override with `--timeout`. On Windows,
timeout/interruption terminates only the process tree launched by that invocation.
Do not run overlapping actions against the same game's outputs. Failed receipts
and logs are retained. Preflight errors occur before a run directory is created.

## Validation and limits

Run `python -m unittest discover -s tools/tests -v` plus the repository workflow,
wizard and registry checks. Tests include changed dependencies, local edit
preservation, unavailable/changed selections, escaping paths, dependency cycles,
missing/failed automation, smoke markers and retained failure receipts.

The two pilots still consume different gameplay rules. This milestone proves a
common installation and execution interface, not semantic reuse of one rule in
two games. Asset sourcing, generic gameplay components, packaging, controller
hardware tests and multiplayer remain separate milestones. Pilot execution evidence
is recorded in `framework/MODULE_WORKFLOW_PILOT.md`.


## Acceptance scenarios and build provenance

A consumer may declare `smoke.required_markers` as ordered log-message prefixes.
Every required stage must occur before final success; echoed command-line arguments,
partial strings, missing stages and runtime errors cannot satisfy acceptance.
`smoke_scenarios` holds named overrides for flag/pass/fail/required markers only.
Use `smoke --scenario navigation` (or `test --scenario navigation`) to select one;
the default smoke declaration is unchanged and the receipt records the scenario.

Build receipts now hash project Editor DLLs and module descriptors. Automation and
smoke require a successful build receipt matching current source/config/content and
binary hashes, and reject binaries changed during a test. Run GameCore `build`
after adopting this runner, even if an older/native build already exists. The old
warning that tests could unknowingly consume stale binaries is superseded by this gate.

Consumers may keep a pinned copy of the runner under `Tools/GameCore/tools` for a
self-contained checkout. Its Python sources are included in build input snapshots;
Python caches are excluded. Canonical module installation still requires the full
GameCore registry; an offline build/test bundle does not implicitly carry that registry.
