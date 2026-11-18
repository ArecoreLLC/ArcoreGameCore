"""Per-game music design records for the manual Suno workflow.

One JSON record (source of truth) and one rendered Markdown page per game
(31 catalog games + 50 roadmap tracks) under hub/data/music-design/, plus an
aggregate index.json for browser preview and Tauri seeding. Never calls Suno;
never overwrites recorded work (existing records and tracks are preserved).
"""
import argparse
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "hub" / "data" / "music-design"
CATALOG = ROOT / "hub" / "data" / "catalog.json"
ROADMAP = ROOT / "hub" / "data" / "capability-roadmap.json"
ARCH = ROOT / "workflows" / "adaptive-music-stems" / "archetypes.json"
GAME_STATUS = {"unassigned", "recommended", "excluded", "planned", "in_progress", "approved"}
TRACK_STATUS = {"prompt_ready", "generated", "stems_split", "approved", "rejected"}
VOCALS = {"none", "wordless", "sung"}

_spec = importlib.util.spec_from_file_location("amp", ROOT / "tools" / "adaptive_music_prompts.py")
amp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(amp)

CATALOG_RECOMMENDATIONS = {
    "beast-bistro-express": ("action-rock", "island food truck & crab boss hunt", "Fast-paced food truck driving and monster hunting fit high-energy guitar & drums."),
    "box-fort-brigade": ("arcade", "miniature cardboard fort physics siege", "Playful toy-scale structural destruction fits bright chiptune-arcade energy."),
    "chroma-turf": ("arcade", "elemental paint arena", "Vibrant elemental painting mechanics pair naturally with playful synth-arcade pulse."),
    "critter-contraptions": ("cozy", "friendly creature parcel factory", "Befriending creatures on a tiny parcel line calls for warm marimba and acoustic guitar."),
    "dungeon-dash-market": ("dark-fantasy", "slime dungeon & bustling fantasy shop", "Dungeon slime combat transitioning into timed shop shifts fits orchestral-fantasy tension and release."),
    "echo-forge": ("dark-fantasy", "ancient resonant cavern & world-organ", "Restoring a cavernous World-Organ through resonance puzzles suits haunting choir and low brass."),
    "flotsam-citadel": ("action-rock", "storm-tossed salvage raft", "Assembling a raft to survive a forty-second storm benefits from driving rock urgency."),
    "gully-giants": ("dark-fantasy", "mossy garden colossus climb", "Grappling up a towering garden golem to release armor pins fits heroic orchestral brass and taiko."),
    "haunt-and-haul": ("horror", "creepy nocturnal museum heist", "Ghosts disguising as museum props while guards scan fits sneaky detuned piano and suspenseful strings."),
    "lumen-weaver": ("dark-fantasy", "amber cathedral mirror chamber", "Redirecting amber light beams through sacred chambers suits mystical strings and resonant drones."),
    "pebblekin-command": ("dark-fantasy", "miniature stone-knight valley", "Knights, archers, and healers defending bridge repair against a monster fit heroic fantasy score."),
    "pocket-fort-patrol": ("arcade", "living-room bottle-cap trap defense", "Cardboard fort defense with bottle caps and toy traps fits upbeat arcade-electronic cues."),
    "scrapshift-arena": ("cyberpunk", "industrial robot salvage arena", "Fighting robot waves and rebuilding loadouts from scrap parts fits industrial synthwave and metallic percussion."),
    "skybound-sabotage": ("arcade", "skyline obstacle race course", "Competitive party obstacle drafting and racing fits energetic 140 BPM arcade leads."),
    "snap-rally": ("action-rock", "modular vehicle bowling track", "Building vehicles to smash physical pins suits punchy, adrenaline-fueled rock riffs."),
    "tugboat-tumble": ("cozy", "breezy harbor & salvage bay", "Winching salvage and balancing a harbor tugboat fits nautical-acoustic guitar and brush drums."),
    "3d-tower-assault": ("dark-fantasy", "wind-swept artillery battlefield", "Tower formations exchanging artillery across varied terrain suits martial drums and brass."),
    "acorn-anvil": ("cozy", "woodland village & four-age forest", "Growing a woodland village through four Ages fits pastoral acoustic guitar, flute, and marimba."),
    "arcore-openworld": ("dark-fantasy", "island, mountain & jungle frontier", "Exploring an 8km island and mountain landscape fits sweeping cinematic strings and woodwinds."),
    "salvage-circuit": ("cyberpunk", "industrial swarm-net storm wasteland", "Foundry vs. Swarm-Net armies in a closing industrial storm fits dark cyberpunk synth and distorted drums."),
    "sandbox-kingdoms": ("cozy", "tabletop toy-box sand castle", "Toy-box sand trucks and shared castle building fit whimsical glockenspiel and upright bass."),
    "scorched-frontier": ("cyberpunk", "alloy & fuel logistics warzone", "Three-faction alloy/fuel logistics RTS fits tense dystopian bass synth and sequenced arpeggiators."),
    "shammyverse": ("cozy", "soft cartoon island & sailing", "Already scored: 10 original island songs and reconstructions in Assets/Music and Sonic Alchemist."),
    "bubble-wishes-poofy-s-story-studio": ("cozy", "storybook island & narration studio", "Gentle story-driven island quests and narration fit soft acoustic fingerpicking and marimba."),
    "colobrary-battle-modes": ("arcade", "creature battle stadium", "Turn-based creature battles and team building fit classic chiptune-meets-modern arcade battle themes."),
    "plumpy-adventures": ("cozy", "sea-creature ocean platformer", "Cozy 2D sea-creature platforming with chapter bosses fits whimsical marimba and upbeat rhythm."),
    "tower-assault-web": ("arcade", "2D artillery duel", "Browser artillery duels fit punchy retro-arcade synth leads and tight 8-bit drums."),
    "shammiequest": ("cozy", "candy-world learning adventure", "Already has 4 theme/stage MP3 tracks in public/assets/mp3."),
    "shammiemath": ("cozy", "friendly math lab", "Already has 87 background/module audio tracks in apps/backend/.data/audio."),
    "shammyverse-vr-beach": ("cozy", "tropical VR beach vignette", "Shares the ShammyVerse island musical universe and ambient beach soundscape."),
    "engage-math-activity-collection": ("cozy", "playful classroom learning hub", "Curriculum math activities benefit from calm, non-distracting acoustic-marimba loops."),
}

DEFAULT_EXCLUSIONS = {
    "shammyverse": "Already has 10 full island songs and Sonic Alchemist reconstructions.",
    "shammiequest": "Already has 4 theme/stage MP3 tracks in public/assets/mp3.",
    "shammiemath": "Already has 87 module background audio tracks.",
    "scorched-frontier": "Already has adaptive calm/tension stems in Media/Audio/Sonic-v004.",
    "shammyverse-vr-beach": "Vignette in the ShammyVerse universe; reuses ShammyVerse island music.",
}

ROADMAP_RECOMMENDATIONS = {
    "lantern-heist": ("horror", "chiaroscuro clockwork museum", "Nocturnal museum infiltration with a shuttered amber lantern and automaton guard fits tense horror-stealth strings and detuned piano."),
    "clockwork-courier": ("action-rock", "rough-terrain buggy circuit", "Delivering fragile cargo on a rough-terrain buggy course fits driving rock bass and drums."),
    "pocket-expedition": ("dark-fantasy", "five-room ruin & two-phase guardian", "Exploring a generated ruin and escaping a two-phase guardian fits ominous orchestral strings and brass."),
    "garden-council": ("cozy", "turn-based garden rescue board", "Card-guided gardeners on a rescue board fit warm acoustic guitar and marimba."),
    "foundry-friends": ("cozy", "creature parcel machine workshop", "Creature-assisted parcel belts and machine repair fit playful marimba and upright bass."),
    "storm-harbor": ("action-rock", "leaking boat in stormy harbor current", "Patching a leaking boat across a stormy current calls for urgent rock rhythm."),
    "canopy-courier": ("cozy", "treetop parcel zip-route", "Treetop parcel delivery routes fit breezy acoustic guitar and brush percussion."),
    "bastion-tactics": ("dark-fantasy", "fogged courtyard rescue formation", "Leading six rescuers through a fogged courtyard fits tactical low brass and staccato strings."),
    "duelists-circuit": ("cyberpunk", "one-on-one robot duel arena", "Directional robot arena duels fit aggressive synth leads and industrial drums."),
    "pocket-town": ("cozy", "twelve-house miniature district", "Keeping a miniature twelve-house district supplied fits peaceful town-builder instrumentation."),
    "paper-council": ("cozy", "island village council hall", "Resolving an island dispute through story choices fits gentle acoustic motifs."),
    "echo-stage": ("arcade", "sound-powered rhythm puzzle stage", "Conducting sound-powered machines in a 60-second rhythm puzzle fits crisp arcade synth leads."),
    "living-wilds": ("cozy", "daylight-shifting nature habitat", "Observing a changing habitat across daylight shifts fits organic acoustic and woodwind textures."),
    "rescue-demolition": ("action-rock", "unstable shed demolition rescue", "Bracing an unstable shed and clearing blocked entrances under pressure fits punchy rock."),
    "orbital-salvage": ("cyberpunk", "zero-g station & underwater chamber", "Recovering drifting crates outside a station fits spaced-out arpeggiators and analog bass."),
    "sky-post": ("arcade", "aerial delivery ring course", "Flying a repairable aircraft through delivery rings fits upbeat arcade synth energy."),
    "learning-garden": ("cozy", "quantity-puzzle garden", "Growing a garden through quantity puzzles fits calm, encouraging marimba and guitar."),
    "clockwork-rooms": ("dark-fantasy", "time-rewinding escape rooms", "Rewinding machines across linked escape rooms fits mysterious strings and resonant percussion."),
    "patchwork-parade": ("cozy", "stitched-creature obstacle parade", "Guiding a stitched creature to a parade platform fits whimsical glockenspiel and upright bass."),
    "pocket-workshop-xr": ("cozy", "tabletop creature repair bench", "Seated tabletop creature-machine repair in XR fits intimate acoustic instruments."),
    "arena-relay": ("cyberpunk", "two-player battery robot arena", "Contesting a battery in a two-player robot arena fits high-tempo cyberpunk synthwave."),
    "community-isles": ("cozy", "cooperative island monument", "Two players building a shared island monument fits warm, welcoming island acoustics."),
    "marshlight-rescue": ("horror", "foggy marsh & patrolling creature", "Rescuing a traveler by boat while avoiding a marsh creature fits dread drones and sparse piano."),
    "clockwork-cartographer": ("dark-fantasy", "ancient surveyed ruin", "Mapping a ruin with limited survey tools fits exploratory pizzicato cello and woodwinds."),
    "railbound-salvage": ("cyberpunk", "industrial salvage rail yard", "Dispatching salvage trains to rebuild a machine fits industrial percussion and bass synth."),
    "reef-keeper": ("cozy", "underwater coral nursery", "Repairing underwater habitat pumps for a coral nursery fits soft marimba and glockenspiel."),
    "siege-workshop": ("dark-fantasy", "medieval siege rig test yard", "Building and testing a siege rig on a wall fits heavy taiko war drums and brass."),
    "moonbase-freight": ("cyberpunk", "low-gravity lunar loading bay", "Moving fragile modules onto a lunar rover fits atmospheric synth arpeggios."),
    "windmill-village": ("cozy", "wind-powered creature mill cottages", "Supplying six cottages around a wind-powered creature mill fits pastoral acoustic guitar."),
    "shadow-couriers": ("horror", "nocturnal guarded museum relay", "Passing a package through a guarded museum at night fits tense stealth strings and sub pulse."),
    "circuit-kitchen": ("arcade", "high-speed three-station kitchen", "Scheduling three kitchen stations without waste fits fast, playful arcade percussion."),
    "prism-patrol": ("dark-fantasy", "light-bridge dark miniature fort", "Redirecting light bridges for a patrol in a dark fort fits mystical strings and brass swells."),
    "gravity-parcel": ("dark-fantasy", "two-phase relic guardian arena", "Rematching a two-phase relic guardian fits epic boss-state brass ostinato and timpani."),
    "memory-orchard": ("cozy", "story-pattern fruit orchard", "Helping orchard residents remember patterns fits nostalgic fingerpicked guitar."),
    "puppet-theater": ("cozy", "cloth-curtain puppet stage", "Staging a two-minute puppet scene fits playful woodwinds, marimba, and brush snare."),
    "beatwing-rally": ("arcade", "musical ring flight course", "Flying rings on musical cues fits bright, beat-locked chiptune-arcade synths."),
    "tether-team": ("cyberpunk", "dual-drone docking bay", "Two repair drones stabilizing a swinging module fits clean analog bass and sci-fi percussion."),
    "emberwatch": ("dark-fantasy", "foggy night watchtower defense", "Defending a watchtower through a foggy night fits ominous strings and war drums."),
    "tiny-merchants": ("cozy", "three-stall market square", "Trading favors across three market stalls fits cheerful acoustic guitar and upright bass."),
    "floodgate-engineers": ("action-rock", "rising-water floodgate district", "Adjusting floodgates and repairing a failed pump under pressure fits driving rock rhythm."),
    "rover-garden": ("cozy", "seedling rover habitat patches", "Driving a small rover to deliver seedlings fits warm, optimistic indie instrumentation."),
    "chrono-arena": ("cyberpunk", "time-rewind robot combat arena", "Rewinding a bounded robot combat sequence fits glitch percussion and aggressive synth leads."),
    "quiet-library": ("cozy", "tactile quiet reading hall", "Returning books in a quiet sliding puzzle fits gentle, sparse acoustic guitar and marimba."),
    "salvage-submersible": ("cozy", "curated relic exhibition gallery", "Curating a relic exhibition under controlled lighting fits calm, reflective acoustic textures."),
    "living-fortress": ("dark-fantasy", "besieged courtyard fortress", "Repairing and defending a damaged courtyard with a small squad fits heroic brass and strings."),
    "tracksmith-trials": ("action-rock", "custom obstacle race track", "Building and racing an obstacle track against a ghost fits high-adrenaline rock guitar."),
    "wisp-shepherd": ("cozy", "glowing wisp twilight habitat", "Guiding twelve wisps to a sheltered nest fits delicate glockenspiel and acoustic guitar."),
    "sandcastle-stories": ("cozy", "tabletop beach sandcastle", "Building and stabilizing a tabletop sandcastle fits breezy beach marimba and brush drums."),
    "starboard-signals": ("horror", "foggy acoustic-signal harbor", "Guiding a boat through fog by sound signals fits eerie drones and metallic percussion."),
    "frontier-assembly": ("cyberpunk", "salvage buggy frontier outpost", "Delivering salvaged parts by buggy to defend an outpost fits industrial synth and driving bass."),
}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rpath(d, gid):
    return Path(d) / f"{gid}.json"


def new_record(game, excluded_reason=None, scope="catalog", rec_arch=None, rec_setting="", rec_reason=""):
    status = "excluded" if excluded_reason else ("recommended" if rec_arch else "unassigned")
    return {
        "schema_version": 1,
        "game_id": game["id"],
        "name": game.get("name") or game.get("title") or game["id"],
        "scope": scope,
        "status": status,
        "exclusion_reason": excluded_reason or "",
        "recommended_archetype": rec_arch,
        "recommended_setting": rec_setting,
        "recommendation_reason": rec_reason,
        "archetype": None,
        "setting": "",
        "sonic_alchemist_project": "shammyverse-adaptive" if game["id"] == "shammyverse" else "",
        "soundcore_project": "sandbox-kingdoms" if game["id"] == "sandbox-kingdoms" else "",
        "modelforge_project": "",
        "tracks": [],
        "updated_at": now(),
    }


def init(catalog, d, exclude, reason="Already has music", roadmap=None):
    Path(d).mkdir(parents=True, exist_ok=True)
    created = []
    for g in catalog:
        p = rpath(d, g["id"])
        if p.exists():
            continue
        rec = CATALOG_RECOMMENDATIONS.get(g["id"], (None, "", ""))
        exc = DEFAULT_EXCLUSIONS.get(g["id"], reason) if g["id"] in exclude else None
        save(p, new_record(g, exc, scope="catalog", rec_arch=rec[0], rec_setting=rec[1], rec_reason=rec[2]))
        created.append(g["id"])
    if roadmap:
        for r in roadmap:
            p = rpath(d, r["id"])
            if p.exists():
                continue
            rec = ROADMAP_RECOMMENDATIONS.get(r["id"], (None, "", ""))
            exc = reason if r["id"] in exclude else None
            save(p, new_record(r, exc, scope="roadmap", rec_arch=rec[0], rec_setting=rec[1], rec_reason=rec[2]))
            created.append(r["id"])
    return created


def assign(rec, arch_doc, archetype, setting="", count=3, force_refresh_prompts=False):
    game = {"id": rec["game_id"], "title": rec["name"], "archetype": archetype,
            "setting": setting, "has_music": False}
    tracks = amp.generate(arch_doc, {"tracks_per_game": count, "games": [game]})
    by_id = {t["track_id"]: t for t in rec["tracks"]}
    arch = arch_doc["archetypes"][archetype]
    new_tracks = []
    for t in tracks:
        prev = by_id.get(t["track_id"])
        if prev and (prev.get("suno", {}).get("url") or (prev.get("status") != "prompt_ready" and not force_refresh_prompts)):
            new_tracks.append(prev)
            continue
        if prev and not force_refresh_prompts:
            new_tracks.append(prev)
            continue
        new_tracks.append({
            "track_id": t["track_id"], "title": t["title"], "status": "prompt_ready",
            "vocals": prev["vocals"] if prev else "none", "bpm": t["bpm"], "style_prompt": t["style"],
            "lyrics": prev["lyrics"] if (prev and prev.get("vocals") == "sung" and prev.get("lyrics")) else t["lyrics"],
            "instruments": [{"name": i["name"], "stem": i["stem"], "keep": i["core"]} for i in arch["instruments"]],
            "stems_requested": t["keep_stems"],
            "states": t["states"],
            "suno": prev["suno"] if prev else {"url": "", "clip_id": "", "model": "", "generated_at": ""},
            "files": prev["files"] if prev else [], "notes": prev["notes"] if prev else ""})
    rec["tracks"] = new_tracks
    rec["archetype"], rec["setting"] = archetype, setting
    if rec["status"] in ("unassigned", "recommended"):
        rec["status"] = "planned"
    rec["updated_at"] = now()
    return rec


def apply_recommendations(d, arch_doc, catalog, roadmap):
    Path(d).mkdir(parents=True, exist_ok=True)
    updated = []
    all_games = [("catalog", g, CATALOG_RECOMMENDATIONS.get(g["id"], (None, "", ""))) for g in catalog]
    all_games += [("roadmap", r, ROADMAP_RECOMMENDATIONS.get(r["id"], (None, "", ""))) for r in roadmap]
    for scope, g, (rec_arch, rec_setting, rec_reason) in all_games:
        p = rpath(d, g["id"])
        if p.exists():
            rec = load(p)
        else:
            exc = DEFAULT_EXCLUSIONS.get(g["id"])
            rec = new_record(g, exc, scope=scope, rec_arch=rec_arch, rec_setting=rec_setting, rec_reason=rec_reason)
        rec["scope"] = rec.get("scope") or scope
        rec["recommended_archetype"] = rec_arch
        rec["recommended_setting"] = rec_setting
        rec["recommendation_reason"] = rec_reason
        if g["id"] in DEFAULT_EXCLUSIONS and rec["status"] in ("unassigned", "recommended", "excluded"):
            rec["status"] = "excluded"
            rec["exclusion_reason"] = DEFAULT_EXCLUSIONS[g["id"]]
            if not any(t.get("suno", {}).get("url") for t in rec.get("tracks", [])):
                rec["tracks"] = []
        elif rec["status"] in ("unassigned", "recommended") and rec_arch:
            assign(rec, arch_doc, rec_arch, rec_setting, 3, force_refresh_prompts=True)
            rec["status"] = "recommended"
        save(p, rec)
        updated.append(g["id"])
    return updated


def write_index(d):
    records = [load(f) for f in sorted(Path(d).glob("*.json")) if f.name != "index.json"]
    save(Path(d) / "index.json", records)
    return records


def errors(rec, allowed_stems=None):
    if allowed_stems is None:
        allowed_stems = set(load(ARCH)["suno_stem_categories"])
    e = []
    if rec.get("status") not in GAME_STATUS:
        e.append(f"{rec.get('game_id')}: bad status")
    for t in rec.get("tracks", []):
        tid = t.get("track_id")
        if t.get("status") not in TRACK_STATUS:
            e.append(f"{tid}: bad status")
        if t.get("vocals") not in VOCALS:
            e.append(f"{tid}: bad vocals")
        if not t.get("style_prompt"):
            e.append(f"{tid}: missing style_prompt")
        if t.get("vocals") == "sung" and not t.get("lyrics", "").strip():
            e.append(f"{tid}: sung track needs lyrics")
        if t.get("status") in ("generated", "stems_split", "approved") and not t["suno"].get("url"):
            e.append(f"{tid}: generated track needs suno url")
        insts = t.get("instruments", [])
        if not insts:
            e.append(f"{tid}: no instruments")
        for i in insts:
            if i.get("name") not in allowed_stems or i.get("stem") not in allowed_stems:
                e.append(f"{tid}: instrument '{i.get('name')}' / stem '{i.get('stem')}' not in Suno 22 Standard + 68 Beta options")
    return e


def render(rec):
    L = [f"# Music design: {rec['name']}", "",
         f"Game: `{rec['game_id']}` ({rec.get('scope', 'catalog')})  \nStatus: **{rec['status']}**  \nArchetype: {rec['archetype'] or rec.get('recommended_archetype') or 'unassigned'}"
         + (f"  \nSetting: {rec.get('setting') or rec.get('recommended_setting')}" if (rec.get("setting") or rec.get("recommended_setting")) else "")]
    if rec.get("recommendation_reason"):
        L += ["", f"Recommendation: {rec['recommendation_reason']}"]
    if rec.get("exclusion_reason"):
        L += ["", f"Excluded: {rec['exclusion_reason']}"]
    for t in rec["tracks"]:
        L += ["", f"## {t['title']} (`{t['track_id']}`)", "",
              f"Status: {t['status']} | Vocals: {t['vocals']} | BPM: {t['bpm']}", ""]
        s = t["suno"]
        if s.get("url"):
            L += [f"Suno: {s['url']} (clip `{s.get('clip_id','')}`, model {s.get('model') or '?'}, {s.get('generated_at') or '?'})", ""]
        if s.get("analysis"):
            an = s["analysis"]
            L += [
                "**Suno MCP Audio Analysis (0-credit beat/key/section map)**",
                "",
                f"- Detected BPM: `{an.get('bpm_detected')}` | Key: `{an.get('key_detected')}` | Meter: `{an.get('time_signature')}/4` | Bars: `{an.get('bars_detected')}` | Sections: `{len(an.get('sections') or [])}`",
                f"- Recommended 32-bar loop window: Bar `{an.get('recommended_loop_start_bar')}` (`{an.get('recommended_loop_start_s')}s`–`{an.get('recommended_loop_end_s')}s`)",
                f"- Tags / terms: `{', '.join(an.get('terms') or [])}`",
                "",
            ]
        if s.get("candidates"):
            L += [
                "**Generated Takes Comparison**",
                "",
                "| Take | Clip ID | Duration | Detected BPM | Key | Bars | Sections | Instrumental Prob | Score | URL |",
                "|---|---|---|---|---|---|---|---|---|---|",
            ]
            for c in s["candidates"]:
                inst_p = (c.get("labels") or {}).get("arrangement:instrumental", 0.0)
                rec_mark = " **(Recommended)**" if c.get("take") == s.get("recommended_take") else ""
                L += [
                    f"| Take {c['take']}{rec_mark} | `{c['clip_id']}` | {c['duration_s']}s | {c['bpm_detected']} | {c['key_detected']} | {c['bars_detected']} | {c['sections_count']} | {inst_p:.3f} | {c['quality_score']:.2f} | {c['url']} |"
                ]
            L += [""]
        L += ["**Style prompt**", "", "```", t["style_prompt"], "```", "",
              "**Instruments and Advanced Split stems**", "",
              "| Instrument | Stem category | Keep |", "|---|---|---|"]
        L += [f"| {i['name']} | {i['stem']} | {'yes' if i['keep'] else 'no'} |" for i in t["instruments"]]
        L += ["", f"Stems requested: {', '.join(t['stems_requested'])}", "",
              "**Lyrics / section structure**" + (" (sung lyrics)" if t["vocals"] == "sung" else ""), "",
              "```", t["lyrics"], "```"]
        if t.get("files"):
            L += ["", "Files:"] + [f"- `{f['path']}` {f.get('kind','')} {f.get('sha256','')}" for f in t["files"]]
        if t.get("notes"):
            L += ["", f"Notes: {t['notes']}"]
    return "\n".join(L) + "\n"


INTEGRATED_MUSIC_SUMMARIES = {
    "3d-tower-assault": (
        "Adaptive music integrated (Wind-Swept Artillery, Sonic-v001, 115 BPM, 32-bar 66.78s loop, 0.85s fade-in/out): "
        "4 bar-quantized stems — Strings (SW_Music_Strings_v001), Percussion (SW_Music_Percussion_v001), "
        "Drums (SW_Music_Drums_v001), Brass (SW_Music_Brass_v001). States: Explore (Setup screen: Strings -5 dB) -> "
        "Tension (Aiming turn: +Percussion, +Drums) -> Combat (Firing/projectiles in flight, 8s hold: +Brass 0 dB) -> "
        "Boss (Nuclear/Kamikaze/Sudden Death/Critical HP: full orchestral boost)."
    ),
    "acorn-anvil": (
        "Adaptive music integrated (Forest Loop, Sonic-v001, 92 BPM, 32-bar 83.48s loop, 0.85s fade-in/out): "
        "4 bar-quantized stems — Keyboards (SW_Music_Keyboards_v001), Synth (SW_Music_Synth_v001), "
        "Bass (SW_Music_Bass_v001), Drums (SW_Music_Drums_v001). States: Explore (Age I gathering: Keyboards -2 dB + Synth -5 dB) -> "
        "Tension (Age II+, troops trained, or relic held: +Bass -1 dB) -> Combat (Active skirmish, 8s hold: +Drums -1 dB) -> "
        "Boss (Briar Golem, Harvest Festival, Relic countdown, or Hall <65% HP)."
    ),
    "chroma-turf": (
        "Adaptive music integrated (Chroma-Turf Main Theme, Sonic-v001, 140 BPM, 32-bar 54.86s loop, 0.85s fade-in/out): "
        "4 bar-quantized stems — Keyboards (SW_Music_Keyboards_v001), Synth (SW_Music_Synth_v001), "
        "Bass (SW_Music_Bass_v001), Drums (SW_Music_Drums_v001). States: Explore (Neutral tile: Keyboards + Synth) -> "
        "Tension (Grass/food tile: +Bass) -> Combat (Magma/slow tile: +Drums) -> Boss (Ice/speed tile: full 140 BPM arcade mix)."
    ),
    "box-fort-brigade": (
        "Adaptive music integrated (Box-Fort Brigade Main Theme, Sonic-v001, 140 BPM, 32-bar 54.86s loop, 0.85s fade-in/out): "
        "4 bar-quantized stems — Keyboards (SW_Music_Keyboards_v001), Synth (SW_Music_Synth_v001), "
        "Bass (SW_Music_Bass_v001), Drums (SW_Music_Drums_v001). States: Explore (Commander planning: Keyboards + Synth) -> "
        "Tension (Squad moving or Hero possessed: +Bass) -> Combat (Hero firing at fort or breach unlocked, 6s hold: +Drums) -> "
        "Boss (Capturing objective core)."
    ),
    "beast-bistro-express": (
        "Adaptive music integrated (Beast Bistro Express Main Theme, Sonic-v001, 150 BPM, 32-bar 51.20s loop, 0.85s fade-in/out): "
        "4 bar-quantized stems — Guitar (SW_Music_Guitar_v001), Synth (SW_Music_Synth_v001), "
        "Bass (SW_Music_Bass_v001), Drums (SW_Music_Drums_v001). States: Explore (Driving food truck: Guitar -2 dB + Synth -5 dB) -> "
        "Tension (On foot prepping/cooking at stove: +Bass) -> Combat (Hunting Coconut Crab in clearing, 6s hold: +Drums) -> "
        "Boss (Claw Slam / Shell Burst windup or Mutation Hunt 2+)."
    ),
    "snap-rally": (
        "Adaptive music integrated (Snap Rally Main Theme, Sonic-v001, 150 BPM, 32-bar 51.20s loop, 0.85s fade-in/out): "
        "4 bar-quantized stems — Guitar (SW_Music_Guitar_v001), Synth (SW_Music_Synth_v001), "
        "Bass (SW_Music_Bass_v001), Drums (SW_Music_Drums_v001). States: Explore (Vehicle assembly in garage: Guitar + Synth) -> "
        "Tension (Driving proving lane: +Bass) -> Combat (Boosting / high speed >=450 cm/s, 6s hold: +Drums) -> "
        "Boss (Pin deck impact or final 8s countdown)."
    ),
    "sandbox-kingdoms": (
        "Adaptive music integrated (Sandbox Kingdoms Main Theme, Sonic-v001, 92 BPM, 32-bar 83.48s loop, 0.85s fade-in/out): "
        "4 bar-quantized stems — Guitar (SW_Music_Guitar_v001), Woodwinds (SW_Music_Woodwinds_v001), "
        "Bass (SW_Music_Bass_v001), Drums (SW_Music_Drums_v001). States: Explore (Free Play / Cardboard Era 0: Guitar -2 dB + Woodwinds -5 dB) -> "
        "Tension (Wood/Plastic Era or active sand delivery: +Bass) -> Combat (Toy squad skirmish or Golden Bucket carrier, 6s hold: +Drums) -> "
        "Boss (Sprinkler active, >=9 castle layers, or final 90s)."
    ),
    "critter-contraptions": (
        "Adaptive music generated & split via Suno MCP (Critter Contraptions - main theme, clip a4e91dfa-70cb-4963-aed7-56468104f9dc, "
        "128.88s, detected 91.2 BPM C major, stem group stemgrp_27fd5387-f39f-4d47-8aa4-bfe637d69658): "
        "12 Auto Split stems ready in Suno library (drums, bass, guitar, keyboard, percussion, strings, synth, woodwinds, brass, fx, vocals, backing_vocals)."
    ),
    "dungeon-dash-market": (
        "Adaptive music generated & split via Suno MCP (Dungeon Dash Market - main theme, clip e72a4697-1218-4736-b469-c99f839d1fc6, "
        "177.48s, 115 BPM dark-fantasy orchestral, stem group stemgrp_a2bd6c44-e2c4-49ca-b9a9-c571dd2c3d04): "
        "12 Auto Split stems ready in Suno library (strings, brass, drums, percussion, bass, woodwinds, keyboard, synth, guitar, fx, vocals, backing_vocals)."
    ),
}


def ingest_suno_mcp_pair(
    music_dir: Path,
    game_id: str,
    clips: list,
    analyses: dict,
    track_status: str = "generated",
    liked_ids: set = None,
    stem_group_id: str = "",
) -> dict:
    """Evaluate a pair of Suno MCP takes using 0-credit audio-analysis metadata,
    prefer the user's liked take unless a hard technical gate (< 36 bars) fails,
    compute a bar-aligned 32-bar loop window from the beat map, and store the
    full metadata on the game's music design record."""
    liked_ids = liked_ids or set()
    rec_path = rpath(music_dir, game_id)
    rec = load(rec_path)
    rec["status"] = "in_progress"
    rec["archetype"] = rec.get("archetype") or rec.get("recommended_archetype")
    t0 = rec["tracks"][0]
    target_bpm = float(t0.get("bpm") or 120.0)

    candidates = []
    best_cid = None
    best_score = -1e9
    for idx, c in enumerate(clips, 1):
        cid = c["id"]
        a = analyses.get(cid, {})
        dur = c.get("metadata", {}).get("duration") or a.get("duration_s") or 0.0
        bpm = a.get("bpm") or target_bpm
        key = a.get("key") or "Unknown"
        tsig = a.get("time_signature") or 4
        beats = a.get("beats") or []
        downbeats = [b["time_s"] for b in beats if b.get("bar_position") == 1]
        bars_count = len(downbeats)
        sections = a.get("sections") or []
        labels = {x["label"]: round(x["probability"], 3) for x in (a.get("labels") or [])}
        terms = a.get("terms") or []
        inst_prob = labels.get("arrangement:instrumental", 0.5)
        bpm_diff = min(abs(bpm - target_bpm), abs(bpm * 2 - target_bpm), abs(bpm / 2 - target_bpm))
        dur_bonus = 2.0 if dur >= 120.0 else (0.5 if dur >= 90.0 else -3.0)
        bar_gate_bonus = 2.0 if bars_count >= 36 else -2.0
        is_liked = cid in liked_ids
        like_bonus = 5.0 if (is_liked and bars_count >= 36) else 0.0
        score = inst_prob * 10.0 - (bpm_diff * 0.15) + min(bars_count, 48) * 0.1 + len(sections) * 0.2 + dur_bonus + bar_gate_bonus + like_bonus

        # Pick a 32-bar window starting near section 2/3 (~15-35s in) aligned to downbeats
        start_bar_idx = min(max(4, bars_count // 5), max(0, bars_count - 33)) if bars_count >= 33 else 2
        start_s = round(downbeats[start_bar_idx], 3) if start_bar_idx < len(downbeats) else round(start_bar_idx * 4.0 * 60.0 / bpm, 3)
        end_bar_idx = start_bar_idx + 32
        end_s = round(downbeats[end_bar_idx], 3) if end_bar_idx < len(downbeats) else round(start_s + 32.0 * 4.0 * 60.0 / bpm, 3)

        if score > best_score:
            best_score = score
            best_cid = cid
        candidates.append({
            "take": idx,
            "clip_id": cid,
            "url": c["song_url"],
            "liked": is_liked,
            "duration_s": dur,
            "bpm_detected": bpm,
            "key_detected": key,
            "time_signature": tsig,
            "bars_detected": bars_count,
            "sections_count": len(sections),
            "sections": sections,
            "labels": labels,
            "terms": terms,
            "recommended_loop_start_bar": start_bar_idx + 1,
            "recommended_loop_start_s": start_s,
            "recommended_loop_end_s": end_s,
            "quality_score": round(score, 3),
        })

    existing_cands = {c.get("clip_id"): c for c in (t0.get("suno", {}).get("candidates") or []) if c.get("clip_id")}
    new_cands_by_id = {c["clip_id"]: c for c in candidates}
    merged_candidates = []
    for old_cid, old_c in existing_cands.items():
        if old_cid not in new_cands_by_id:
            merged_candidates.append(old_c)
    for c in candidates:
        old_c = existing_cands.get(c["clip_id"], {})
        c["listen_rating"] = old_c.get("listen_rating")
        c["listen_notes"] = old_c.get("listen_notes", "")
        c["used_in_game"] = old_c.get("used_in_game", False)
        if old_c.get("midi_files"):
            c["midi_files"] = old_c["midi_files"]
        merged_candidates.append(c)
    for i, c in enumerate(merged_candidates, 1):
        c["take"] = i

    best_cand = next(x for x in merged_candidates if x["clip_id"] == best_cid)
    t0["status"] = track_status
    model_str = "v6 (MCP audio-create + audio-analysis + audio-stems-create mode=twelve)" if stem_group_id else "v6 (MCP audio-create + audio-analysis)"
    old_suno = t0.get("suno") or {}
    t0["suno"] = {
        "url": best_cand["url"],
        "clip_id": best_cid,
        "stem_group_id": stem_group_id or old_suno.get("stem_group_id"),
        "model": model_str,
        "generated_at": clips[0].get("created_at", now()),
        "recommended_take": best_cand["take"],
        "in_game_status": old_suno.get("in_game_status") or ("stems_split" if stem_group_id else "not_integrated"),
        "in_game_loop_s": old_suno.get("in_game_loop_s"),
        "in_game_stems": old_suno.get("in_game_stems") or [],
        "engine_asset_path": old_suno.get("engine_asset_path") or "",
        "analysis": {
            "bpm_detected": best_cand["bpm_detected"],
            "key_detected": best_cand["key_detected"],
            "time_signature": best_cand["time_signature"],
            "bars_detected": best_cand["bars_detected"],
            "recommended_loop_start_bar": best_cand["recommended_loop_start_bar"],
            "recommended_loop_start_s": best_cand["recommended_loop_start_s"],
            "recommended_loop_end_s": best_cand["recommended_loop_end_s"],
            "sections": best_cand["sections"],
            "labels": best_cand["labels"],
            "terms": best_cand["terms"],
        },
        "candidates": merged_candidates,
    }
    c1, c2 = candidates[0], candidates[1]
    stem_note = f" | 12-stem Auto Split group: {stem_group_id} (complete)" if stem_group_id else ""
    t0["notes"] = (
        f"Generated 2 takes via Suno MCP (v6) & analyzed via 0-credit audio-analysis:\n"
        f"- Take 1 ({c1['clip_id']}{', Liked' if c1['liked'] else ''}): {c1['url']} — {c1['duration_s']}s, detected {c1['bpm_detected']} BPM, {c1['key_detected']}, "
        f"{c1['bars_detected']} bars, {c1['sections_count']} sections, loop bars {c1['recommended_loop_start_bar']}..{c1['recommended_loop_start_bar']+32} "
        f"({c1['recommended_loop_start_s']}s–{c1['recommended_loop_end_s']}s), score={c1['quality_score']}\n"
        f"- Take 2 ({c2['clip_id']}{', Liked' if c2['liked'] else ''}): {c2['url']} — {c2['duration_s']}s, detected {c2['bpm_detected']} BPM, {c2['key_detected']}, "
        f"{c2['bars_detected']} bars, {c2['sections_count']} sections, loop bars {c2['recommended_loop_start_bar']}..{c2['recommended_loop_start_bar']+32} "
        f"({c2['recommended_loop_start_s']}s–{c2['recommended_loop_end_s']}s), score={c2['quality_score']}\n"
        f"Selected for stem split: Take {best_cand['take']} ({best_cid}){stem_note}."
    )
    rec["updated_at"] = now()
    save(rec_path, rec)
    return best_cand


SUNO_MATCH_STOPWORDS = {
    "3d", "2d", "vr", "xr", "web", "game", "games", "track", "test", "test2",
    "adaptive", "music", "main", "theme", "song", "loop", "stems", "mix", "remix",
    "part", "version", "v1", "v2", "v3", "the", "and", "of", "in", "for", "a", "an",
    "beach", "collection", "activity", "modes", "story", "studio",
}
STEM_TITLE_SUFFIXES = (
    " - vocals", " - backing vocals", " - drums", " - bass", " - guitar",
    " - keyboard", " - percussion", " - strings", " - synth", " - fx",
    " - brass", " - woodwinds", " - instrumental",
)


def _norm_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _title_tokens(s: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(t) >= 2 and t not in SUNO_MATCH_STOPWORDS]


def _game_anchors(rec: dict) -> tuple[str, list[str], list[str]]:
    name = rec.get("name") or rec["game_id"]
    full_norm = _norm_title(name)
    raw_words = re.findall(r"[a-z0-9]+", name.lower())
    anchors = []
    # Two-word prefix anchors like "3dtower" for "3D Tower Assault"
    if len(raw_words) >= 2 and len(raw_words[0] + raw_words[1]) >= 6:
        anchors.append(raw_words[0] + raw_words[1])
    sig_tokens = _title_tokens(name)
    if len(sig_tokens) >= 2:
        anchors.append("".join(sig_tokens[:2]))
    return full_norm, sorted(set(anchors)), sig_tokens


def match_suno_library_clips(clips: list[dict], records: list[dict]) -> dict[str, list[dict]]:
    """Match Suno library clips to GameCore games by title without false positives
    on generic tokens like '3D' alone, flagging multi-game hits as ambiguous and
    dropping unrelated Suno library songs."""
    game_index = []
    for rec in records:
        gid = rec["game_id"]
        full_norm, anchors, sig_tokens = _game_anchors(rec)
        known_ids = set()
        for t in rec.get("tracks") or []:
            s = t.get("suno") or {}
            if s.get("clip_id"):
                known_ids.add(s["clip_id"])
            for c in s.get("candidates") or []:
                if c.get("clip_id"):
                    known_ids.add(c["clip_id"])
        game_index.append((gid, full_norm, anchors, sig_tokens, known_ids))

    by_game: dict[str, list[dict]] = {}
    for cl in clips:
        cid = cl.get("id") or cl.get("clip_id")
        title = (cl.get("title") or "").strip()
        if not cid or not title:
            continue
        low_title = title.lower()
        if any(low_title.endswith(sfx) for sfx in STEM_TITLE_SUFFIXES):
            continue
        norm_c = _norm_title(title)
        c_tokens = set(_title_tokens(title))

        hits = []
        for gid, full_norm, anchors, sig_tokens, known_ids in game_index:
            if cid in known_ids:
                continue
            matched = []
            conf = None
            if len(full_norm) >= 6 and full_norm in norm_c:
                conf = "exact"
                matched.append(full_norm)
            else:
                hit_anchors = [a for a in anchors if len(a) >= 6 and a in norm_c]
                if hit_anchors:
                    conf = "high"
                    matched.extend(hit_anchors)
                elif len(sig_tokens) >= 2 and all(t in c_tokens for t in sig_tokens):
                    conf = "high"
                    matched.extend(sig_tokens)
                elif len(sig_tokens) == 1 and len(sig_tokens[0]) >= 6 and sig_tokens[0] in c_tokens:
                    conf = "high"
                    matched.append(sig_tokens[0])
            if conf:
                hits.append((gid, conf, matched))

        if not hits:
            continue
        # If one hit is exact on a longer specific compound (e.g. "3dtowerassault" vs "towerassault"),
        # prune shorter subset hits; keep variant games that share the exact prefix (e.g. "shammyverse").
        exact_hits = [h for h in hits if h[1] == "exact"]
        if len(exact_hits) == 1:
            ex_gid, _, ex_terms = exact_hits[0]
            ex_norm = ex_terms[0]
            hits = [
                h for h in hits
                if h[0] == ex_gid or any(ex_norm in t or t == ex_norm for t in h[2])
            ]
        cand_ids = [h[0] for h in hits]
        for gid, conf, matched in hits:
            eff_conf = "ambiguous" if len(hits) > 1 and conf != "exact" else ("ambiguous" if len(exact_hits) > 1 else conf)
            meta = cl.get("metadata") or {}
            entry = {
                "clip_id": cid,
                "title": title,
                "url": cl.get("song_url") or f"https://suno.com/song/{cid}",
                "created_at": cl.get("created_at", ""),
                "duration_s": meta.get("duration"),
                "model": meta.get("model", ""),
                "style": meta.get("style", ""),
                "liked": bool(cl.get("liked", False)),
                "match_confidence": eff_conf,
                "matched_terms": sorted(set(matched)),
            }
            if len(cand_ids) > 1:
                entry["match_candidates"] = cand_ids
            by_game.setdefault(gid, []).append(entry)
    return by_game


def sync_related_suno_tracks(music_dir: Path, clips: list[dict]) -> dict[str, int]:
    records = [load(p) for p in sorted(music_dir.glob("*.json")) if p.name != "index.json"]
    matched = match_suno_library_clips(clips, records)
    counts = {}
    for gid, entries in matched.items():
        p = rpath(music_dir, gid)
        rec = load(p)
        existing = {x["clip_id"]: x for x in (rec.get("related_suno_tracks") or []) if x.get("clip_id")}
        for e in entries:
            prev = existing.get(e["clip_id"], {})
            if prev.get("dismissed"):
                e["dismissed"] = True
            existing[e["clip_id"]] = e
        rec["related_suno_tracks"] = sorted(existing.values(), key=lambda x: x.get("created_at", ""), reverse=True)
        rec["updated_at"] = now()
        save(p, rec)
        counts[gid] = len(entries)
    return counts


def sync_catalog_descriptions(catalog_path: Path, music_dir: Path) -> None:
    if not catalog_path.is_file():
        return
    catalog = load(catalog_path)
    for g in catalog:
        gid = g["id"]
        md_file = music_dir / f"{gid}.json"
        md = load(md_file) if md_file.is_file() else {}
        arch = md.get("archetype") or md.get("recommended_archetype") or "unassigned"
        setting = md.get("setting") or md.get("recommended_setting") or ""
        t0 = md["tracks"][0] if md.get("tracks") else {}
        bpm = t0.get("bpm", 120)
        stems_req = ", ".join(t0.get("stems_requested", []))
        suno_info = t0.get("suno") or {}

        if gid in INTEGRATED_MUSIC_SUMMARIES:
            music_summary = INTEGRATED_MUSIC_SUMMARIES[gid]
            sa_asset_id = f"{gid}-adaptive"
            sa_version = "Sonic-v001 (4 stems, 48kHz 24-bit)"
        elif suno_info.get("analysis"):
            an = suno_info["analysis"]
            music_summary = (
                f"Adaptive music generated & analyzed via Suno MCP ({t0.get('title')}, Recommended Take {suno_info.get('recommended_take')}: "
                f"clip {suno_info.get('clip_id')}, detected {an.get('bpm_detected')} BPM, {an.get('key_detected')}, "
                f"{an.get('bars_detected')} bars, 32-bar loop window {an.get('recommended_loop_start_s')}s–{an.get('recommended_loop_end_s')}s): "
                f"target stems {stems_req}."
            )
            sa_asset_id = md.get("sonic_alchemist_project", "")
            sa_version = "suno-v6-analyzed"
        elif md.get("status") == "excluded":
            music_summary = f"Existing score utilized: {md.get('exclusion_reason') or 'Pre-scored project audio.'}"
            sa_asset_id = md.get("sonic_alchemist_project", "")
            sa_version = "existing-score"
        else:
            music_summary = (
                f"Adaptive music design ({arch} archetype, {bpm} BPM, {setting}): "
                f"Suno Advanced Split stems configured for {stems_req} across Explore, Tension, Combat, and Boss states."
            )
            sa_asset_id = md.get("sonic_alchemist_project", "")
            sa_version = "prompt-ready"

        base_assets = g.get("assets", "").split(" Adaptive music")[0].split(" Existing score utilized:")[0].strip()
        g["assets"] = f"{base_assets} {music_summary}".strip()

        links = g.setdefault("provider_links", [])
        sa_entry = next((p for p in links if p.get("provider") == "ArcoreSonicAlchemist"), None)
        if sa_entry is None:
            links.append({
                "provider": "ArcoreSonicAlchemist",
                "path": "X:/Projects/ArcoreSonicAlchemist",
                "asset_id": sa_asset_id,
                "version": sa_version,
                "description": music_summary,
            })
        else:
            sa_entry["asset_id"] = sa_asset_id or sa_entry.get("asset_id", "")
            sa_entry["version"] = sa_version
            sa_entry["description"] = music_summary

    save(catalog_path, catalog)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dir", default=str(DIR))
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init"); i.add_argument("--catalog", default=str(CATALOG))
    i.add_argument("--roadmap", default=""); i.add_argument("--exclude", nargs="*", default=list(DEFAULT_EXCLUSIONS))
    rec_p = sub.add_parser("recommend", help="populate recommended archetypes and tracks for all catalog and roadmap games")
    rec_p.add_argument("--catalog", default=str(CATALOG)); rec_p.add_argument("--roadmap", default=str(ROADMAP))
    a = sub.add_parser("assign"); a.add_argument("game"); a.add_argument("archetype")
    a.add_argument("--setting", default=""); a.add_argument("--count", type=int, default=3)
    r = sub.add_parser("record", help="log a manual Suno result")
    r.add_argument("game"); r.add_argument("track"); r.add_argument("--status", choices=sorted(TRACK_STATUS))
    r.add_argument("--url"); r.add_argument("--clip-id"); r.add_argument("--model")
    r.add_argument("--vocals", choices=sorted(VOCALS)); r.add_argument("--lyrics-file")
    r.add_argument("--style-file", help="replace style prompt if edited in Suno")
    r.add_argument("--note")
    sub.add_parser("render"); sub.add_parser("validate")
    o = p.parse_args(argv)
    d = Path(o.dir)
    if o.cmd == "init":
        rm = load(o.roadmap)["projects"] if o.roadmap else None
        c = init(load(o.catalog), d, set(o.exclude), roadmap=rm)
        print(f"created {len(c)} records")
    elif o.cmd == "recommend":
        u = apply_recommendations(d, load(ARCH), load(o.catalog), load(o.roadmap)["projects"])
        write_index(d)
        print(f"recommended {len(u)} records")
    elif o.cmd == "assign":
        rec = assign(load(rpath(d, o.game)), load(ARCH), o.archetype, o.setting, o.count)
        save(rpath(d, o.game), rec); print(f"{o.game}: {len(rec['tracks'])} tracks")
    elif o.cmd == "record":
        rec = load(rpath(d, o.game))
        t = next(x for x in rec["tracks"] if x["track_id"] == o.track)
        if o.status: t["status"] = o.status
        if o.url: t["suno"]["url"] = o.url; t["suno"]["generated_at"] = t["suno"]["generated_at"] or now()
        if o.clip_id: t["suno"]["clip_id"] = o.clip_id
        if o.model: t["suno"]["model"] = o.model
        if o.vocals: t["vocals"] = o.vocals
        if o.lyrics_file: t["lyrics"] = Path(o.lyrics_file).read_text(encoding="utf-8").strip()
        if o.style_file: t["style_prompt"] = Path(o.style_file).read_text(encoding="utf-8").strip()
        if o.note: t["notes"] = (t["notes"] + "\n" if t["notes"] else "") + o.note
        rec["updated_at"] = now()
        bad = errors(rec)
        if bad: raise SystemExit("; ".join(bad))
        save(rpath(d, o.game), rec)
    elif o.cmd == "render":
        for f in sorted(d.glob("*.json")):
            if f.name == "index.json":
                continue
            rec = load(f); (d / f"{rec['game_id']}.md").write_text(render(rec), encoding="utf-8")
        write_index(d)
        if d.resolve() == DIR.resolve():
            sync_catalog_descriptions(CATALOG, d)
    elif o.cmd == "validate":
        bad = [e for f in sorted(d.glob("*.json")) if f.name != "index.json" for e in errors(load(f))]
        print(json.dumps({"status": "failed" if bad else "passed", "errors": bad}, indent=2))
        raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
