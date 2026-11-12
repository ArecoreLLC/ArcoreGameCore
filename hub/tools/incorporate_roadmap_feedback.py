"""Reproducible editorial update from the preserved review baseline (no live DB writes)."""
import collections
import copy
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/roadmap-feedback-2026-11-11'
REVISION = 'review-2026-11-11-v1'


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    for name in ['capability-roadmap.json', 'taxonomy.json']:
        baseline = EVIDENCE / ('before-' + name)
        if not baseline.exists():
            baseline.write_bytes((ROOT / 'data' / name).read_bytes())
    review = EVIDENCE / 'review-source.txt'
    if not review.exists():
        raise SystemExit('Place the supplied review in evidence/roadmap-feedback-2026-11-11/review-source.txt first.')
    source = review.read_text(encoding='utf-8-sig')
    plan = json.loads((EVIDENCE / 'before-capability-roadmap.json').read_text(encoding='utf-8'))
    taxonomy = json.loads((EVIDENCE / 'before-taxonomy.json').read_text(encoding='utf-8'))
    catalog = {g['id']: g for g in json.loads((ROOT / 'data/catalog.json').read_text(encoding='utf-8'))}
    games = {g['id']: g for g in plan['projects']}
    cap = lambda name: 'cap-' + name

    additions = [
        ('save-corruption-recovery', 'Save corruption recovery', 'Technology', 'Persistence and recovery', 'persistence',
         'Inject malformed/truncated saves and disk-full, quota or write-denied failures. Recover the last known-good state without duplicated rewards; keep the failed original for diagnosis.'),
        ('audio-device-recovery', 'Audio device recovery', 'Presentation', 'Audio and music', 'audio',
         'Disconnect/reconnect the audio device and change its buffer/sample rate. Rebase the musical clock without lost game progress or duplicate beat events; record latency and recovery time.'),
        ('frame-rate-resilience', 'Frame-rate resilience', 'Gameplay', 'Rigid body simulation', 'physics',
         'Compare a 60 Hz baseline with injected 20 FPS hitches using bounded substeps and a catch-up limit. Declare numeric position/contact tolerances and hardware before testing; report drift and overload behavior.')]
    for name, label, family, group, parent, description in additions:
        taxonomy.append(dict(id=cap(name), label=label, family=family, group=group, parent_id=parent,
                             level='capability', description=description, acceptance=description + ' Record exact build, platform, commands and evidence in two independent consumers.'))
    definitions = {t['id']: t for t in taxonomy}

    def add(game, names):
        g = games[game]
        for name in names.split(','):
            target = cap(name)
            assert target in definitions, target
            if target not in g['capability_ids']:
                g['capability_ids'].append(target)
                g['later_capabilities'].append(target)

    # Preserve all fifty stable IDs; retire overlapping pitches into existing chapters.
    for gid, title, first, later, pitch, donors in [
        ('gravity-parcel', 'Relic Rematch', 'boss-phase-transitions,new-game-plus', 'threat-and-aggro,lock-on-targeting,directional-blocking,hit-stop-and-hit-stun',
         'Rematch a two-phase relic guardian with carried-over unlocks. Validate boss reset, reward conservation and readable combat escalation in a bounded arena.', ['duelists-circuit', 'pocket-expedition']),
        ('salvage-submersible', 'Relic Gallery', 'global-illumination,asset-version-comparison,localization-pipeline', 'stylized-outline-rendering',
         'Curate a small relic exhibition: compare admitted model versions under controlled lighting and switch localized labels without losing layout or selection.', ['living-wilds', 'foundry-friends'])]:
        g = games[gid]
        g['previous_title'] = g['title']
        g['title'], g['pitch'] = title, pitch
        g['first_slice_capabilities'] = list(map(cap, first.split(',')))
        g['later_capabilities'] = list(map(cap, later.split(',')))
        g['capability_ids'] = g['first_slice_capabilities'] + g['later_capabilities']
        g['donors'] = list({d['project_id']: copy.deepcopy(d) for owner in donors for d in games[owner]['donors']}.values())
        g['priority_reason'] = 'Repurposed duplicate track to validate previously single-consumer portfolio capabilities; stable ID retained.'
        g['implementation_approach']['starting_project_id'] = g['donors'][0]['project_id']
        g['acceptance'] = ('Reset both boss phases, restart a new-game-plus cycle, reject duplicate rewards, and test blocking/lock-on with readable telegraphs.' if gid == 'gravity-parcel' else
                           'Compare two pinned asset versions with identical camera/exposure; measure lighting cost and outline readability; test long strings, missing translations and locale switching.')
        g['reusable_outputs'] = (['Boss phase/reset contract', 'Progression carry-over rules', 'Combat readability fixtures'] if gid == 'gravity-parcel' else
                                 ['Asset comparison scene', 'Lighting benchmark fixtures', 'Localized exhibit-label contract'])
    add('moonbase-freight', 'portal-puzzles,replay-recording')
    add('reef-keeper', 'boat-propulsion,vehicle-damage-model,flooding-and-compartments')
    assignments = {
        'pocket-expedition': 'save-corruption-recovery', 'learning-garden': 'save-corruption-recovery', 'paper-council': 'save-corruption-recovery',
        'echo-stage': 'audio-device-recovery', 'beatwing-rally': 'audio-device-recovery',
        'clockwork-courier': 'frame-rate-resilience', 'orbital-salvage': 'frame-rate-resilience',
        'patchwork-parade': 'frame-rate-resilience,swinging-ropes,inverse-kinematics',
        'marshlight-rescue': 'surface-footsteps', 'tracksmith-trials': 'lap-and-sector-timing,anti-cheat-validation,live-events',
        'quiet-library': 'touch-gestures', 'siege-workshop': 'snapping-and-sockets',
        'clockwork-cartographer': 'variable-jump-height,wall-traversal,climbing-surfaces,stamina-traversal',
        'wisp-shepherd': 'gliding', 'puppet-theater': 'skeletal-animation-blending,camera-feedback',
        'living-fortress': 'cover-selection,selection-and-control-groups,area-damage',
        'chrono-arena': 'ragdoll-blending', 'windmill-village': 'settlement-growth',
        'memory-orchard': 'faction-reputation,procedural-quest-composition,cloud-save-conflict-resolution',
        'starboard-signals': 'procedural-audio-synthesis', 'sandcastle-stories': 'voxel-excavation,xr-comfort-locomotion',
        'frontier-assembly': 'hitscan-weapons,weapon-heat-and-reload,armor-penetration',
        'shadow-couriers': 'lag-compensated-hits,dedicated-server-lifecycle', 'tether-team': 'cross-platform-identity',
        'duelists-circuit': 'deterministic-replay-verification'}
    for gid, names in assignments.items():
        add(gid, names)
    for key in ['capability_ids', 'later_capabilities']:
        games['clockwork-courier'][key].remove(cap('deterministic-replay-verification'))
    for gid, later in [('clockwork-rooms', ['portal-puzzles']), ('patchwork-parade', ['cloth-simulation', 'soft-body-deformation'])]:
        for name in later:
            games[gid]['first_slice_capabilities'].remove(cap(name))
            if cap(name) not in games[gid]['later_capabilities']:
                games[gid]['later_capabilities'].insert(0, cap(name))
    donor_templates = {d['project_id']: d for g in games.values() for d in g['donors']}
    games['canopy-courier']['donors'] = [copy.deepcopy(donor_templates[x]) for x in ['shammyverse', 'bubble-wishes-poofy-s-story-studio']]
    games['canopy-courier']['implementation_approach']['starting_project_id'] = 'shammyverse'

    # Creative text is inspiration, never an implicit acceptance/scope expansion.
    creative = source.split('2. Expanded Gameplay', 1)[1].split('Flagship Larger-Game Combinations', 1)[0]
    matches = list(re.finditer(r'(?<!\d)(\d{1,2})\.\s+([a-z][a-z0-9-]*)', creative))
    assert len(matches) == 50
    for i, match in enumerate(matches):
        g = games[match.group(2)]
        excerpt = creative[match.end():matches[i+1].start() if i+1 < len(matches) else len(creative)].strip()
        excerpt = re.split(r'Wave \d:', excerpt)[0].strip().replace('\ufffd', ' — ')
        if 'Expanded Gameplay Loop:' in excerpt:
            text = excerpt.split('Expanded Gameplay Loop:', 1)[1]
        else:
            text = re.sub(r'^.*?\):', '', excerpt) if '):' in excerpt else re.sub(r'^(Godot XR|Godot|Web / TS|Unreal)', '', excerpt)
        parts = re.split(r'Graphics & Visual Identity:|Visuals:', text, maxsplit=1)
        g['creative_direction'] = parts[0].strip()
        g['visual_direction'] = parts[1].strip() if len(parts) > 1 else 'Use the scenario brief as visual inspiration; establish readability, accessibility and a distinct palette in the first art review.'
        g['creative_scope'] = 'Proposed creative direction. Only named first-slice targets gate the initial playable; additional interactions and polish need later scope approval.'
    for gid in ['gravity-parcel', 'salvage-submersible']:
        games[gid]['creative_direction'] = games[gid]['pitch']
    games['gravity-parcel']['visual_direction'] = 'A moss-and-brass circular shrine; guardian silhouettes and animation telegraphs change clearly between phases, with high-contrast impact and block signals.'
    games['salvage-submersible']['visual_direction'] = 'A quiet miniature museum with neutral comparison bays, warm exhibit lighting, adjustable outline views and typography that accommodates multiple locales.'

    amendments = {
        'pocket-expedition': 'First playable has no stealth-AI gate. Test 1,000 seeded five-room graphs with zero unreachable exits, recipe conservation and v1-to-v2 save fixtures. Perception is optional later support.',
        'clockwork-courier': 'Snap-Rally is an arcade reference, not a suspension implementation. Record transform/input ghosts; measure drift over 100 rough-terrain playbacks against declared tolerances. Deterministic combat hashes belong to Duelist’s Circuit and Chrono Arena.',
        'clockwork-rooms': 'First playable: discrete Sokoban plus bounded rewind. Continuous portal transforms/momentum are a separate later test room.',
        'patchwork-parade': 'First playable: procedural gait only. Validate cloth and soft-body attachment in separate later fixtures before combining them. Later rope/IK tests use one tethered puppet.',
        'arena-relay': 'Keep predicted hitscan and rollback melee in separate test modes with independent authority/state contracts and latency tests.',
        'moonbase-freight': 'Absorbs Gravity Parcel as a later portal/loading-bay chapter with recorded replay; initial zero-gravity cargo slice stays bounded.',
        'reef-keeper': 'Free-swimming nursery maintenance first. Absorbs Salvage Submersible as a later repairable ROV chapter with compartment damage, propulsion and flooding; distinct from Storm Harbor route navigation.',
        'shadow-couriers': 'Reconnect tests focus on stealth treasure authority, duplicate pickup prevention and bounded guard-hit reconciliation.',
        'tether-team': 'Reconnect tests focus on cable ownership, joint restoration and identity continuity under physics load.',
        'starboard-signals': 'Reconnect tests focus on asymmetric lighthouse/boat roles and beat-clock continuity; later procedural foghorn synthesis.',
        'chrono-arena': 'Use fixed-step bounded combat state hashes. Cosmetic ragdolls are outside rewind state; verify their blend/reset separately.',
        'frontier-assembly': 'Later defensive turret slice validates hitscan, reload/heat and armor with a fixed budget; do not add these to the initial outpost slice.',
        'tracksmith-trials': 'Later seasonal event fixture tests server-side score rejection, lap sectors and event expiration without requiring a live public service.',
        'memory-orchard': 'Later branches test faction-driven quest composition and conflicting offline saves without discarding learning progress.',
        'wisp-shepherd': 'Later wind/glide route tests flying navigation and procedural gait transitions; keep the initial flock small.',
        'sandcastle-stories': 'Later fixtures separate voxel carving, soft sand deformation and comfort locomotion on named XR hardware.',
    }
    for gid, note in amendments.items():
        games[gid]['review_changes'] = [note]
        games[gid]['acceptance'] += ' ' + note

    def engine(text):
        return 'unreal' if 'unreal' in text.lower() else 'godot' if 'godot' in text.lower() else 'web'

    owners = {}
    for g in sorted(games.values(), key=lambda x: x['priority']):
        for target in g['capability_ids']:
            owners.setdefault(target, g['id'])
    # Dependencies name actual producer milestones and are scoped to first/later work.
    # For foundation games, retain only useful shared subsystem dependencies.
    for g in games.values():
        requirements, stages = {}, {}
        for target in g['capability_ids']:
            owner = owners[target]
            if owner != g['id']:
                requirements.setdefault(owner, []).append(target)
                stages.setdefault(owner, {})[target] = 'first_slice' if target in g['first_slice_capabilities'] else 'later'
        g['dependency_requirements'] = requirements
        g['dependency_stages'] = stages
        g['depends_on'] = list(requirements)
        g['dependency_contracts'] = {dep: {
            'mode': 'behavior_contract_only' if engine(g['preferred_runtime']) != engine(games[dep]['preferred_runtime']) else 'same_engine_candidate',
            'contract': 'Versioned state/input/output schema, units and coordinate conventions, failure fixtures and expected results for the named targets.',
            'adapter': 'Consumer-owned runtime adapter; validate equivalent fixtures in both engines. No runtime-source compatibility implied.' if engine(g['preferred_runtime']) != engine(games[dep]['preferred_runtime']) else 'Pin subsystem boundary and engine/plugin versions; run consumer integration fixtures.'
        } for dep in requirements}
        g['feedback_revision'] = REVISION
        g['capability_labels'] = [definitions[x]['label'] for x in g['capability_ids']]
        g.setdefault('review_changes', ['Added explicit producer milestones, stage-scoped prerequisites and donor admission requirements.'])
        for d in g['donors']:
            d['reuse_mode'] = 'same_engine_candidate' if engine(g['preferred_runtime']) == engine(catalog[d['project_id']]['engine']) else 'behavior_contract_only'
            d['admission'] = 'Pin a commit plus dirty/untracked changes, or a complete source/dependency/binary-asset hash manifest. Inspect external plugins/headers and asset rights; record actual engine/platform and build evidence. Provider IDs remain unpinned until resolved.'
            if d['reuse_mode'] == 'behavior_contract_only':
                d['admission'] += ' Port behavior/data through a consumer-owned adapter and run parity fixtures; these source links are not directly executable in this runtime.'
            if d['project_id'] == 'colobrary-battle-modes':
                d['admission'] += ' Battle-state/data-structure reference only. Use original characters; do not import franchise names, media or cries without admitted rights.'
        for target in g['capability_ids']:
            if target in [cap(x[0]) for x in additions]:
                g['acceptance'] += ' ' + definitions[target]['description']

    # Supporting systems need not be targets of the consumer itself.
    for gid, dep, names, stage, contract in [
        ('bastion-tactics', 'lantern-heist', 'navigation-mesh-traversal,dynamic-path-replanning', 'first_slice', 'Squad movement consumes navigation and replanning interfaces.'),
        ('pocket-workshop-xr', 'orbital-salvage', 'physics-grabbing,joint-constraints', 'later', 'Portable grab/constraint behavior fixtures; implement Godot adapters, without gating on zero gravity.'),
        ('pocket-workshop-xr', 'echo-stage', 'haptic-feedback', 'later', 'Device-specific haptic event contract and calibration fixtures.')]:
        g = games[gid]
        g['dependency_requirements'][dep] = list(map(cap, names.split(',')))
        g['dependency_stages'][dep] = {cap(name): stage for name in names.split(',')}
        g['depends_on'] = list(g['dependency_requirements'])
        g['dependency_contracts'][dep] = dict(mode='behavior_contract_only' if engine(g['preferred_runtime']) != engine(games[dep]['preferred_runtime']) else 'same_engine_candidate', contract=contract, adapter='Consumer-owned adapter and independent parity tests; pin runtime and hardware versions.')
    flagship = source.split('Flagship Larger-Game Combinations', 1)[1]
    for i, g in enumerate(plan['larger_game_combinations']):
        start = flagship.index(g['id'])
        end = flagship.index(plan['larger_game_combinations'][i+1]['id']) if i+1 < len(plan['larger_game_combinations']) else len(flagship)
        text = flagship[start:end].replace('\ufffd', ' — ')
        g['creative_direction'], g['visual_direction'] = [x.strip() for x in text.split('Vision:', 1)[1].split('Visual Signature:', 1)]
    counts = collections.Counter(c for g in games.values() for c in g['capability_ids'])
    assert len(games) == 50 and len(counts) == 146 and min(counts.values()) >= 2
    assert all(games[d]['priority'] < g['priority'] for g in games.values() for d in g['depends_on'])
    plan['feedback_revision'] = REVISION
    plan['added_taxonomy'] = taxonomy[-3:]
    plan['feedback_review'] = {
        'source': 'User-supplied external LLM review', 'source_sha256': hashlib.sha256(review.read_bytes()).hexdigest(),
        'accepted': ['Remove unrelated prerequisite gates; require exact producer milestones by stage.', 'Narrow first slices; distinguish three co-op recovery scenarios.', 'Repurpose two redundant tracks while retaining fifty stable IDs.', 'Add three failure-case capabilities and second consumers for every target.', 'Retain all fifty creative briefs and four flagship visions as proposed direction.', 'Record engine boundaries, reproducible donor baselines and asset admission.'],
        'corrected': ['Baseline contains 50 games, 143 definitions and 285 assignments, not 28/89/168. No evidence supports 54 missing export definitions.', 'Baseline has 42 single-consumer capabilities, not ten.', 'A complete immutable manifest is a valid baseline alternative to Git commits. No donor repositories were committed.', 'Reviewer claims about specific engine solver bugs are unverified risks, not catalog facts.'],
        'scope': 'Catalog/roadmap planning update only. No game implementation or capability acceptance claimed.'}
    plan['validation'].update(unique_target_capabilities=len(counts), target_assignments=sum(counts.values()), added_failure_case_capabilities=3,
                              single_consumer_capabilities=[], minimum_planned_consumers=min(counts.values()))
    plan['portfolio_gates']['before_build'] += ' A complete source/dependency/binary-asset manifest may substitute for a commit. A single inspected-file hash is insufficient.'
    write(ROOT / 'data/capability-roadmap.json', plan)
    write(ROOT / 'data/taxonomy.json', taxonomy)
    write(EVIDENCE / 'decisions.json', {'review': plan['feedback_review'], 'validation': plan['validation'], 'consumers': {c: [g['id'] for g in games.values() if c in g['capability_ids']] for c in sorted(counts)}})
    print(json.dumps(plan['validation'], indent=2))


if __name__ == '__main__':
    main()
