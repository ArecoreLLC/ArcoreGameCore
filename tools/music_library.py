"""Shared game music library index, organized by the adaptive-music archetype taxonomy.

The library lives outside this repo (default X:/Projects/GameMusic/Library, or
$GAMECORE_MUSIC_LIBRARY). Each folder holds audio files plus a metadata.json
(schema gamecore.music-library.folder/v1) that is the source of truth for its
tracks. This tool validates those files against
workflows/adaptive-music-stems/archetypes.json and writes
hub/data/music-library/index.json, which the hub's Music library view reads.

It never moves, renames or edits audio or folder metadata.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "workflows" / "adaptive-music-stems" / "archetypes.json"
INDEX = ROOT / "hub" / "data" / "music-library" / "index.json"
DEFAULT_LIBRARY = Path(os.environ.get("GAMECORE_MUSIC_LIBRARY", "X:/Projects/GameMusic/Library"))
FOLDER_SCHEMA = "gamecore.music-library.folder/v1"
INDEX_SCHEMA = "gamecore.music-library.index/v1"
AUDIO_EXT = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
VOCALS = {"none", "wordless", "sung"}
STATUSES = {"library", "candidate", "retired"}
# Where in a game a cue is used. Orthogonal to the archetype (sound) and game_states (energy).
CONTEXTS = {
    "overworld", "town", "hub", "dungeon", "boss", "combat", "arena", "duel", "chase", "stealth",
    "investigation", "racing", "sports", "platformer", "puzzle", "minigame", "rhythm", "sailing",
    "underwater", "farming", "crafting", "building", "shop", "social", "sanctuary", "strategy-map",
    "ambient", "menu", "victory", "game-over", "credits",
}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def taxonomy(arch_doc):
    archetypes = arch_doc["archetypes"]
    parents = {}
    for aid, info in archetypes.items():
        parent = info.get("parent_archetype") or aid
        parents.setdefault(parent, [])
        if parent != aid:
            parents[parent].append(aid)
    states = list(arch_doc["states"])
    return archetypes, parents, states


def track_errors(track, where, archetypes, states, folder_dir):
    errs = []
    tid = track.get("id") or "?"
    p = f"{where}:{tid}"
    for key in ("id", "title", "file", "archetype"):
        if not str(track.get(key) or "").strip():
            errs.append(f"{p}: missing {key}")
    arch = track.get("archetype")
    if arch and arch not in archetypes:
        errs.append(f"{p}: unknown archetype '{arch}'")
    for sec in track.get("secondary_archetypes") or []:
        if sec not in archetypes:
            errs.append(f"{p}: unknown secondary archetype '{sec}'")
        elif sec == arch:
            errs.append(f"{p}: secondary archetype repeats primary '{sec}'")
    gs = track.get("game_states") or []
    if not gs:
        errs.append(f"{p}: game_states must list at least one of {states}")
    for s in gs:
        if s not in states:
            errs.append(f"{p}: unknown game state '{s}'")
    for c in track.get("contexts") or []:
        if c not in CONTEXTS:
            errs.append(f"{p}: unknown context '{c}'")
    if track.get("vocals", "none") not in VOCALS:
        errs.append(f"{p}: invalid vocals '{track.get('vocals')}'")
    if track.get("status", "library") not in STATUSES:
        errs.append(f"{p}: invalid status '{track.get('status')}'")
    f = track.get("file")
    if f:
        fp = folder_dir / f
        if Path(f).suffix.lower() not in AUDIO_EXT:
            errs.append(f"{p}: '{f}' is not a supported audio file")
        elif not fp.is_file():
            errs.append(f"{p}: file not found '{f}'")
    return errs


def scan(library, arch_doc):
    """Return (tracks, folders, errors) for every <library>/<folder>/metadata.json."""
    archetypes, parents, states = taxonomy(arch_doc)
    library = Path(library)
    tracks, folders, errs, seen = [], [], [], {}
    for meta in sorted(library.glob("*/metadata.json")):
        folder_dir = meta.parent
        try:
            doc = load(meta)
        except (OSError, json.JSONDecodeError) as e:
            errs.append(f"{folder_dir.name}: unreadable metadata.json ({e})")
            continue
        if doc.get("schema") != FOLDER_SCHEMA:
            errs.append(f"{folder_dir.name}: schema must be {FOLDER_SCHEMA}")
            continue
        listed = set()
        for t in doc.get("tracks") or []:
            e = track_errors(t, folder_dir.name, archetypes, states, folder_dir)
            errs.extend(e)
            tid = t.get("id")
            if tid in seen:
                errs.append(f"{folder_dir.name}:{tid}: duplicate id (also in {seen[tid]})")
            seen[tid] = folder_dir.name
            listed.add(t.get("file"))
            if e:
                continue
            arch = t["archetype"]
            tracks.append({
                **t,
                "folder": folder_dir.name,
                "path": f"{folder_dir.name}/{t['file']}",
                "parent_archetype": archetypes[arch].get("parent_archetype") or arch,
                "secondary_archetypes": t.get("secondary_archetypes") or [],
                "contexts": t.get("contexts") or [],
                "vocals": t.get("vocals", "none"),
                "status": t.get("status", "library"),
            })
        for audio in sorted(folder_dir.iterdir()):
            if audio.suffix.lower() in AUDIO_EXT and audio.name not in listed:
                errs.append(f"{folder_dir.name}: '{audio.name}' has no metadata entry")
        folders.append({
            "folder": folder_dir.name,
            "label": doc.get("label") or folder_dir.name,
            "description": doc.get("description", ""),
            "track_count": len(doc.get("tracks") or []),
        })
    tracks.sort(key=lambda t: t["id"])
    return tracks, folders, errs


def coverage(tracks, arch_doc):
    """Per archetype: library track count and which game states have no primary track yet."""
    archetypes, parents, states = taxonomy(arch_doc)
    out = []
    for parent, subs in parents.items():
        for aid in [parent, *subs]:
            primary = [t for t in tracks if t["archetype"] == aid and t["status"] == "library"]
            related = [t for t in tracks if aid in t["secondary_archetypes"] and t["status"] == "library"]
            have = {s for t in primary for s in t["game_states"]}
            out.append({
                "archetype": aid,
                "parent_archetype": parent,
                "primary_tracks": len(primary),
                "related_tracks": len(related),
                "missing_states": [s for s in states if s not in have],
            })
    return out


def build(library, arch_doc, generated_at=None):
    tracks, folders, errs = scan(library, arch_doc)
    archetypes, parents, states = taxonomy(arch_doc)
    index = {
        "schema": INDEX_SCHEMA,
        "generated_at": generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "library_root": Path(library).as_posix(),
        "game_states": states,
        "contexts": sorted(CONTEXTS),
        "families": [{"archetype": p, "sub_archetypes": subs} for p, subs in parents.items()],
        "folders": folders,
        "coverage": coverage(tracks, arch_doc),
        "tracks": tracks,
    }
    return index, errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("build", "validate", "coverage"):
        s = sub.add_parser(name)
        s.add_argument("--library", default=str(DEFAULT_LIBRARY))
    sub.choices["build"].add_argument("--out", default=str(INDEX))
    a = ap.parse_args(argv)
    arch_doc = load(ARCH)
    index, errs = build(a.library, arch_doc)
    for e in errs:
        print(f"ERROR {e}", file=sys.stderr)
    if a.cmd == "coverage":
        for c in index["coverage"]:
            gap = ", ".join(c["missing_states"]) or "-"
            print(f"{c['archetype']:<22} {c['parent_archetype']:<14} primary={c['primary_tracks']:<3} related={c['related_tracks']:<3} missing: {gap}")
        return 1 if errs else 0
    if errs:
        return 1
    if a.cmd == "build":
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {len(index['tracks'])} tracks from {len(index['folders'])} folders to {out}")
    else:
        print(f"OK: {len(index['tracks'])} tracks in {len(index['folders'])} folders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
