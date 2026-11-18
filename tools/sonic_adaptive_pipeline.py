"""Prepare, export, and validate a Sonic Alchemist adaptive-v1 music package from Suno stems.

Reusable offline tool for the 50+ GameCore library:
1. Copies selected hero stems from a Suno stem folder into the consuming game's
   Media/Audio/Sonic-v001/ directory with SHA-256 verification.
2. Authors a portable Sonic Alchemist `.arcore` session with bar-aligned loop
   region and micro-fades (`fadeIn`/`fadeOut` = 0.02s) for click-free looping,
   plus `Design.json` (`arcore-adaptive-v1`) and saves a copy to
   `ArcoreSonicAlchemist/compositions/<game-id>-adaptive.json`.
3. Invokes Sonic Alchemist's `export-adaptive.exe` to render aligned 48 kHz
   24-bit stereo `layer-NN.wav` loop stems and `assets.json`.
4. Validates PCM format, equal loop frame counts, non-silence, loop-seam step
   discontinuity (< 0.001), and coherent state headroom (< 0.99), then writes
   provenance receipts (`exporter.json`, `verified-copies.json`, `validation.json`).
"""
import argparse
import hashlib
import json
import math
import shutil
import struct
import subprocess
import wave
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SONIC_ROOT = ROOT.parent / "ArcoreSonicAlchemist"
DEFAULT_EXPORTER = SONIC_ROOT / "target/debug/examples/export-adaptive.exe"

DEFAULT_STEMS = [
    (1, "Strings", "7 Strings.wav", "strings", "SW_Music_Strings_v001"),
    (2, "Percussion", "6 Percussion.wav", "percussion", "SW_Music_Percussion_v001"),
    (3, "Drums", "2 Drums.wav", "drums", "SW_Music_Drums_v001"),
    (4, "Brass", "10 Brass.wav", "brass", "SW_Music_Brass_v001"),
]

DEFAULT_STATES = [
    ("Explore", 0.2, [
        {"enabled": True, "gainDb": -5.0},
        {"enabled": False, "gainDb": -60.0},
        {"enabled": False, "gainDb": -60.0},
        {"enabled": False, "gainDb": -60.0},
    ]),
    ("Tension", 0.5, [
        {"enabled": True, "gainDb": -2.0},
        {"enabled": True, "gainDb": -1.0},
        {"enabled": True, "gainDb": -3.0},
        {"enabled": False, "gainDb": -60.0},
    ]),
    ("Combat", 0.85, [
        {"enabled": True, "gainDb": -2.0},
        {"enabled": True, "gainDb": 0.0},
        {"enabled": True, "gainDb": 0.0},
        {"enabled": True, "gainDb": 0.0},
    ]),
    ("Boss", 1.0, [
        {"enabled": True, "gainDb": -1.0},
        {"enabled": True, "gainDb": 0.0},
        {"enabled": True, "gainDb": 1.0},
        {"enabled": True, "gainDb": 2.0},
    ]),
]

RICH_STATES = [
    ("Explore", 0.2, [
        {"enabled": True, "gainDb": -2.0},
        {"enabled": True, "gainDb": -5.0},
        {"enabled": False, "gainDb": -60.0},
        {"enabled": False, "gainDb": -60.0},
    ]),
    ("Tension", 0.5, [
        {"enabled": True, "gainDb": -1.0},
        {"enabled": True, "gainDb": -2.0},
        {"enabled": True, "gainDb": -1.0},
        {"enabled": False, "gainDb": -60.0},
    ]),
    ("Combat", 0.85, [
        {"enabled": True, "gainDb": 0.0},
        {"enabled": True, "gainDb": -1.0},
        {"enabled": True, "gainDb": 0.0},
        {"enabled": True, "gainDb": -1.0},
    ]),
    ("Boss", 1.0, [
        {"enabled": True, "gainDb": 1.0},
        {"enabled": True, "gainDb": 0.0},
        {"enabled": True, "gainDb": 1.0},
        {"enabled": True, "gainDb": 1.0},
    ]),
]

GAME_PROFILES = {
    "3d-tower-assault": {
        "bpm": 115.0,
        "key": "D minor",
        "bars": 32,
        "start_bar": 38,
        "master_db": -8.0,
        "stems": DEFAULT_STEMS,
        "states": DEFAULT_STATES,
    },
    "acorn-anvil": {
        "bpm": 92.0,
        "key": "G major",
        "bars": 32,
        "start_bar": 6,
        "master_db": -8.0,
        "stems": [
            (1, "Keyboards", "5 Keyboard.wav", "keyboards", "SW_Music_Keyboards_v001"),
            (2, "Synth", "7 Synth.wav", "synth", "SW_Music_Synth_v001"),
            (3, "Bass", "3 Bass.wav", "bass", "SW_Music_Bass_v001"),
            (4, "Drums", "2 Drums.wav", "drums", "SW_Music_Drums_v001"),
        ],
        "states": RICH_STATES,
    },
    "chroma-turf": {
        "bpm": 140.0,
        "key": "C minor",
        "bars": 32,
        "start_bar": 32,
        "master_db": -8.0,
        "stems": [
            (1, "Keyboards", "4 Keyboard.wav", "keyboards", "SW_Music_Keyboards_v001"),
            (2, "Synth", "6 Synth.wav", "synth", "SW_Music_Synth_v001"),
            (3, "Bass", "3 Bass.wav", "bass", "SW_Music_Bass_v001"),
            (4, "Drums", "2 Drums.wav", "drums", "SW_Music_Drums_v001"),
        ],
        "states": RICH_STATES,
    },
    "box-fort-brigade": {
        "bpm": 140.0,
        "key": "A minor",
        "bars": 32,
        "start_bar": 7,
        "master_db": -8.0,
        "stems": [
            (1, "Keyboards", "5 Keyboard.wav", "keyboards", "SW_Music_Keyboards_v001"),
            (2, "Synth", "7 Synth.wav", "synth", "SW_Music_Synth_v001"),
            (3, "Bass", "4 Bass.wav", "bass", "SW_Music_Bass_v001"),
            (4, "Drums", "3 Drums.wav", "drums", "SW_Music_Drums_v001"),
        ],
        "states": RICH_STATES,
    },
    "beast-bistro-express": {
        "bpm": 150.0,
        "key": "E minor",
        "bars": 32,
        "start_bar": 47,
        "master_db": -8.0,
        "stems": [
            (1, "Guitar", "4 Guitar.wav", "guitar", "SW_Music_Guitar_v001"),
            (2, "Synth", "7 Synth.wav", "synth", "SW_Music_Synth_v001"),
            (3, "Bass", "3 Bass.wav", "bass", "SW_Music_Bass_v001"),
            (4, "Drums", "2 Drums.wav", "drums", "SW_Music_Drums_v001"),
        ],
        "states": RICH_STATES,
    },
    "snap-rally": {
        "bpm": 150.0,
        "key": "E minor",
        "bars": 32,
        "start_bar": 54,
        "master_db": -8.0,
        "stems": [
            (1, "Guitar", "4 Guitar.wav", "guitar", "SW_Music_Guitar_v001"),
            (2, "Synth", "8 Synth.wav", "synth", "SW_Music_Synth_v001"),
            (3, "Bass", "3 Bass.wav", "bass", "SW_Music_Bass_v001"),
            (4, "Drums", "2 Drums.wav", "drums", "SW_Music_Drums_v001"),
        ],
        "states": RICH_STATES,
    },
    "sandbox-kingdoms": {
        "bpm": 92.0,
        "key": "G major",
        "bars": 32,
        "start_bar": 4,
        "master_db": -8.0,
        "stems": [
            (1, "Guitar", "3 Guitar.wav", "guitar", "SW_Music_Guitar_v001"),
            (2, "Woodwinds", "9 Woodwinds.wav", "woodwinds", "SW_Music_Woodwinds_v001"),
            (3, "Bass", "2 Bass.wav", "bass", "SW_Music_Bass_v001"),
            (4, "Drums", "1 Drums.wav", "drums", "SW_Music_Drums_v001"),
        ],
        "states": RICH_STATES,
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def exact_wav_duration(path: Path) -> float:
    with path.open("rb") as f:
        header = f.read(4096)
        pos = 12
        sr = 48000
        ch = 2
        bps = 32
        pcm_size = 0
        while pos + 8 <= len(header):
            cid = header[pos:pos + 4]
            csz = struct.unpack_from("<I", header, pos + 4)[0]
            if cid == b"fmt ":
                _, ch, sr, _, _, bps = struct.unpack_from("<HHIIHH", header, pos + 8)
            elif cid == b"data":
                pcm_size = csz
                break
            pos += 8 + csz + (csz & 1)
        if pcm_size <= 0:
            raise ValueError(f"Could not read WAV data chunk from {path}")
        return (pcm_size // (ch * (bps // 8))) / sr


def prepare_loop_folded_stem(
    src_path: Path,
    dest_path: Path,
    start_sec: float,
    loop_sec: float,
    crossfade_sec: float,
) -> float:
    """Copy the raw stem into the consumer project so Sonic Alchemist applies
    a clean fade-out / fade-in at the loop boundary."""
    shutil.copy2(src_path, dest_path)
    return exact_wav_duration(dest_path)


def build_session_and_design(
    title: str,
    bpm: float,
    key: str,
    beats_per_bar: int,
    bars: int,
    start_bar: int,
    master_db: float,
    fade_beats: float,
    stem_files: list,
    states: list = None,
):
    if states is None:
        states = DEFAULT_STATES
    bar_sec = beats_per_bar * 60.0 / bpm
    start_sec = round(start_bar * bar_sec, 6)
    loop_sec = bars * beats_per_bar * 60.0 / bpm
    end_sec = start_sec + loop_sec
    clip_fade = 0.85  # Smooth 0.85s fade-in and fade-out at the loop boundary so wrapping never stutters

    tracks = []
    layers = []
    for tid, name, rel_name, dur, role in stem_files:
        tracks.append({
            "id": tid,
            "name": name,
            "path": rel_name,
            "gainDb": 0.0,
            "muted": False,
            "solo": False,
            "edit": {
                "offset": start_sec,
                "trimStart": start_sec,
                "trimEnd": end_sec,
                "fadeIn": clip_fade,
                "fadeOut": clip_fade,
                "pan": 0.0,
                "fx": {"eq": [], "compressor": None},
            },
        })
        layers.append({
            "id": tid,
            "name": name,
            "duration": dur,
            "role": role,
        })

    session_doc = {
        "version": 3,
        "masterDb": master_db,
        "position": start_sec,
        "bpm": bpm,
        "key": key,
        "loopRegion": [start_sec, end_sec],
        "tracks": tracks,
    }
    design_doc = {
        "schema": "arcore-adaptive-v1",
        "title": title,
        "bpm": bpm,
        "key": key,
        "beatsPerBar": beats_per_bar,
        "bars": bars,
        "start": start_sec,
        "masterDb": master_db,
        "layers": layers,
        "states": [
            {"name": s_name, "intensity": s_int, "levels": s_levels}
            for s_name, s_int, s_levels in states
        ],
        "transition": {"boundary": "bar", "fadeBeats": fade_beats},
    }
    return session_doc, design_doc


def validate_export(export_dir: Path) -> dict:
    design = json.loads((export_dir / "design.json").read_text(encoding="utf-8"))
    assets = json.loads((export_dir / "assets.json").read_text(encoding="utf-8"))
    if assets.get("schema") != "arcore-adaptive-assets-v1":
        raise ValueError("Invalid assets.json schema")
    expected_beats = design["bars"] * design["beatsPerBar"]
    if assets.get("loopBeats") != expected_beats:
        raise ValueError("loopBeats mismatch")
    frames = round(assets["loopBeats"] * 60.0 / design["bpm"] * 48000)

    layer_metrics = []
    for entry in assets["assets"]:
        wav_path = export_dir / entry["file"]
        with wave.open(str(wav_path), "rb") as w:
            spec = (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes())
            if spec != (2, 3, 48000, frames):
                raise ValueError(f"{entry['file']}: expected (2, 3, 48000, {frames}), got {spec}")
            raw = w.readframes(frames)
        samples = [
            int.from_bytes(raw[i:i + 3], "little", signed=True) / 8388608.0
            for i in range(0, len(raw), 3)
        ]
        peak = max(abs(s) for s in samples)
        rms = math.sqrt(sum(s * s for s in samples) / len(samples))
        seam = max(abs(samples[ch] - samples[-2 + ch]) for ch in (0, 1))
        if not (0.0 < rms < 0.5 and peak < 0.99 and seam < 0.001):
            raise ValueError(
                f"{entry['file']}: failed acoustic gate (rms={rms:.4f}, peak={peak:.4f}, seam={seam:.6f})"
            )
        layer_metrics.append({
            "file": entry["file"],
            "name": entry["name"],
            "frames": frames,
            "peak": round(peak, 6),
            "rms": round(rms, 6),
            "seam_step": round(seam, 6),
            "sha256": digest(wav_path),
        })

    state_bounds = {}
    for st in design["states"]:
        if len(st["levels"]) != len(layer_metrics):
            raise ValueError(f"State {st['name']} level count mismatch")
        bound = sum(
            m["peak"] * (10.0 ** ((lvl["gainDb"] + design["masterDb"]) / 20.0))
            for m, lvl in zip(layer_metrics, st["levels"])
            if lvl["enabled"]
        )
        if bound >= 0.99:
            raise ValueError(f"State {st['name']} coherent sum bound {bound:.4f} >= 0.99")
        state_bounds[st["name"]] = round(bound, 6)

    return {
        "passed": True,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frames": frames,
        "duration_seconds": round(frames / 48000.0, 6),
        "layers": layer_metrics,
        "state_coherent_peak_bounds": state_bounds,
        "scope": "PCM format, equal loop length, non-silence, headroom, endpoint discontinuity. Does not certify musical quality, audible playback, or mixer-clock synchronization.",
    }


def auto_select_stems(source_dir: Path, bpm: float = 120.0, bars: int = 32):
    """Automatically rank Suno stems by RMS energy, order the top 4 by musical role,
    and pick the optimal 32-bar loop window."""
    bar_sec = 4.0 * 60.0 / bpm
    bar_frames = max(1, int(bar_sec * 48000))
    candidates = []
    for w in sorted(source_dir.glob("*.wav")):
        if w.name.startswith("0 "):
            continue
        raw_label = " ".join(w.stem.split()[1:]) if " " in w.stem else w.stem
        if raw_label in ("Vocals", "Backing Vocals", "FX", "Other"):
            continue
        data = w.read_bytes()
        pos = 12
        dpos = 0
        frames = 0
        while pos + 8 <= len(data):
            cid = data[pos:pos + 4]
            csz = struct.unpack_from("<I", data, pos + 4)[0]
            if cid == b"data":
                dpos = pos + 8
                frames = csz // 8
                break
            pos += 8 + csz + (csz & 1)
        if frames <= 0:
            continue
        total_bars = max(1, frames // bar_frames)
        bar_rms = []
        for b in range(total_bars):
            f0 = b * bar_frames
            vals = [
                struct.unpack_from("<f", data, dpos + f * 8)[0]
                for f in range(f0, min(frames, f0 + bar_frames), 256)
            ]
            bar_rms.append(math.sqrt(sum(v * v for v in vals) / max(1, len(vals))))
        overall_rms = math.sqrt(sum(r * r for r in bar_rms) / len(bar_rms))
        canon = "Keyboards" if raw_label == "Keyboard" else raw_label
        role = canon.lower().replace(" ", "_")
        candidates.append((overall_rms, canon, w.name, role, f"SW_Music_{canon.replace(' ', '')}_v001", bar_rms))

    candidates.sort(reverse=True)
    top4 = candidates[:4]
    if len(top4) < 4:
        raise ValueError(f"Expected at least 4 instrumental stems in {source_dir}, found {len(top4)}")

    def role_sort_key(item):
        _, canon, _, _, _, _ = item
        if canon in ("Strings", "Guitar", "Acoustic Guitar", "Keyboards", "Piano"):
            return 0
        if canon in ("Synth", "Synth Pad", "Woodwinds", "Percussion"):
            return 1
        if "Bass" in canon:
            return 2
        if canon in ("Drums", "Brass"):
            return 3
        return 1

    top4.sort(key=role_sort_key)
    total_bars = len(top4[0][5])
    best_b = 2
    best_score = -1e9
    for b in range(2, max(3, total_bars - bars - 1)):
        active = 0.0
        seam_diff = 0.0
        energy = 0.0
        for _, _, _, _, _, brms in top4:
            w_rms = brms[b:b + bars]
            if not w_rms:
                continue
            thr = max(0.008, 0.25 * (sum(brms) / len(brms)))
            active += sum(1 for r in w_rms if r >= thr) / len(w_rms)
            seam_diff += abs(w_rms[0] - w_rms[-1])
            energy += sum(w_rms) / len(w_rms)
        score = active * 2.0 + energy * 3.0 - seam_diff * 4.0
        if score > best_score:
            best_score = score
            best_b = b

    stems_cfg = [
        (idx + 1, canon, fname, role, unreal_name)
        for idx, (_, canon, fname, role, unreal_name, _) in enumerate(top4)
    ]
    return stems_cfg, best_b


def ensure_always_cook_music(project_root: Path, unreal_dest: str = "/Game/Audio/Music") -> None:
    ini_path = project_root / "Config" / "DefaultGame.ini"
    if not ini_path.is_file():
        return
    text = ini_path.read_text(encoding="utf-8")
    entry = f'+DirectoriesToAlwaysCook=(Path="{unreal_dest}")'
    if entry in text:
        return
    section = "[/Script/UnrealEd.ProjectPackagingSettings]"
    if section in text:
        text = text.replace(section, f"{section}\n{entry}", 1)
    else:
        text = text.rstrip() + f"\n\n{section}\n{entry}\n"
    ini_path.write_text(text, encoding="utf-8")


def sync_catalog_record(
    game_id: str,
    source_dir: Path,
    bpm: float,
    bars: int,
    start_bar: int,
    duration_sec: float,
    frames: int,
    imports: list,
    layers_validation: list,
) -> None:
    record_path = ROOT / "hub" / "data" / "music-design" / f"{game_id}.json"
    if not record_path.is_file():
        return
    rec = json.loads(record_path.read_text(encoding="utf-8"))
    rec["status"] = "in_progress"
    rec["sonic_alchemist_project"] = f"{game_id}-adaptive"
    if rec.get("tracks"):
        t0 = rec["tracks"][0]
        t0["status"] = "stems_split"
        t0["bpm"] = int(round(bpm))
        t0["instruments"] = [
            {"name": imp["name"], "stem": imp["name"], "keep": True}
            for imp in imports
        ]
        t0["stems_requested"] = sorted({imp["name"] for imp in imports})
        t0["suno"] = {
            "url": source_dir.as_posix(),
            "clip_id": f"{game_id}-main-theme",
            "model": "Suno Premier Stem Split (32-bit float 48kHz)",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        t0["files"] = [
            {
                "path": imp["path"],
                "kind": f"{imp['name']} ({imp['unreal_name']})",
                "sha256": imp["sha256"],
            }
            for imp in imports
        ]
        max_seam = max((m["seam_step"] for m in layers_validation), default=0.0)
        bar_sec = 4.0 * 60.0 / bpm
        s0 = start_bar * bar_sec
        s1 = s0 + duration_sec
        t0["notes"] = (
            f"Exported {bars}-bar loop (bars {start_bar}-{start_bar + bars}, "
            f"{s0:.2f}s-{s1:.2f}s, {duration_sec:.2f}s, {frames} frames @ 48kHz 24-bit) "
            f"via SonicAlchemist export-adaptive.exe with 0.85s fade-in/fade-out clip envelopes "
            f"(seam_step <= {max_seam:.6f}). Integrated into /Game/Audio/Music/SW_Music_*_v001 "
            f"with 4 states (Explore, Tension, Combat, Boss)."
        )
    save_json(record_path, rec)


def import_into_unreal(project_root: Path, unreal_dest: str = "/Game/Audio/Music") -> None:
    ensure_always_cook_music(project_root, unreal_dest)
    uprojects = list(project_root.glob("*.uproject"))
    if not uprojects:
        raise FileNotFoundError(f"No .uproject found in {project_root}")
    editor_cmd = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
    script_path = ROOT / "tools" / "unreal_import_adaptive_music.py"
    env = dict(**__import__("os").environ)
    env["UE-LocalDataCachePath"] = str(project_root / "DerivedDataCache")
    subprocess.run(
        [
            str(editor_cmd),
            str(uprojects[0]),
            f"-ExecutePythonScript={script_path}",
            "-unattended",
            "-nop4",
            "-nosplash",
            "-NullRHI",
            "-nosound",
            "-ddc=InstalledNoZenLocalFallback",
        ],
        env=env,
        check=True,
    )


def deploy_to_consumer(
    source_dir: Path,
    project_root: Path,
    game_id: str,
    title: str,
    version_tag: str = "Sonic-v001",
    bpm: float = None,
    key: str = None,
    beats_per_bar: int = 4,
    bars: int = None,
    start_bar: int = None,
    master_db: float = None,
    fade_beats: float = 2.0,
    exporter_exe: Path = DEFAULT_EXPORTER,
    overwrite: bool = False,
    unreal_dest: str = "/Game/Audio/Music",
    import_unreal: bool = False,
) -> dict:
    profile = GAME_PROFILES.get(game_id, {})
    bpm = bpm if bpm is not None else profile.get("bpm", 115.0)
    key = key if key is not None else profile.get("key", "D minor")
    bars = bars if bars is not None else profile.get("bars", 32)
    master_db = master_db if master_db is not None else profile.get("master_db", -8.0)
    if "stems" in profile:
        stems_cfg = profile["stems"]
        start_bar = start_bar if start_bar is not None else profile.get("start_bar", 38)
        states_cfg = profile.get("states", DEFAULT_STATES)
    else:
        try:
            stems_cfg, auto_bar = auto_select_stems(source_dir, bpm=bpm, bars=bars)
            start_bar = start_bar if start_bar is not None else auto_bar
            states_cfg = RICH_STATES
        except Exception:
            stems_cfg = DEFAULT_STEMS
            start_bar = start_bar if start_bar is not None else 38
            states_cfg = DEFAULT_STATES

    base_dir = project_root / "Media" / "Audio" / version_tag
    evidence_dir = project_root / "Media" / "Provenance" / version_tag
    if (base_dir.exists() or evidence_dir.exists()) and not overwrite:
        raise FileExistsError(f"Preserving existing {version_tag} in {project_root}. Pass --overwrite or a new version.")
    if overwrite:
        if base_dir.exists():
            shutil.rmtree(base_dir)
        if evidence_dir.exists():
            shutil.rmtree(evidence_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    bar_sec = beats_per_bar * 60.0 / bpm
    start_sec = round(start_bar * bar_sec, 6)
    loop_sec = bars * beats_per_bar * 60.0 / bpm

    stem_files = []
    source_origins = []
    for tid, name, src_fname, role, _ in stems_cfg:
        src_path = source_dir / src_fname
        if not src_path.is_file():
            raise FileNotFoundError(f"Missing stem file: {src_path}")
        dest_name = f"stem-{tid:02d}-{role}.wav"
        dest_path = base_dir / dest_name
        src_sha = digest(src_path)
        dur = prepare_loop_folded_stem(src_path, dest_path, start_sec, loop_sec, bar_sec)
        staged_sha = digest(dest_path)
        stem_files.append((tid, name, dest_name, dur, role))
        source_origins.append({
            "layer_id": tid,
            "name": name,
            "role": role,
            "original_path": str(src_path),
            "original_sha256": src_sha,
            "staged_path": dest_path.relative_to(project_root).as_posix(),
            "sha256": staged_sha,
            "duration_seconds": round(dur, 6),
        })

    session_doc, design_doc = build_session_and_design(
        title=title,
        bpm=bpm,
        key=key,
        beats_per_bar=beats_per_bar,
        bars=bars,
        start_bar=start_bar,
        master_db=master_db,
        fade_beats=fade_beats,
        stem_files=stem_files,
        states=states_cfg,
    )
    arcore_path = base_dir / f"{game_id}.arcore"
    design_path = base_dir / "Design.json"
    export_dir = base_dir / "Export"
    save_json(arcore_path, session_doc)
    save_json(design_path, design_doc)

    # Also register the composition in ArcoreSonicAlchemist/compositions if present
    comp_dir = SONIC_ROOT / "compositions"
    if comp_dir.is_dir():
        save_json(comp_dir / f"{game_id}-adaptive.json", design_doc)

    subprocess.run(
        [str(exporter_exe), str(arcore_path), str(design_path), str(export_dir)],
        check=True,
    )

    validation = validate_export(export_dir)
    save_json(evidence_dir / "validation.json", validation)

    imports = []
    for (tid, name, _, _, role), (_, _, _, _, unreal_name) in zip(stem_files, stems_cfg):
        layer_rel = (export_dir / f"layer-{tid:02d}.wav").relative_to(project_root).as_posix()
        imports.append({
            "layer_id": tid,
            "name": name,
            "role": role,
            "path": layer_rel,
            "sha256": digest(project_root / layer_rel),
            "unreal_name": unreal_name,
            "loop": True,
        })

    all_files = [
        {"path": p.relative_to(project_root).as_posix(), "sha256": digest(p)}
        for p in sorted(base_dir.rglob("*"))
        if p.is_file()
    ]
    save_json(
        evidence_dir / "verified-copies.json",
        {
            "schema": "arcore-sonic-handoff-v1",
            "game_id": game_id,
            "version": version_tag,
            "unreal_destination": unreal_dest,
            "source_origins": source_origins,
            "imports": imports,
            "files": all_files,
        },
    )

    sonic_commit = "unknown"
    sonic_dirty = False
    if (SONIC_ROOT / ".git").exists():
        sonic_commit = subprocess.check_output(
            ["git", "-C", str(SONIC_ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
        sonic_dirty = bool(
            subprocess.check_output(
                ["git", "-C", str(SONIC_ROOT), "status", "--porcelain"], text=True
            ).strip()
        )
    save_json(
        evidence_dir / "exporter.json",
        {
            "repository": "ArcoreSonicAlchemist",
            "commit": sonic_commit,
            "workingTreeDirty": sonic_dirty,
            "binarySha256": digest(exporter_exe),
            "license": "LicenseRef-ArcoreStudio-SunoPremierCommercial",
            "source_directory": str(source_dir),
        },
    )
    ensure_always_cook_music(project_root, unreal_dest)
    sync_catalog_record(
        game_id=game_id,
        source_dir=source_dir,
        bpm=bpm,
        bars=bars,
        start_bar=start_bar,
        duration_sec=validation["duration_seconds"],
        frames=validation["frames"],
        imports=imports,
        layers_validation=validation["layers"],
    )
    if import_unreal:
        import_into_unreal(project_root, unreal_dest)
    return validation


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True, help="Suno stem directory")
    p.add_argument("--project", required=True, help="Target Unreal/Godot game project root")
    p.add_argument("--game-id", required=True, help="Catalog game ID (e.g. 3d-tower-assault)")
    p.add_argument("--title", required=True, help="Adaptive design title")
    p.add_argument("--version", default="Sonic-v001")
    p.add_argument("--bpm", type=float, default=None)
    p.add_argument("--key", default=None)
    p.add_argument("--bars", type=int, default=None)
    p.add_argument("--start-bar", type=int, default=None)
    p.add_argument("--master-db", type=float, default=None)
    p.add_argument("--unreal-dest", default="/Game/Audio/Music")
    p.add_argument("--import-unreal", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args(argv)
    res = deploy_to_consumer(
        source_dir=Path(args.source),
        project_root=Path(args.project),
        game_id=args.game_id,
        title=args.title,
        version_tag=args.version,
        bpm=args.bpm,
        key=args.key,
        bars=args.bars,
        start_bar=args.start_bar,
        master_db=args.master_db,
        overwrite=args.overwrite,
        unreal_dest=args.unreal_dest,
        import_unreal=args.import_unreal,
    )
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
