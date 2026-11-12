"""Record editorial selections from visually reviewed contact sheets and filmstrips."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'evidence/marketing-2026-11-11'
# index: title, visual description, selection rationale
SHOTS={
8:('Blue battery ready','Three blue-bannered artillery towers stand in a grassy arena with aiming controls.','Clear overview of playable artillery and its HUD.'),
10:('Impact at the red battery','An explosion lights the base of a red-bannered tower amid a three-tower formation.','Communicates impact effects in gameplay context.'),
4:('Strike aftermath','A stylized mushroom cloud rises over the tower battlefield.','Clean wide effects view; feature illustration, not ordinary gameplay.'),
19:('Village command','A pastel village with workers, buildings, resource counters and construction controls.','Readable current skirmish interface and settlement layout.'),
16:('Village buildings','A teal-roofed pavilion and wooden buildings sit beside a village path.','Uncluttered architecture detail complements the gameplay view.'),
17:('Units on the path','Small stylized units face one another along a sandy path.','Shows character scale and roster apart from the HUD.'),
37:('Nature Walk forest','A path runs through a dense stylized green forest with review information above.','Strong scene composition; this is an observation environment.'),
38:('World review map','An island elevation map fills a world-review interface with configuration panels.','Demonstrates terrain review tooling, not character gameplay.'),
35:('Dry woodland','Bare branching trees cast shadows across dry terrain in an environment review.','Contrasting biome and reusable environment assets.'),
39:('Bistro prototype','A blocky chef stands beside a teal cooking station under hunt and cooking status text.','Best available prototype evidence; replace for public promotion after visual polish.'),
40:('A wish on Shampoo Island','Poofy stands on a sunny beach with a dialogue panel and a five-step activity objective.','Captures the playable story preview and interaction context.'),
42:('Creature work clearing','Colored creatures and a short conveyor occupy a green clearing beneath job and energy readouts.','Shows the production layout and creature roles.'),
43:('Dungeon stock run','Small figures occupy a tiled dungeon room with health and carried-stock readouts.','One half of the dungeon-to-shop loop.'),
44:('Market shift','Colored shelves and a shop counter fill a tiled room with stock and customer status.','Complements the dungeon capture with the selling phase.'),
46:('Raft construction demo','A small assembled wooden raft floats in a dark grid view beside a construction palette.','Assembled raft is more informative than the single-deck starting view.'),
47:('Gully prototype camera reference','A large bright foreground surface obscures much of the traversal scene beneath status text.','Reference only: obstructed camera cannot clearly show grapple traversal.'),
48:('Museum disguise prototype','Rounded and block-shaped museum props sit on plinths beneath ghost interaction instructions.','Readable prototype setting and prop-disguise context.'),
49:('Garden squad deployment','A small squad stands on one bank of a river while a purple enemy and cargo sit nearby.','Shows the spatial relationship between squad, obstacle and objective.'),
50:('Fort patrol route','A blocky defender and small enemies occupy a tiled route with fort status above.','Only available prototype capture; retain as internal gameplay evidence.'),
51:('Salvage command field','Teal units and industrial structures occupy a gray battlefield beneath a command HUD.','Recent packaged gameplay overview.'),
52:('Tracked combat unit','A teal low-poly tank with black tracks and a forward cannon appears on a neutral background.','Clear reusable vehicle asset detail.'),
57:('Guardian component rig','A teal mechanical walker with box-shaped limbs appears on a neutral background.','Contrasts the tracked vehicle with an articulated rig asset.'),
58:('Kingdoms postcard','Toy-like squads and a small puppy share a sand-colored arena between castle corners.','Clean HUD-free overview of the playful visual style.'),
60:('Build together','Two groups of toy soldiers stand in a sand arena beneath a shared construction interface.','Shows the cooperative building controls and shared progress.'),
62:('Gather around the monument','Toy squads form a ring around colorful building pads in a castle-sided sandbox.','Distinct cooperative composition without the HUD.'),
81:('Frontier production command','Industrial units and buildings occupy a gray base with vehicle production controls visible.','Current packaged interface and command context.'),
82:('Engineer placement preview','A circular placement overlay surrounds an industrial base beside engineer build controls.','Demonstrates construction affordances.'),
75:('Articulated roster','Several small tanks, trucks and walkers stand in rows on a neutral terrain strip.','Useful vehicle roster reference alongside gameplay.'),
84:('Scrapshift combat floor','Small modular combat robots face one another in a bordered arena beneath health and parts readouts.','Best available combat-floor prototype framing.'),
90:('Meet Poofy','A pale blue winged character stands on a bright beach beneath soft clouds.','Strong character-led cover with little interface clutter.'),
96:('Plumpy at Teacup Isle','A mint-green creature peeks from a white teacup among pastel candy decorations.','Distinctive character and environment asset detail.'),
95:('Island cove','A small sunny island with palms, docks and a ship is surrounded by turquoise water.','Wide environment overview suitable for an internal portfolio cover.'),
100:('Sailing between islands','A stylized ship sits between pastel islands and wooden piers on turquoise water.','Shows the sailing environment and ship asset.'),
87:('Paper portal story preview','Characters gather on the beach beneath a drawing suspended above a story dialogue panel.','Adds narrative context; explicitly a finale preview.'),
106:('VR beach desktop preview','A beach island with characters, floating instructions and menu buttons appears from an elevated observer view.','Reference only: desktop preview does not demonstrate headset interaction or comfort.'),
107:('Obstacle draft prototype','Three colored obstacle platforms sit beside a starting figure above a draft selection panel.','Shows the obstacle-building choices and prototype layout.'),
108:('Vehicle assembly prototype','A block-built vehicle faces a set of bowling pins in a gray test course.','Documents the assembly-to-driving challenge with visible controls.'),
109:('Harbor salvage prototype','A small yellow-decked boat floats beside a dock with salvage and cargo status visible.','Brighter and clearer than the earlier dark harbor screenshot.'),
}
VIDEOS={
1:('Artillery effects showcase','A labeled sequence shows hit flash, smoke marker, bomber, weapon release and detonation.','feature-demo','Short existing feature reel; not a complete game trailer.'),
2:('Environment asset flythrough','The review camera passes dry branches, logs and ground-root assets displayed in rows.','asset-demo','Useful for asset reuse; still needs a scene or gameplay showcase.'),
3:('Vehicle running gear','Teal tracked combat and cargo vehicles demonstrate their running gear against a neutral background.','asset-demo','Short rig demonstration; does not show the strategy game loop.'),
5:('Sailing to meet Plumpy','Poofy boards a candy ship, crosses the water and arrives at Plumpy on Teacup Isle.','gameplay','Best reviewed short journey showing traversal and an interaction destination.'),
6:('Character ability demonstrations','A labeled in-game reel demonstrates invisibility, bubble attack, wing swoop and shockwave abilities.','feature-demo','Useful mechanics reel; bright exposure and test labels remain.'),
7:('Tsunami story walkthrough','A long story walkthrough follows Tsunami, memory scenes and a reunion with Poofy.','story-walkthrough','Narrative reference and editing source; long-form footage, not a trailer. Audio not auditioned.'),
}
def main():
    shots=json.loads((EVIDENCE/'shortlist.json').read_text())
    videos=json.loads((EVIDENCE/'video-review.json').read_text())
    selected=[]
    for index,(title,alt,reason) in SHOTS.items():
        s=shots[index]; assert s['review_index']==index
        role='reference' if index in [47,106] else 'selected'
        selected.append(dict(project_id=s['project_id'],source_path=s['path'],sha256=s['sha256'],kind='screenshot',title=title,alt_text=alt,caption=alt,
            width=s['width'],height=s['height'],duration_seconds=None,curation=role,content_role='prototype-capture',review_notes=reason,review_evidence=f'contact-{index//12:02d}.jpg / tile {index}'))
    for index,(title,caption,role,reason) in VIDEOS.items():
        s=videos[index]; assert s['review_index']==index and s['decode_passed']
        selected.append(dict(project_id=s['project_id'],source_path=s['path'],sha256=hashlib.file_digest(open(s['path'],'rb'),'sha256').hexdigest(),kind='video',title=title,alt_text=caption,caption=caption,
            width=s['width'],height=s['height'],duration_seconds=s['duration_seconds'],curation='selected',content_role=role,review_notes=reason+' Six sampled frames visually reviewed; complete file decoded without errors. Audio clearance and full editorial playback remain pending.',review_evidence=f'video-{index}.jpg'))
    for i,s in enumerate(selected):
        s.update(sort_order=i,status='draft',rights='Unreviewed for external publication. Source project provenance retained; verify model, texture, font and audio licenses before approval.',credit='Source: '+Path(s['source_path']).as_posix(),reviewed_at='2026-11-11',selection_version=1)
    (ROOT/'data/marketing-selection.json').write_text(json.dumps(selected,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'{len(selected)} selections across {len({s["project_id"] for s in selected})} projects')
if __name__=='__main__': main()
