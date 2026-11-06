"""Load and resolve engine-neutral subject taxonomy labels."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CATALOG=ROOT/'shared'/'subject-taxonomy'/'catalog.v1.json'


def normalize_label(value):
    value=re.sub(r'[_-]+',' ',str(value).casefold())
    value=re.sub(r'[^a-z0-9 ]+',' ',value)
    value=re.sub(r'\s+',' ',value).strip()
    return re.sub(r'^(the|an|a)\s+','',value)


def load_catalog(path=DEFAULT_CATALOG):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def candidate_profiles(raw_label,catalog):
    label=normalize_label(raw_label);matches=[]
    for profile_id,profile in catalog['profiles'].items():
        aliases=[profile['label'],*profile.get('aliases',[])]
        scored=[]
        for alias in aliases:
            alias=normalize_label(alias)
            if label==alias:scored.append(1.0)
            elif re.search(rf'\b{re.escape(alias)}\b',label):scored.append(.8)
        if scored:matches.append({'profile':profile_id,'alias_score':max(scored),'raw_label':raw_label})
    return sorted(matches,key=lambda item:(-item['alias_score'],item['profile']))


def resolve_part(raw_label,catalog,profile_id=None):
    label=normalize_label(raw_label)
    if profile_id:
        profile=catalog['profiles'].get(profile_id)
        if profile is None:raise KeyError(f'Unknown profile: {profile_id}')
        override={normalize_label(k):v for k,v in profile.get('part_aliases',{}).items()}
        if label in override:return {'status':'resolved' if override[label]!='part.ambiguous' else 'ambiguous','part':override[label],'candidates':[override[label]],'source':'profile_alias'}
        allowed={entry['part'] for entry in profile['parts']}|{'part.unknown','part.ambiguous'}
    else:allowed=set(catalog['parts'])
    candidates=[]
    for part_id,part in catalog['parts'].items():
        if part_id not in allowed:continue
        aliases=[part['label'],*part.get('aliases',[])]
        if label in {normalize_label(alias) for alias in aliases}:candidates.append(part_id)
    candidates=sorted(set(candidates))
    if len(candidates)==1:return {'status':'resolved','part':candidates[0],'candidates':candidates,'source':'canonical_alias'}
    if candidates:return {'status':'ambiguous','part':'part.ambiguous','candidates':candidates,'source':'canonical_alias'}
    return {'status':'unknown','part':'part.unknown','candidates':[],'source':'no_match'}


def compose_parts(catalog,profile_id,trait_ids=()):
    """Return a profile's parts plus optional trait-provided parts."""
    profile=catalog['profiles'].get(profile_id)
    if profile is None:raise KeyError(f'Unknown profile: {profile_id}')
    selected=list(dict.fromkeys([*profile.get('traits',[]),*trait_ids]))
    counts={entry['part']:list(entry['count']) for entry in profile['parts']}
    for trait_id in selected:
        trait=catalog.get('traits',{}).get(trait_id)
        if trait is None:raise KeyError(f'Unknown trait: {trait_id}')
        for part_id in trait.get('adds_parts',[]):
            counts.setdefault(part_id,[0,1])
    return {'profile':profile_id,'traits':selected,'parts':counts}


def validate_catalog(catalog):
    errors=[]
    if catalog.get('schema_version')!=1:errors.append('schema_version must be 1')
    if not re.fullmatch(r'\d+\.\d+\.\d+',catalog.get('taxonomy_version','')):errors.append('taxonomy_version must use semantic version form')
    primitives=set(catalog.get('primitive_vocabulary',[]));applications=set(catalog.get('applications',[]))
    parts=catalog.get('parts',{});profiles=catalog.get('profiles',{});traits=catalog.get('traits',{})
    if len(parts)<2:errors.append('parts must contain canonical fallback entries')
    for fallback in ('part.unknown','part.ambiguous'):
        if fallback not in parts:errors.append(f'missing {fallback}')
    for part_id,part in parts.items():
        if not part_id.startswith('part.'):errors.append(f'{part_id}: invalid part ID')
        if not part.get('label'):errors.append(f'{part_id}: missing label')
        unknown=set(part.get('geometry',[]))-primitives
        if unknown:errors.append(f'{part_id}: unknown primitives {sorted(unknown)}')
        unknown=set(part.get('capabilities',[]))-applications
        if unknown:errors.append(f'{part_id}: unknown applications {sorted(unknown)}')
    for trait_id,trait in traits.items():
        if not trait_id.startswith('trait.'):errors.append(f'{trait_id}: invalid trait ID')
        if not trait.get('label'):errors.append(f'{trait_id}: missing label')
        for part_id in trait.get('adds_parts',[]):
            if part_id not in parts:errors.append(f'{trait_id}: unknown added part {part_id}')
    for profile_id,profile in profiles.items():
        if not profile_id.startswith('profile.'):errors.append(f'{profile_id}: invalid profile ID')
        if not profile.get('parts'):errors.append(f'{profile_id}: missing parts')
        for trait_id in profile.get('traits',[]):
            if trait_id not in traits:errors.append(f'{profile_id}: unknown trait {trait_id}')
        referenced=set()
        for entry in profile.get('parts',[]):
            part_id=entry.get('part');referenced.add(part_id)
            if part_id not in parts:errors.append(f'{profile_id}: unknown part {part_id}')
            count=entry.get('count')
            if not isinstance(count,list) or len(count)!=2 or not all(isinstance(x,int) and x>=0 for x in count) or count[0]>count[1]:errors.append(f'{profile_id}/{part_id}: invalid count')
            if entry.get('required') and isinstance(count,list) and count[0]<1:errors.append(f'{profile_id}/{part_id}: required count minimum must be positive')
        for alias,target in profile.get('part_aliases',{}).items():
            if not normalize_label(alias):errors.append(f'{profile_id}: empty part alias')
            if target not in parts:errors.append(f'{profile_id}: alias targets unknown part {target}')
            if target not in referenced and target not in ('part.unknown','part.ambiguous'):errors.append(f'{profile_id}: alias target {target} is outside profile')
    for topology_id,topology in catalog.get('topology_templates',{}).items():
        if not topology_id.startswith('topology.'):errors.append(f'{topology_id}: invalid topology ID')
        applied=topology.get('applies_to',[])
        if not applied:errors.append(f'{topology_id}: missing applicable profiles')
        for profile_id in applied:
            if profile_id not in profiles:errors.append(f'{topology_id}: unknown profile {profile_id}')
        edges=topology.get('edges',[])
        if not edges:errors.append(f'{topology_id}: missing edges')
        for edge in edges:
            if not isinstance(edge,list) or len(edge)!=3:
                errors.append(f'{topology_id}: invalid edge {edge!r}')
                continue
            source,target,relation=edge
            if source not in parts:errors.append(f'{topology_id}: unknown edge part {source}')
            if target not in parts:errors.append(f'{topology_id}: unknown edge part {target}')
            if not isinstance(relation,str) or not relation:errors.append(f'{topology_id}: invalid edge relation')
    return errors
