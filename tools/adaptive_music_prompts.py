"""Generate Suno Custom Mode prompt packs for adaptive game music.

Offline and deterministic: reads archetypes.json + a games list, writes one
JSON manifest and one Markdown pack per game. It never calls Suno.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "workflows" / "adaptive-music-stems"
BPM_STEPS = [0, -8, 10]
VARIANTS = [
    ("A", "main theme", "memorable repeating melodic motif"),
    ("B", "alternate region", "different key, blended sub-archetype palette, new motif"),
    ("C", "late-game variation", "darker harmony, hybrid escalation palette, motif reprised"),
]

# V2 Sub-category pairing & cross-genre blend map: primary_archetype -> (B_sub, C_sub, C_accent)
V2_SUBCATEGORY_BLENDS = {
    "cozy": ("nautical-folk", "storybook-orchestral", "cosmic-ambient"),
    "nautical-folk": ("storybook-orchestral", "modern-tactics", "noir-mystery"),
    "lofi-workshop": ("nautical-folk", "neon-synthfunk", "storybook-orchestral"),
    "storybook-orchestral": ("lofi-workshop", "cosmic-ambient", "medieval-siege"),
    "dark-fantasy": ("medieval-siege", "cosmic-ambient", "mech-industrial"),
    "medieval-siege": ("storybook-orchestral", "modern-tactics", "dark-fantasy"),
    "cosmic-ambient": ("noir-mystery", "mech-industrial", "dark-fantasy"),
    "cyberpunk": ("neon-synthfunk", "mech-industrial", "modern-tactics"),
    "neon-synthfunk": ("lofi-workshop", "retro-chiptune-rock", "mech-industrial"),
    "mech-industrial": ("neon-synthfunk", "modern-tactics", "horror"),
    "arcade": ("retro-chiptune-rock", "neon-synthfunk", "mech-industrial"),
    "retro-chiptune-rock": ("neon-synthfunk", "mech-industrial", "modern-tactics"),
    "horror": ("noir-mystery", "cosmic-ambient", "mech-industrial"),
    "noir-mystery": ("lofi-workshop", "mech-industrial", "dark-fantasy"),
    "action-rock": ("modern-tactics", "mech-industrial", "retro-chiptune-rock"),
    "modern-tactics": ("mech-industrial", "medieval-siege", "noir-mystery"),
}


def resolve_variant_archetypes(primary_id, index, archetypes_map):
    """Return (primary_variant_arch, accent_arch_or_None, variant_label) for track index."""
    if index == 0 or primary_id not in V2_SUBCATEGORY_BLENDS:
        return archetypes_map[primary_id], None, primary_id
    b_id, c_id, c_accent_id = V2_SUBCATEGORY_BLENDS[primary_id]
    if index == 1:
        sub = archetypes_map.get(b_id, archetypes_map[primary_id])
        return sub, None, b_id
    sub = archetypes_map.get(c_id, archetypes_map[primary_id])
    accent = archetypes_map.get(c_accent_id)
    return sub, accent, f"{c_id} + {c_accent_id}" if accent else c_id


def build_track(game, arch, index, archetypes_map=None):
    letter, label, motif = VARIANTS[index % len(VARIANTS)]
    var_arch, accent_arch, blend_tag = (
        resolve_variant_archetypes(game["archetype"], index, archetypes_map)
        if archetypes_map and game.get("archetype") in archetypes_map
        else (arch, None, game.get("archetype", ""))
    )
    bpm = var_arch["bpm"] if index > 0 and var_arch is not arch else arch["bpm"] + BPM_STEPS[index % len(BPM_STEPS)]
    insts = [i["name"] for i in var_arch["instruments"]]
    if accent_arch:
        for ai in accent_arch["instruments"]:
            if ai["name"] not in insts and len(insts) < 7:
                insts.append(ai["name"])
    genre_text = f"{var_arch['genre']} blended with {accent_arch['genre']}" if accent_arch else var_arch["genre"]
    setting = f", {game['setting']} atmosphere" if game.get("setting") else ""
    style = (f"{genre_text}, clean mix, dry studio recording, minimalist frequency separation, "
             f"{var_arch['mood']}{setting}, {', '.join(insts)}, {bpm} BPM, strict quantize, steady 4/4 rhythm, "
             f"{motif}, instrumental")
    return style, bpm, letter, label, var_arch, blend_tag


def lyrics(arch, sections, bpm=None):
    eff_bpm = bpm or arch["bpm"]
    cues = arch.get("section_cues", {})
    bass_inst = next((i["name"] for i in arch["instruments"] if "Bass" in i["name"] or i["name"] == "808"), arch["instruments"][0]["name"])
    lines = [
        "[Instrumental]",
        f"[Tempo: {eff_bpm} BPM, strict quantize, steady rhythm]",
        "",
        "[Intro - Bass Stem Only]",
        f"[Deep pulsing {bass_inst}, clean low-end drone, minimal]",
        "",
        "[Part 1 - Add Percussion Stem]",
        f"[{cues.get('[Verse 1 - Exploration Layer]', 'Crisp dry percussion and rhythm layer')}, steady 4/4 rhythm]",
        "",
        "[Part 2 - Add Melody Stem]",
        f"[{cues.get('[Pre-Chorus - Tension Build]', 'Sharp melodic ostinato')}, high frequency separation, dry studio]",
        "",
        "[Part 3 - Add Combat & Climax Layer]",
        f"[{cues.get('[Chorus - Combat Layer]', 'Full tactical intensity')}; {cues.get('[Bridge - Danger / Boss State]', 'tight separated stabs')}]",
        "",
        "[Outro - Strip Back]",
        "[Sub-bass pulse and distant percussion fade out]",
    ]
    return "\n".join(lines)


def select_games(data):
    excluded = set(data.get("exclude", []))
    return [g for g in data["games"]
            if g["id"] not in excluded and not g.get("has_music")]


def generate(arch_doc, games_doc):
    n = games_doc.get("tracks_per_game", 3)
    if n not in (2, 3):
        raise ValueError("tracks_per_game must be 2 or 3")
    out = []
    for game in select_games(games_doc):
        arch = arch_doc["archetypes"].get(game["archetype"])
        if arch is None:
            raise ValueError(f"{game['id']}: unknown archetype {game['archetype']}")
        for i in range(n):
            style, bpm, letter, label, var_arch, blend_tag = build_track(game, arch, i, arch_doc["archetypes"])
            core = [i2 for i2 in var_arch["instruments"] if i2["core"]]
            out.append({
                "track_id": f"{game['id']}-{letter}",
                "game": game["id"], "title": f"{game['title']} - {label}",
                "archetype": blend_tag, "bpm": bpm,
                "style": style,
                "lyrics": lyrics(var_arch, arch_doc["sections"], bpm),
                "keep_stems": sorted({c["stem"] for c in core}),
                "stem_map": {c["name"]: c["stem"] for c in var_arch["instruments"]},
                "states": [{"state": s["state"], "section": s["tag"]} for s in arch_doc["sections"]],
                "status": "prompt_ready",
            })
    return out


def check_style_length(tracks, limit=1000):
    return [t["track_id"] for t in tracks if len(t["style"]) > limit]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--games", default=str(WF / "games.example.json"))
    p.add_argument("--archetypes", default=str(WF / "archetypes.json"))
    p.add_argument("--out", required=True, help="output directory (consumer-owned)")
    a = p.parse_args(argv)
    arch_doc = json.loads(Path(a.archetypes).read_text(encoding="utf-8"))
    games_doc = json.loads(Path(a.games).read_text(encoding="utf-8"))
    tracks = generate(arch_doc, games_doc)
    long = check_style_length(tracks)
    if long:
        raise SystemExit(f"style box too long: {long}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps({"schema_version": 1, "tracks": tracks}, indent=2), encoding="utf-8")
    for t in tracks:
        md = (f"# {t['title']} ({t['track_id']})\n\n**Style box**\n\n```\n{t['style']}\n```\n\n"
              f"**Lyrics box**\n\n```\n{t['lyrics']}\n```\n\n"
              f"Keep stems: {', '.join(t['keep_stems'])}\n")
        (out / f"{t['track_id']}.md").write_text(md, encoding="utf-8")
    print(f"wrote {len(tracks)} prompts to {out}")


if __name__ == "__main__":
    main()
