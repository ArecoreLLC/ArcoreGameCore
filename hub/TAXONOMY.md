# Classifying the game portfolio

The goal is coverage of transferable capability, not the largest number of genre labels. A game can be a puzzle adventure while demonstrating optical traces, checkpoint recovery, collision switching and accessible feedback. Another water-themed game may demonstrate cargo economics without a reusable fluid simulation. Keep those distinctions explicit.

## Independent facets

| Facet | Record | Why it matters |
|---|---|---|
| Game identity | Stable ID, title, source root, parent/variant, engine/language/version, revision | Prevent duplicate games and select the correct runtime donor |
| Player experience | Genre, perspective/camera, audience, session length, input, solo/co-op/competitive | Find comparable controls and UX without assuming identical implementations |
| Mechanics | Named verbs, states, transition guards, costs, timing, success/failure, reset/persistence | Explain what can actually be reused |
| Simulation | Discrete rules, analytic motion, rigid body, nav grid/navmesh, authority/fixed step | Separate a convincing approximation from a physics/network implementation |
| Presentation | 2D/3D/XR, style, lighting, animation, terrain, effects, audio | Choose compatible render and asset pipelines |
| Delivery | Platforms, builds, dependencies, packaging, saves, accessibility, performance evidence | Estimate integration and validation work |
| Reuse | Exact files/symbols, dependency boundary, engine adapter, license/provenance, donor version | Make a responsible extraction decision |
| Marketing | Reviewed pitch, audience, release description, captures, credits and media clearance | Assemble an accurate portfolio or press kit |

The app provides editable project facets and four capability families: **Gameplay, Presentation, Interaction, Technology**. Stable capability IDs are in `data/taxonomy.json`; display labels can evolve without changing IDs. Engine, visual style and genre should not be substituted for capability evidence.

## Detailed capability atlas, version 2

The first atlas had 57 broad tags. Its 16 empty tags substantially understated the breadth still to explore: a game tagged physics did not establish suspension, rope constraints, soft bodies, flooding or cloth. Version 2 retains those tags as `level: domain` and adds **240 independently assessable capabilities in 30 groups**. Only specific capabilities count in atlas statistics. This is an extensible planning vocabulary, not an exhaustive definition of all games.

The current source audit maps **97 capabilities through 107 game-to-capability links**. **143 capabilities are not yet evidenced**, and none are promoted to fresh verified/reused status. Each new link cites a named mechanic and source boundary. No child capability inherits coverage from its parent domain. A game without a mapped capability may still contain relevant code; investigate before commissioning a duplicate implementation.

| Groups | Distinctions to preserve |
|---|---|
| Ground locomotion; air and water movement | Buffered jumping, moving platforms, grappling, gliding, swimming and zero gravity are separate |
| Combat resolution; weapons and damage; enemy and encounter AI | Telegraphed attacks, parries, hitscan, ballistics, interception, perception, cover and group tactics |
| Squads and strategy; pathfinding | Role orders, hauling, formations, fog of war, grids, navmeshes, flow fields and avoidance |
| Construction and assembly; destruction | Connected parts, swept placement, load solving, support collapse, fracture, repair and persistence |
| Rigid body simulation; water and buoyancy; vehicles | Lift samples are distinct from fluid displacement; arcade driving is distinct from tires, suspension and drivetrains |
| Racing and competition; automation and production | Checkpoints, ranking, ghosts, creature jobs, production clocks, belts and scheduling |
| Economy and logistics; power and settlement | Delivery accounting, queues, recipes, power components, utility distribution, population and traffic |
| Puzzles; quests and progression; turns cards and rhythm; education and adaptation | Reflection, temporal puzzles, quest events, consequence, cards, timing, grading and mastery |
| World generation; rendering and lighting; animation and cameras; audio and music | Scattering, dungeon connectivity, streaming, illumination, rigs, cameras, spatial sound and music stems |
| Controls and accessibility; XR and embodiment | Rebinding, touch, focus, screen readers, reduced motion, observer stations, hands and anchors |
| Persistence and recovery; multiplayer; online services; tooling and reuse | Atomic writes, migration, authority, prediction, rollback, reconnect, matchmaking, replay and modding |

For example, Flotsam Citadel supplies a source candidate for sampled buoyant lift. Tugboat Tumble supplies analytic cargo-roll and salvage behaviors. Neither establishes a fluid solver, flooding compartments or water-current forces. Similarly, Box-Fort's support collapse does not establish runtime mesh fracture or structural load analysis.

Future admission requires the behavior's trigger, inputs/outputs, units and update clock, invariants, failure and reset cases, engine dependencies, platform constraints, revision and evidence. Store performance budgets, licensing constraints and demonstrated second consumers before calling a candidate a reusable foundation. Per-capability cards show an acceptance gate; game mechanic records carry the concrete implementation details.

## Capability maturity

| State | Meaning | Evidence needed to advance |
|---|---|---|
| planned | A concept, dependency or intended feature | A bounded implementation and source location |
| prototype | Partial or exploratory mechanic | Working rules and explicit boundaries |
| implemented | Source exists for the named behavior | Build plus meaningful runtime acceptance on named platform/revision |
| verified | Specific checks passed for this behavior | Evidence references, commands, result, platform, hardware where relevant |
| reused | Successfully adopted by another independent consumer | Second consumer, pinned donor, integration changes and its acceptance results |

Keep build, rule/unit tests, rendered review, full playthrough, multiplayer, controller hardware, packaging and performance as separate checks using `passed`, `failed`, `blocked`, `not_run`. A historical pass may become stale; it does not automatically promote current code. The initial catalog deliberately assigns no fresh verified/reused claims from this audit alone.

## Mechanic record

Each named mechanic has its own stable ID, capability, maturity, rule description, source entry points, reuse boundary and verification note. Describe the trigger and state transition, not just a feature name. For a more complex extraction, extend the rules with numeric units, update clock, event ordering, ownership, prerequisites, reset conditions, failure behavior and test tolerances.

Examples from this portfolio:

| Mechanic | First donor | Critical boundary |
|---|---|---|
| Structural destruction | Box-Fort Brigade | Support graph is portable; collision/debris remain Unreal-owned |
| Light puzzle | Lumen-Weaver | Reflection math is portable; traces and receiver collision are engine-specific |
| Creature automation | Critter Contraptions | Work/resource/fatigue model can detach from creature presentation |
| Combat timing | Scrapshift Arena | Active/recovery windows are distinct from animation, targeting and damage |
| Vehicle assembly | Snap Rally | Connectivity validation is reusable; vehicle physics is arcade motion |
| Buoyancy | Flotsam Citadel / Tugboat Tumble | Fixed-step lift model versus analytic boat roll; neither establishes fluid dynamics |
| Squad control | Pebblekin Command | Role assignment and cooperative tasks; not general crowd avoidance |
| Obstacle racing | Skybound Sabotage | Replicated phases and envelope placement; eight-player/latency acceptance remains open |

## Asset admission

Use the provider as owner, the game as consumer, and the catalog as a decision aid. Record provider asset/collection ID, immutable version and source path. A model admission should additionally establish scale/units, axes, pivot, dimensions, mesh/LOD count, materials/textures, rig and clips, collision, engine compatibility and rights. Audio should identify cue versus source, composer/performer rights, sample rate, channels, duration, loop points, stems, loudness targets and audition status. Unknown fields stay unknown; file extensions/counts do not supply them.

ArcoreModelForge owns 3D model discovery/versioning. ArcoreSoundCore owns source/cue catalogs and licensed deliveries. ArcoreSonicAlchemist owns composition/production/stems. The catalog stores pointers and overall asset descriptions, while curated marketing copies are managed locally. Agent integrations continue through the GameCore hub registry, not new direct downstream MCP wiring.

## Choosing the next small games

The current inventory is strongest in Unreal graybox mechanics, strategy/economy, construction, and a growing Godot character/adventure pipeline. Browser collections already contribute rhythm, memory and learning systems, so those should be evaluated before duplicating them in another game.

Use the atlas gaps as **classification gaps**, not proof that no code exists anywhere. Prioritize a new small game by: new capability value + useful connections to existing systems + realistic acceptance scope − duplicated work − integration risk. Choose one primary new capability, two reused foundations and one visible portfolio demonstration. Require a second consumer before promoting a mechanism to a shared framework.

| Proposed small slice | New capability to prove | Existing foundations to evaluate | Acceptance focus |
|---|---|---|---|
| Lantern Heist | Perception-driven stealth AI and dynamic navigation | Haunt and Haul detection; Lumen-Weaver occlusion | LOS/hearing transitions, search/return, route invalidation |
| Clockwork Courier | Physical vehicle handling and a replay | Snap Rally assembly; Tugboat contract loop | Suspension/traction, deterministic replay limits, controller hardware |
| Pocket Expedition | Seeded procedural dungeon with valid objectives | Dungeon Dash economy; Echo-Forge checkpoints | Reachability, seed reproducibility, recovery, no soft locks |
| Paper Council | Branching dialogue with consequential state | Story Studio quest cursor; ShammieQuest story choices | Branch persistence, localization, contradictory-state prevention |
| Tiny Duel | Small rollback-networked combat | CombatWindow; arena telegraphs | Resimulation, packet loss, prediction correction, reproducible mismatch logs |
| Garden Cards | Deck building and turn-state rules | Tower Assault turns; StockLedger-style transactions | Legal actions, draw/discard invariants, replay and AI fairness |

These are proposals, not existing games or implementation commitments. Before expanding, consider finishing production readiness in one current slice: authored visuals/audio, input rebinding, accessible cues, packaged build, real device tests and measured performance. Coverage quality matters as much as breadth.
