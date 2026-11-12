"""Author the detailed capability vocabulary and conservative source-backed mappings.

Broad legacy tags remain searchable domains, but do not satisfy detailed capabilities.
This edits seed data only; apply_catalog_update.py merges it into an existing library.
"""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def slug(s): return 'cap-' + re.sub('[^a-z0-9]+', '-', s.lower()).strip('-')

# family | group | legacy domain | independently assessable behavior
GROUPS = '''
Gameplay|Ground locomotion|traversal
Ground movement: Acceleration, braking and collision-aware walking or running.
Buffered jumping: Coyote time and input buffering at ledges and landings.
Variable jump height: Early release changes jump height without breaking collision.
Wall traversal: Wall jumps, slides or runs with attachment and exit rules.
Ledge climbing: Detect, hang from and mantle valid ledges.
Moving platform support: Preserve relative motion while standing on moving bases.
Grapple traversal: Validate anchors and control attachment, travel and release.
Stamina traversal: Resource costs gate movement and recovery.
Gameplay|Air and water movement|traversal
Controlled flight: Steering, ascent, descent and landing in a flight mode.
Gliding: Lift and descent constrain unpowered aerial travel.
Swimming: Water entry, surface motion and exit change locomotion.
Diving and oxygen: Underwater depth, breath and recovery rules.
Climbing surfaces: Valid surfaces constrain climbing and detachment.
Swinging ropes: Pendulum motion and release transfer momentum.
Zero gravity movement: Free orientation and inertia without a ground plane.
Traversal recovery: Recover from falls without corrupting objective state.
Gameplay|Combat resolution|combat
Melee hit resolution: Reach, target selection and damage resolve a melee strike.
Attack telegraphs: Wind-up cues precede a damaging attack.
Dodge invulnerability: A bounded dodge window rejects otherwise valid hits.
Timed parries: A timed defense interrupts or counters an attack.
Combo chains: Ordered attacks branch with cancel and timing rules.
Hit stop and hit stun: Impact pauses and recovery states change control.
Lock-on targeting: Acquire, maintain and switch a combat target.
Directional blocking: Facing and attack direction determine a block.
Gameplay|Weapons and damage|combat
Projectile ballistics: Gravity, drag and wind influence projectile flight.
Trajectory prediction: Predicted paths share the runtime flight model.
Guided interception: Pursuit or intercept guidance obeys fuel and turn limits.
Hitscan weapons: Instant traces resolve impacts and obstruction.
Area damage: Radius and exposure determine multi-target damage.
Status effect combos: Timed effects alter subsequent damage or interaction.
Armor penetration: Materials, angles or layers change damage penetration.
Weapon heat and reload: Resource and cooldown states constrain repeated fire.
Gameplay|Enemy and encounter AI|stealth-ai
Perception and occlusion: Range and sight obstruction gate detection.
Disguise detection: Disguises and temporary reveals alter detection.
Patrol and investigation: Agents patrol, investigate stimuli and resume duties.
Cover selection: Agents evaluate and occupy protective positions.
Group tactics: Agents coordinate flanks, focus fire or retreat.
Boss phase transitions: Health or objectives change boss rules and attacks.
Encounter wave progression: Clearing a wave grants rewards and advances difficulty.
Threat and aggro: Agents prioritize threats with explicit decay or transfer rules.
Gameplay|Squads and strategy|squads
Role-specific orders: Different unit roles accept independent assignments.
Cooperative hauling: Multiple nearby units jointly lift or carry an object.
Selection and control groups: Select, group and recall units consistently.
Formation movement: Units preserve or recover a formation while moving.
Unit counter roster: Unit matchups and unlocks produce distinct counters.
Fog of war: Visibility distinguishes unknown, remembered and currently seen space.
Merge split conservation: Unit merges and splits preserve health and population constraints.
Mobile bases: Packing and relocating a command structure preserves strategic state.
Gameplay|Pathfinding|navigation
Grid pathfinding: Search traversable cells with explicit cost and obstruction rules.
Route-safe construction: Placement preserves routes for entrances and active agents.
Dynamic path replanning: Changed obstacles invalidate and recompute routes.
Navigation mesh traversal: Agents traverse navmesh links and disconnected regions.
Crowd avoidance: Local steering prevents agent overlap and deadlock.
Flow field navigation: Shared directional fields guide many agents to destinations.
Flying navigation: Paths avoid obstacles through three-dimensional space.
Hierarchical navigation: Long routes combine coarse and fine searches.
Gameplay|Construction and assembly|construction
Connected grid assembly: Parts must remain face or edge connected to a valid base.
Motion-envelope placement: Placement accounts for the full swept obstacle volume.
Construction costs: Resources and inventory gate valid build operations.
Assembly save validation: Reject invalid saved assemblies before replacing live state.
Structural load solver: Loads and capacity determine stability and failure.
Snapping and sockets: Compatible connection points constrain part attachment.
Construction staging: Building progresses through timed or worker-driven stages.
Editable blueprints: Save, place and modify reusable construction plans.
Gameplay|Destruction|destruction
Support graph collapse: Loss of support detaches disconnected structural pieces.
Physics debris lifecycle: Bound debris and restore attachment, transforms and velocity on reset.
Damage-stage presentation: Cracks, fire and mesh changes communicate damage state.
Runtime mesh fracture: Generate new fragments and interior faces at impact time.
Voxel excavation: Remove terrain volume and update surfaces and collision.
Structural repair: Restore damaged connections and load-bearing capacity.
Material-specific failure: Material properties change fracture or deformation.
Persistent destruction: Save and restore destroyed world geometry consistently.
Gameplay|Rigid body simulation|physics
Rigid body collisions: Simulated bodies exchange collision impulses.
Joint constraints: Hinges, sliders or fixed joints bound relative motion.
Ragdoll blending: Switch between animation and physical bodies without discontinuity.
Rope simulation: Segmented or constraint-based ropes react to forces and contact.
Cloth simulation: Fabric deforms with attachments and collision.
Soft body deformation: Deformable volumes respond to contact and recover or fail.
Physics grabbing: Manipulate bodies through constrained forces or handles.
Fixed-step simulation: Advance bounded deterministic-sized steps under frame hitches.
Gameplay|Water and buoyancy|buoyancy
Sampled buoyant lift: Distributed lift samples produce heave, roll and pitch.
Cargo center of mass: Cargo mass and placement change stability.
Wave response: Surface changes disturb a floating body's motion.
Flooding and compartments: Water ingress changes displacement and stability.
Water current forces: Flow transfers force to bodies and swimmers.
Fluid displacement: Moving bodies change a simulated water surface or volume.
Capsize failure: Sustained tilt or low freeboard triggers damage or loss.
Speed-gated salvage: Range and vessel speed constrain winching and delivery.
Gameplay|Vehicles|vehicles
Arcade driving: Direct steering and speed rules control a vehicle.
Suspension solver: Wheel suspension reacts to terrain and load.
Tire friction: Slip, traction and braking determine contact forces.
Vehicle drivetrain: Gears, torque and engine response drive motion.
Vehicle part effects: Assembled parts change speed, damage or collision bounds.
Vehicle damage model: Component failures change control and performance.
Boat propulsion: Thrust and rudder or differential steering drive a vessel.
Aircraft aerodynamics: Lift, drag, stall and control surfaces govern flight.
Gameplay|Racing and competition|racing
Obstacle race phases: Draft, build, race and results use bounded phase rules.
Checkpoint validation: Valid ordered checkpoints gate race progress and recovery.
Race ranking: Arrival order or timing determines scores and standings.
Ghost time trials: Replay a previous run alongside the current attempt.
Lap and sector timing: Record lap validity, splits and personal bests.
Rubber-band competition: Adjust opposition within explicit fairness bounds.
Track generation: Generate traversable courses with difficulty constraints.
Stunt scoring: Recognize maneuvers and award chained scores.
Gameplay|Automation and production|automation
Creature job assignment: Befriended creatures accept and stop production jobs.
Fatigue rest hysteresis: Different stop and resume thresholds prevent work-state oscillation.
Input-gated production: Consume required stock before producing an output.
Production speed modifiers: Workers or upgrades alter throughput without creating free inputs.
Conveyor routing: Items travel through connected belts, splitters and junctions.
Factory scheduling: Dependencies and capacity coordinate multi-step production.
Automation logic circuits: Signals and conditions control machines.
Machine faults and maintenance: Wear or faults interrupt production until repaired.
Gameplay|Economy and logistics|economy
Cargo delivery accounting: Credit resources only after delivery while preserving carried stock.
Finite resource buffers: Extraction and pickup consume bounded stocks.
Customer patience queues: Stock and customer deadlines determine sales opportunities.
Mutation recipes: Consume ingredients to grant distinct persistent mutations.
Trading and price discovery: Supply, demand or offers determine exchange prices.
Inventory capacity: Weight, slots or stacking constrain carried items.
Crafting recipe graph: Multi-step ingredient dependencies constrain crafting.
Reward ledger: Record grants and claims without double-crediting balances.
Gameplay|Power and settlement|power-grid
Independent power networks: Connected components allocate independent supply budgets.
Power-priority allocation: Scarce power is allocated according to explicit priorities.
Power-gated queues: Production pauses and resumes with power availability.
Powered victory objectives: Continuous supply sustains objective progress with outage rules.
Utility distribution: Water, heat or sewage networks serve consumers with capacity limits.
Population needs: Residents react to shelter, food, jobs and services.
Traffic simulation: Road capacity and routes determine congestion and delivery.
Settlement growth: Land use, desirability and policy change development.
Gameplay|Puzzles|puzzle
Mirror beam reflection: Bounded reflected rays activate valid receivers.
Signal-driven geometry: Receiver or switch state immediately changes traversable geometry.
Typed resonance puzzles: Pulse type, spacing, proximity and visibility gate resonators.
Sequence memory: Reproduce a growing sequence with explicit error and completion rules.
Target tracking puzzle: Track an object through swaps or occlusion.
Sokoban pushing: Grid pushes respect occupancy and solvability constraints.
Portal puzzles: Linked portals transform position, orientation and momentum.
Time manipulation puzzles: Rewind, pause or clone temporal state under defined rules.
Gameplay|Quests and progression|quests
Ordered quest events: Only the current event kind and target advance a quest.
Idempotent objectives: Repeated events cannot duplicate objective progress.
Competing victory conditions: Multiple independent objectives can end a match.
Persistent upgrades: Purchased improvements survive between sessions.
Branching dialogue: Choices alter dialogue state and later consequences.
Faction reputation: Actions change faction standing and future responses.
Procedural quest composition: Valid objective graphs are assembled from reusable parts.
New game plus: Restart progression with specified retained systems and scaling.
Gameplay|Turns cards and rhythm|turn-based
Turn timer lifecycle: Start, stop and transition timers without stale callbacks.
Local alternating combat: Local players alternate actions through battle-state rules.
Deck construction: Card selection obeys deck constraints and persistent collection rules.
Card effect stack: Resolve ordered or interruptible effects consistently.
Tactical action points: Turns consume movement and action budgets.
Rhythm hit windows: Input timing maps to graded hits and misses.
Rhythm calibration: Store and apply input or audio timing offsets.
Fighting frame data: Startup, active, recovery and cancel frames define exchanges.
Gameplay|Education and adaptation|education
Deterministic problem grading: Canonical problem answers feed pure grading rules.
Mastery progression: Attempts update learning progress independently of rewards.
Interactive manipulatives: Directly manipulate visual quantities and representations.
Adaptive difficulty: Performance changes challenge under measurable rules.
Spaced repetition: Schedule reviews based on recall history.
Hint scaffolding: Incremental hints preserve learning and track assistance.
Answer equivalence: Accept multiple mathematically equivalent answer forms.
Authorable lessons: Validate editable lesson content before learner delivery.
Presentation|World generation|procedural
Habitat-masked scattering: Terrain and exclusion masks constrain procedural instances.
Terrain height sampling: Query terrain heights for placement or navigation.
Editable terrain states: Change terrain state, geometry and collision together.
Seeded encounter generation: A stored seed reproduces an encounter layout or sequence.
Procedural dungeon connectivity: Generated rooms retain a reachable entrance and goal.
Biome transitions: Blend terrain, vegetation and climate at biome boundaries.
World partition streaming: Stream world regions while preserving persistent references.
Runtime terrain generation: Generate terrain geometry and collision during play.
Presentation|Rendering and lighting|lighting
Dynamic shadow lighting: Moving lights and objects produce coherent shadows.
Global illumination: Indirect light responds to scene changes.
Day night cycle: Time changes lighting, sky and related scene state.
Weather rendering: Rain, snow or fog respond to weather state.
Water surface rendering: Surface shading conveys depth, waves and reflection.
Destruction visual effects: Bounded sparks, dust, smoke and fire communicate impacts.
Stylized outline rendering: Stable edge outlines support a deliberate visual style.
Material state transitions: Wetness, damage or heat changes materials continuously.
Presentation|Animation and cameras|animation
Component rig animation: Animate rigid limbs, wheels or turrets through component transforms.
Skeletal animation blending: Blend skeletal clips across locomotion and actions.
Inverse kinematics: Solve limbs or look targets against world constraints.
Procedural locomotion: Generate gait and foot placement from movement and terrain.
Facial performance: Drive coherent facial poses, blinking and expression transitions.
Cinematic sequencing: Coordinate camera, actors and events on a timeline.
Camera obstruction recovery: Prevent occlusion while preserving readable framing.
Camera feedback: Shakes, zoom and lag communicate motion and impact.
Presentation|Audio and music|audio
Adaptive music stems: Gameplay state selects and transitions music stems.
Spatial audio: Position and attenuation place sounds in the world.
Audio occlusion: Geometry changes filtering or audibility.
Surface footsteps: Contact material selects appropriately timed footstep cues.
Music beat synchronization: Game events align with a shared musical clock.
Dialogue voice playback: Voice, subtitles and interruption share playback state.
Audio mixing priorities: Limit competing cues and duck important channels.
Procedural audio synthesis: Generate audio from gameplay parameters at runtime.
Interaction|Controls and accessibility|accessibility
Icon-first commands: Shapes and symbols expose actions without mandatory reading.
Input rebinding: Remap inputs with conflict and device handling.
Touch gestures: Touch zones and gestures drive gameplay without mouse assumptions.
Gamepad focus navigation: Controller focus reaches and activates all essential UI.
Color-independent signals: Shape, pattern or text duplicates color-only information.
Screen reader semantics: Menus and gameplay state expose accessible announcements.
Reduced motion options: Limit camera motion, flashing and animation on request.
Subtitle customization: Size, speaker labels and contrast can be configured.
Interaction|XR and embodiment|vr
Observer station transitions: Fade and translate viewing stations without rotating tracked head.
Controller ray UI: Tracked controller rays interact with interface targets.
Journal control pause: Opening a journal prevents conflicting hero control.
Hand tracking interaction: Recognize and stabilize hand-driven selection and manipulation.
Room scale boundaries: Respect physical play-space limits and recentering.
XR comfort locomotion: Comfort options manage artificial motion and turns.
Haptic feedback: Events map to device-aware tactile feedback.
Mixed reality anchors: Persist content relative to tracked real-world surfaces.
Technology|Persistence and recovery|persistence
Atomic profile commits: Failed writes cannot grant purchases or rewards.
Versioned save recovery: Restore compatible state and fall back to a backup on failure.
Content-hash save isolation: Reject saves from incompatible content versions or event sequences.
Safe activity autosave: Restore timers and activities into safe playable states.
Checkpoint persistence: Falls preserve accepted progress while full restart clears it.
Cloud save conflict resolution: Detect and resolve divergent remote and local progress.
Save schema migration: Upgrade older saves with explicit compatibility tests.
Crash-safe world snapshots: Recover large world state without partial entity graphs.
Technology|Multiplayer|networking
Host-authoritative combat: Host decides damage, purchases and turn outcomes.
Authoritative object interaction: Server validates pickup, disguise and capture decisions.
Replicated race state: Server owns phase clocks, inventory and race scores.
Shared cooperative objectives: Separate players contribute to one authoritative objective.
Late join admission: Joining during a round uses an explicit safe admission phase.
Client prediction reconciliation: Predict input locally and reconcile server corrections.
Rollback simulation: Restore and resimulate historical state for late inputs.
Lag-compensated hits: Validate hits against a bounded historical world state.
Technology|Online services|matchmaking
Lobby matchmaking: Form suitable sessions and handle failed joins.
Dedicated server lifecycle: Allocate, monitor and retire match servers.
Reconnect recovery: Restore a disconnected player without duplicated state.
Cross-platform identity: Map platform identities and permissions to one player.
Anti-cheat validation: Reject impossible or unauthorized gameplay requests.
Session reward API: Start and finish sessions with validated reward grants.
Leaderboards: Submit and rank validated scores with season boundaries.
Live events: Activate versioned time-bounded content consistently.
Technology|Tooling and reuse|authoring
Asset version comparison: Compare pinned asset versions with review context.
Terrain-aware review camera: Navigate to sampled terrain heights and retain review settings.
Runtime content validation: Reject invalid authored content before gameplay consumption.
Replay recording: Record sufficient state or input for repeatable playback.
Mod sandboxing: Load extensions under bounded compatibility and permission rules.
Localization pipeline: Extract, translate and validate text, layouts and locale formats.
Performance budgets: Measure CPU, GPU and memory against per-platform budgets.
Deterministic replay verification: Compare replay state hashes across runs and builds.
'''

# Each mapping names an already documented mechanic; no inheritance from broad tags.
MAPPINGS = {
'beast-bistro-express-1':['Mutation recipes'],
'beast-bistro-express-2':['Attack telegraphs'],
'box-fort-brigade-core':['Support graph collapse'],
'box-fort-brigade-1':['Physics debris lifecycle'],
'chroma-turf-core':['Editable terrain states'],
'critter-contraptions-core':['Creature job assignment','Fixed-step simulation'],
'critter-contraptions-1':['Fatigue rest hysteresis'],
'critter-contraptions-2':['Input-gated production','Production speed modifiers'],
'dungeon-dash-market-core':['Melee hit resolution','Persistent upgrades'],
'dungeon-dash-market-1':['Customer patience queues'],
'dungeon-dash-market-2':['Atomic profile commits'],
'echo-forge-core':['Typed resonance puzzles'],
'echo-forge-1':['Checkpoint persistence'],
'flotsam-citadel-core':['Sampled buoyant lift','Cargo center of mass','Capsize failure','Fixed-step simulation'],
'flotsam-citadel-1':['Connected grid assembly','Construction costs'],
'gully-giants-core':['Traversal recovery'],
'gully-giants-1':['Grapple traversal','Moving platform support'],
'gully-giants-2':['Idempotent objectives'],
'haunt-and-haul-1':['Disguise detection','Perception and occlusion'],
'haunt-and-haul-2':['Authoritative object interaction'],
'lumen-weaver-core':['Mirror beam reflection'],
'lumen-weaver-1':['Signal-driven geometry'],
'pebblekin-command-1':['Cooperative hauling'],
'pebblekin-command-2':['Role-specific orders'],
'pocket-fort-patrol-1':['Route-safe construction'],
'pocket-fort-patrol-2':['Status effect combos'],
'scrapshift-arena-core':['Attack telegraphs','Dodge invulnerability','Timed parries','Encounter wave progression','Seeded encounter generation'],
'scrapshift-arena-1':['Vehicle part effects'],
'skybound-sabotage-core':['Obstacle race phases','Race ranking','Late join admission'],
'skybound-sabotage-1':['Motion-envelope placement'],
'skybound-sabotage-2':['Replicated race state'],
'snap-rally-core':['Connected grid assembly','Vehicle part effects'],
'snap-rally-1':['Assembly save validation'],
'snap-rally-2':['Arcade driving','Rigid body collisions'],
'tugboat-tumble-core':['Cargo center of mass','Wave response','Capsize failure'],
'tugboat-tumble-1':['Speed-gated salvage'],
'3d-tower-assault-core':['Projectile ballistics','Trajectory prediction'],
'3d-tower-assault-1':['Guided interception'],
'3d-tower-assault-2':['Damage-stage presentation','Destruction visual effects'],
'3d-tower-assault-3':['Host-authoritative combat'],
'acorn-anvil-core':['Grid pathfinding','Fixed-step simulation','Construction staging'],
'acorn-anvil-1':['Cargo delivery accounting'],
'acorn-anvil-2':['Unit counter roster','Competing victory conditions'],
'acorn-anvil-3':['Versioned save recovery'],
'arcore-openworld-core':['World partition streaming'],
'arcore-openworld-1':['Habitat-masked scattering','Terrain height sampling'],
'arcore-openworld-2':['Terrain-aware review camera'],
'salvage-circuit-core':['Finite resource buffers'],
'salvage-circuit-1':['Independent power networks','Power-priority allocation','Power-gated queues'],
'salvage-circuit-2':['Merge split conservation'],
'salvage-circuit-3':['Mobile bases'],
'sandbox-kingdoms-1':['Icon-first commands'],
'sandbox-kingdoms-2':['Shared cooperative objectives'],
'scorched-frontier-1':['Finite resource buffers','Cargo delivery accounting'],
'scorched-frontier-2':['Powered victory objectives'],
'scorched-frontier-3':['Component rig animation','Adaptive music stems'],
'shammyverse-1':['Buffered jumping','Controlled flight','Swimming','Ground movement'],
'shammyverse-3':['Safe activity autosave'],
'bubble-wishes-poofy-s-story-studio-1':['Ordered quest events','Idempotent objectives'],
'bubble-wishes-poofy-s-story-studio-2':['Content-hash save isolation'],
'colobrary-battle-modes-1':['Local alternating combat'],
'tower-assault-web-1':['Turn timer lifecycle'],
'shammiequest-1':['Rhythm hit windows','Rhythm calibration'],
'shammiequest-2':['Sequence memory','Target tracking puzzle'],
'shammiequest-3':['Session reward API'],
'shammiemath-1':['Deterministic problem grading','Mastery progression'],
'shammiemath-2':['Reward ledger'],
'shammyverse-vr-beach-1':['Observer station transitions'],
'shammyverse-vr-beach-2':['Controller ray UI','Journal control pause'],
'engage-math-activity-collection-1':['Interactive manipulatives'],
}

def main():
    tags=json.loads((ROOT/'data/taxonomy.json').read_text(encoding='utf-8'))
    tags=[dict(t,level='domain') for t in tags if not t['id'].startswith('cap-')]
    known={t['id'] for t in tags}
    for line in GROUPS.strip().splitlines():
        if '|' in line:
            family,group,parent=line.split('|'); assert parent in known; continue
        label,desc=line.split(': ',1)
        tags.append(dict(id=slug(label),label=label,family=family,group=group,parent_id=parent,level='capability',description=desc,
            acceptance='Demonstrate this behavior and its failure/recovery cases in a runnable build; record revision, platform, dependencies, source boundary and test evidence. A second consumer is required for reused status.'))
    assert len({t['id'] for t in tags})==len(tags)
    games=json.loads((ROOT/'data/catalog.json').read_text(encoding='utf-8'))
    mechanics={m['id']:(g,m) for g in games for m in g['mechanics']}
    ids={t['id'] for t in tags}
    for mid,labels in MAPPINGS.items():
        g,m=mechanics[mid]
        for label in labels:
            cid=slug(label); assert cid in ids
            if any(c['id']==cid for c in g['capabilities']): continue
            g['capabilities'].append(dict(id=cid,state='prototype' if m['state']=='prototype' else 'implemented',
                evidence=f"Catalog source audit: {m['name']}. {m['sources']} | Scope: {m['rules']} | Fresh runtime verification: not_run.",
                mechanic_id=mid,assessment='source-candidate',taxonomy_version=2))
    (ROOT/'data/taxonomy.json').write_text(json.dumps(tags,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (ROOT/'data/catalog.json').write_text(json.dumps(games,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    leaves=[t for t in tags if t['level']=='capability']
    covered={c['id'] for g in games for c in g['capabilities'] if c['state']!='planned'}
    print(json.dumps(dict(domains=len(tags)-len(leaves),capabilities=len(leaves),groups=len({t['group'] for t in leaves}),source_candidates=sum(t['id'] in covered for t in leaves),not_yet_evidenced=sum(t['id'] not in covered for t in leaves))))
if __name__=='__main__': main()
