# Validation and evidence guide

Choose checks according to the change. Record the command, prerequisites, tool version, scenario, result, and evidence path in the iteration record. A passing structural check does not establish visual quality, and a render does not establish gameplay performance.

## Checks by change type

| Change | Minimum relevant checks | Review evidence |
|---|---|---|
| Character geometry/material | Import; finite geometry/normals; weights; retained palette/data; preserved properties | Consistent views, close-up, gameplay distance, representative poses |
| Animation/rig | Clip names/durations; sampled actual bone motion; attachments; transitions | Multiple motion phases, ground/contact views, interaction with accessories |
| Gameplay/progression | Start/boundary/completion; invalid/repeated inputs; reset/cancel; neighboring unlocks | Playable path and fixture setup description |
| Persistence | Isolated path; fresh-process restore; invalid data; backup; reset cancellation; version behavior | Saved fixture, result log, recovery behavior |
| Audio/captions | Cue bounds; real playback transitions; mute/skip; layout; exact recording identity | Separate listening status and unmatched-line record |
| Rendering/performance | Engine render; representative scenes; changed quality tiers; affected contact checks | Matched captures and hardware-specific measurements |
| Documentation | Correct source claims, links, paths, commands, and current/historical labels | Read-through and link/whitespace checks |

## ShammyVerse reference commands

These commands describe the existing Godot project, not a future engine adapter. Run from the ShammyVerse repository root with its local tools installed.

```powershell
# Existing maintenance selection: import plus four named regression suites.
python scripts/maintain_project.py

# Fresh read-only smoke scenario, with no save override inherited.
Remove-Item Env:SHAMMYVERSE_SAVE_PATH -ErrorAction SilentlyContinue
$frameworkGodot = @(Get-ChildItem '.\tools\godot\Godot*_console.exe')
if ($frameworkGodot.Count -ne 1) { throw 'Select exactly one project Godot console executable.' }
& $frameworkGodot[0].FullName --headless --path '.\game' -- --smoke-test
```

Use a dedicated terminal for fixture environment settings. Persistence tests require an explicit disposable save path and may create backups or slot siblings; never supply a real player save. Follow the [autosave record](../../ShammyVerse/Design/Iterations/autosave-v001/DESIGN_LOG.md) for its write-then-read sequence, and [difficulty/slots](../../ShammyVerse/Design/Iterations/difficulty-slots-v001/DESIGN_LOG.md) for later behavior.

The current maintenance selection is defined in [maintain_project.py](../../ShammyVerse/scripts/maintain_project.py). It is not a full campaign, save, performance, or release check. Its `--publish` mode stages all changes and performs Git/network operations; it is not part of this validation workflow.

## Maintain an explicit suite registry

Proposed registry fields: stable suite ID, purpose, owner, source path, command, prerequisites, active/superseded/archived status, replacement ID, expected output, timeout, and evidence directory. Label suites that need rendering, audio, isolated persistence, or real-time timing.

Use separate selections for quick smoke, affected feature regressions, broader milestone regression, and manual/release review. Archived iteration tests remain useful evidence, but may describe intentionally replaced behavior. Test failures must be investigated before changing assertions or marking a suite superseded.

## Performance evidence

Measure normal playback in representative and demanding scenarios. Record hardware, OS, engine, renderer, resolution, quality, VSync/cap, sample duration, warm-up, and p50/p95/p99 frame times where available. Keep CPU, GPU, collision-step, and wall-clock measurements distinct. Compare like-for-like runs.

ShammyVerse's 120+ FPS target and local RX 7900 GRE measurements are project-specific references, not defaults or guarantees for future games. Fixed-frame tests, headless runs, and movie captures are unsuitable as proof of live frame rate. See the [performance budget](../../ShammyVerse/Design/PERFORMANCE_BUDGET.md).

## Record outcomes honestly

Use `pass`, `fail`, `not run`, or `not applicable` per check. Include a reason for omissions. Separate old log results from a new run. Record actionable warnings with their affected scenario and follow-up; do not silently treat every warning as either harmless or a release blocker.
