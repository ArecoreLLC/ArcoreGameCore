# Remaining ShammyVerse procedures: reuse review

Reviewed 2026-11-22 under [reuse suitability policy](../../../shared/module-specialization.md).
Scope: all five candidates remaining after world-life 0.4.0. The registry records
decisions and limitations; candidate status never means an installable module.

| Procedure | Decision | Shared responsibility | Game responsibility / next condition |
|---|---|---|---|
| Reef route clearance | extract-adapter | Finite terrain ring sampling with injected height field | Islands, species margins, spawn search and quality stay in reef_life.gd |
| Lyric world cues | extract-adapter | Current interval identity, rewind handling and duplicate suppression | Words, cooldowns, story/region gates and effect cleanup stay in gameplay_world_effects.gd |
| Save rotation | retain; game-owned candidate | Potential future validated JSON rotation with injected schema validator | Current validation reaches quests, rocks, origin memories and world systems; snapshot/restore/UI are game-specific |
| Flight clearance | retain; game-owned candidate | No additional general module justified yet | Wing names, rest axes, torso dimensions, authored sweep and flying state are Poofy-specific |
| Character authoring | retain; game-owned candidate | Possible geometry/color primitives after a separate authoring review | Artist resets the Blender scene, seeds global RNG, sets Body/Head rig and materials, imports private character_export from an absolute project path |

## Alternate-use assessment and acceptance conditions

Terrain sampling was exercised with different elevations, density and callbacks;
cue observation was exercised with tutorial intervals rather than lyric content.
These are synthetic fixtures, not second-game validation. Both retain original
default behavior and now ship as world-life 0.5.0. See the [API guide](ROUTE_CUE_MODULES.md).

Save rotation remains unchanged. Before extracting, isolate filesystem operations
and inject failures at temp open/write/flush, backup removal, primary rename and
final promotion/rollback. Verify that at least one validated recoverable save
survives each failure, including corrupt primary + valid backup and interrupted
previous writes. Tests must use temporary directories, never player saves. Schema,
slot selection, recovery messages and New Game replacement policy stay game-owned.
Alternate-schema and failure-injection validation: **not_run**; no shared save
module or certification is claimed.

Flight correction needs a second rig with different bone naming/rest axes and
measured bounds before a shared API would be justified. Parameterizing every
constant now would conceal a rig-specific algorithm. Alternate-rig validation:
**not_run**. Existing helper remains unchanged and is discoverable as game-owned.

Character authoring needs explicit scene ownership (no implicit deletion of an
unrelated scene), local random generator, injected exporter/output path, and
separation of species rig/material policy from geometry primitives. Exercise an
alternate rig/material/exporter in an isolated Blender scene before extraction.
Alternate-authoring validation: **not_run**. No art, private exporter or resources
were copied to GameCore.

Consumer evidence lives in ShammyVerse's `Design/Iterations/gamecore-reuse-v003`.
Remaining candidates have a `disposition: game-owned` and a reason in MCP details,
so future agents can distinguish a reviewed decision from an unreviewed backlog.
