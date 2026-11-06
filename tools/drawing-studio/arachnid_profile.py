"""Plain-language grounding plus reusable, review-required arachnid geometry."""
import re
import numpy as np

BODY_PROMPT='The spider has a head, an abdomen, and legs.'
PALP_PROMPT='The spider has two short pedipalps beside its mouth and long walking legs.'


def eligible(profile_id,caption):
    # Do not silently apply spider pose assumptions to scorpions or ticks.
    return profile_id=='profile.arachnid' and bool(re.search(r'\bspider\b',caption,re.I))


def adapt(construction):
    """Preserve candidates without claiming that segments equal individual legs."""
    result=[]
    for part in construction['body_parts']+construction['appendage_candidates']:
        role=part['proposed_role']
        canonical={'head':'part.cephalothorax','abdomen':'part.abdomen','palp candidate':'part.pedipalp'}.get(role,'part.unknown')
        points=np.asarray(part['points']).copy();points[:,0]=points[:,0].clip(0,1279);points[:,1]=points[:,1].clip(0,697)
        result.append({'shape':{'primitive':'ellipse','points':points.tolist()+[points[0].tolist()],'metrics':part['measurements']},'role':role,'canonical':canonical,'box':[float(points[:,0].min()),float(points[:,1].min()),float(points[:,0].max()),float(points[:,1].max())],'raw_box':part.get('detected_box'),'evidence':part.get('role_evidence','model-grounded body region'),'walking_segment_candidate':part.get('eligible_for_walking_leg_grouping',False)})
    return result
