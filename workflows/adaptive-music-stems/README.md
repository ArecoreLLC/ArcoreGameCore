# Adaptive music stems: Suno → Sonic Alchemist handoff

Status: scaffold; applicable to 2D and 3D consumers. Covers prompt generation and tracking only.

Goal: 2–3 mostly instrumental tracks per game (Shammyverse and any game with `has_music: true` are skipped). Each track has a built-in energy arc (explore → tension → combat → boss → resolve) and a locked instrument list so stems separate cleanly.

## What is automated

| Stage | Owner | State |
|---|---|---|
| Prompt packs per game (style box, lyrics box, stem map) | [tools/adaptive_music_prompts.py](../../tools/adaptive_music_prompts.py) + [archetypes.json](archetypes.json) | implemented, offline |
| Suno generation and stem split | Suno (manual) | **not connected**, see below |
| Section slicing, MIDI transcription, adaptive state machine | Sonic Alchemist | not duplicated here; see [music-reconstruction](../music-reconstruction/README.md) |
| In-engine acceptance | Consumer project | per [shared contract](../../shared/migration-contract.md) |

## Suno connection: blocked, needs a decision

Suno has no official public API or MCP that I could confirm. Third-party wrappers use scraped sessions or cookies, which risk account bans and ToS violations and must not hold credentials in this repo. Per repo rules, agents should only register the GameCore hub, so any Suno adapter would be added to `shared/ecosystem.json` → `mcp.servers` and called through the hub. That is not done. Until you choose an approved integration, use the manifest as a manual queue: paste each prompt into Suno Custom Mode, then record results in `manifest.json` (`status`, Suno IDs, file hashes, rights metadata).

## Usage

```
python tools/adaptive_music_prompts.py --games workflows/adaptive-music-stems/games.json --out <consumer-owned dir>
```

1. Copy [games.example.json](games.example.json) to `games.json`; list each game with an archetype (`cyberpunk`, `dark-fantasy`, `cozy`, `arcade`, `horror`, `action-rock`) and optional `setting`.
2. Generate the packs. Tracks A/B/C differ in motif, BPM offset and key hint, keeping instrumentation constant so a game's tracks share stems.
3. Generate in Suno, audition, then run stem separation and keep only the `keep_stems` categories.
4. Hand sources to Sonic Alchemist; record approvals. A render is a candidate until it is auditioned.

## Per-game music design pages

Every catalog game gets a record in `hub/data/music-design/<game-id>.json` (source of truth) and a rendered `<game-id>.md` page. Each track stores the full Suno style prompt, the lyrics box (sung lyrics when `vocals` is `sung`, otherwise the section-tag structure), the instruments with their Advanced Split stem categories, the stems kept, the Suno URL/clip ID/model, files with hashes, and status. Tool: [music_design.py](../../tools/music_design.py).

```
python tools/music_design.py init                       # one record per catalog game; never overwrites
python tools/music_design.py assign <game> cozy --setting village
python tools/music_design.py record <game> <track> --status generated --url <suno url> --vocals none
python tools/music_design.py render                     # rewrite the Markdown pages
python tools/music_design.py validate
```

If you edit the prompt in Suno, pass the final text with `--style-file` or `--lyrics-file` so the record shows what was actually used. The hub UI does not yet show these pages.

## Reusable Sonic Alchemist → Unreal deployment pipeline (50+ games)

Once Suno stems are exported (for example `X:\Projects\GameMusic\<Game>\<Song>\*.wav`), run the reusable pipeline tool [sonic_adaptive_pipeline.py](../../tools/sonic_adaptive_pipeline.py) to author the Sonic Alchemist `.arcore` session, slice a bar-aligned loop with micro-fades, export 48 kHz 24-bit stereo `layer-NN.wav` stems, and verify acoustic gates before importing into Unreal:

```
python tools/sonic_adaptive_pipeline.py --source "X:\Projects\GameMusic\3dTowerAssault\Wind-Swept artillery" --project "X:\Projects\3dTowerAssault" --game-id 3d-tower-assault --title "3D Tower Assault - Wind-Swept Artillery v001" --overwrite
python tools/sonic_adaptive_pipeline.py --source "X:\Projects\GameMusic\Acorn&Anvil\Forest Loop" --project "X:\Projects\Acorn&Anvil" --game-id acorn-anvil --title "Acorn & Anvil - Forest Loop v001" --overwrite --score-header "X:\Projects\Acorn&Anvil\Source\AcornAnvil\Private\AcornAnvilMusicScore.h"
```

### Pipeline steps (reusable across all games)

1. **Inspect & select 4 hero stems:** Isolate 4 core stems from Suno's 32-bit float 48 kHz export (e.g. `Strings`, `Percussion`, `Drums`, `Brass` for `3d-tower-assault`, or `Keyboards`, `Synth`, `Bass`, `Drums` for `acorn-anvil`) and discard silent or low-energy filler stems so layers do not clash.
2. **Stage into `<Game>/Media/Audio/Sonic-v001/`:** Copy the 4 source stems with SHA-256 verification and exact frame-count duration headers (`exact_wav_duration`).
3. **Author `.arcore` + `Design.json` (`arcore-adaptive-v1`):**
   - Pick a full **32-bar loop window** (`128` beats — `66.78s` at 115 BPM or `83.48s` at 92 BPM) where all 4 hero stems are active across the arrangement.
   - Set `edit.offset = start`, `edit.trimStart = start`, `edit.trimEnd = end`, and `edit.fadeIn = edit.fadeOut = 0.85` (0.85s gentle fade-in and fade-out at the loop boundary) so Suno stems wrap smoothly without beat-phase stutter (`seam_step <= 0.00001`).
   - Define the 4 adaptive game states (`Explore`, `Tension`, `Combat`, `Boss`) with per-layer `gainDb` and `masterDb = -8.0` so the coherent peak sum across all enabled layers stays `< 0.99`.
   - Save a copy of `Design.json` to `ArcoreSonicAlchemist/compositions/<game-id>-adaptive.json` so the GameCore hub and Sonic Alchemist discover it automatically.
4. **Validate and export through the Sonic Alchemist MCP:** The pipeline calls the registered `sonic-alchemist` stdio server (`adaptive_validate` against the `.arcore` session, then `adaptive_export`), which renders aligned 48 kHz 24-bit stereo `layer-01.wav`..`layer-04.wav`, `design.json`, and `assets.json` with a `runtime` manifest (linear gains with the master, bar/fade seconds, equal-power curve, per-layer peak/RMS/seam step/SHA-256) into `<Game>/Media/Audio/Sonic-v001/Export/`, then verifies frames and hashes. The reply is kept as `Media/Provenance/<version>/sonic-manifest.json`. Build the server once with `cargo build --release -p arcore-audio --bin sonic-adaptive-mcp` in ArcoreSonicAlchemist; `--via exe` keeps the legacy `export-adaptive.exe` path offline. Agents reach the same tools through the GameCore hub's `music_production` (operation `tools/list` first) and must not register the Sonic server directly.
5. **Verify acoustic gates & provenance:** Check `(channels, sampwidth, framerate, nframes) == (2, 3, 48000, expected_frames)`, `0 < rms < 0.5`, `peak < 0.99`, `seam_step < 0.001`, and state coherent peak bounds `< 0.99`. Write `Media/Provenance/Sonic-v001/{validation.json, verified-copies.json, exporter.json}`.
6. **Unreal Editor import & cooker config:** Verify SHA-256 hashes from `verified-copies.json`, import `SW_Music_<Stem>_v001` into `/Game/.../Audio/Music`, set `looping = True` and `virtualization_mode = PlayWhenSilent`, and ensure `+DirectoriesToAlwaysCook=(Path="/Game/.../Audio/Music")` is present in `Config/DefaultGame.ini` when stems are loaded dynamically via `LoadObject<USoundWave>`.
7. **Runtime: GameCore adaptive-music modules.** Select `adaptive-music` and `unreal-adaptive-music` in `Config/GameCore.project.json` and run `python tools/gamecore.py sync --project <Game>` (module-only consumers need no smoke declaration for sync/check). Pass `--score-header` to the pipeline to generate the compiled `GameCore::AdaptiveScore` from the export. The game keeps only its state rules: hold an `Arcore::Unreal::FAdaptiveMusicPlayer` on a long-lived actor, `Start` it with the imported waves, and `Tick` it with the desired state and volume. Stems start sample-locked on a Quartz clock and transitions follow the audio clock with Sonic Alchemist's equal-power fades. Use `GameCore::EngagementHold` for the 6–8 s combat hold, and add an editor test that compares the compiled score with `design.json` via `ParseAdaptiveDesign`. Tower Assault (`Source/TowerAssault3D/Private/TAMusic.cpp`) is the reference consumer. See [AdaptiveMusic.md](../../shared/cpp/AdaptiveMusic.md) and [AdaptiveMusicPlayer.md](../../3d/unreal/AdaptiveMusicPlayer.md).

## Caveats on the source prompt design

- Instruments and stem targets are restricted to Suno's exact **22 Standard options** (`Lead Vocal`, `Drums`, `Bass`, `Backing Vocals`, `Piano`, `Electric Guitar`, `Percussion`, `Strings`, `Synth`, `Acoustic Guitar`, `Other`, `Synth Pad`, `Synth Bass`, `Guitar`, `Brass`, `Organ`, `Lead Guitar`, `Synth Keys`, `Rhythm Electric Guitar`, `Electric Piano`, `Upright Bass`, `Keyboards`) and **68 Beta options** (`Kick`, `Snare`, `Risers`, `Synth Strings`, `Synth Lead`, `Woodwinds`, `Rhythm Acoustic Guitar`, `Flute`, `Harp`, `Tambourine`, `Trumpet`, `Arpeggiator`, `Accordion`, `Fiddle`, `Slide Guitar`, `Vocoder`, `Violin`, `Synth Brass`, `Mandolin`, `Choir`, `Banjo`, `Bells`, `Clarinet`, `Tenor Saxophone`, `Trombone`, `Shaker`, `French Horn`, `Glockenspiel`, `Cello`, `Timpani`, `Harmonica`, `Marimba`, `Vibraphone`, `Saxophone`, `Orchestra`, `Cymbals`, `Clap`, `Oboe`, `Celesta`, `Congas`, `Drone`, `Alto Saxophone`, `Double Bass`, `Ukulele`, `Harpsichord`, `Baritone Saxophone`, `Xylophone`, `Tuba`, `Bass Guitar`, `Whistle`, `808`, `Bongos`, `Bassoon`, `Cowbell`, `Viola`, `Sitar`, `Steel Drums`, `Piccolo`, `Theremin`, `Bagpipes`, `Hi-Hat`, `Music Box`, `Melodica`, `Tabla`, `Koto`, `Djembe`, `Taiko`, `Didgeridoo`).
- Use `Synth Pad` explicitly (not generic `Synth`) when extracting pads, and separate `Rhythm Electric Guitar` and `Lead Guitar` (rather than generic `Electric Guitar`) to avoid electric guitar stem bleed.
- Section tags guide Suno but do not guarantee clean, loop-aligned, or equal-length sections. Slice at bar boundaries after listening and check loop seams. Cue words in the lyrics box can be sung if you do not add "instrumental" to the style box.
- Not-run so far: no Suno generation, no in-engine playback. Only the generator's unit tests ran.

## Shared music library

Reusable cues that are not tied to one game live outside this repo (default `X:/Projects/GameMusic/Library`, or `$GAMECORE_MUSIC_LIBRARY`). Each folder holds the audio plus a `metadata.json` (`gamecore.music-library.folder/v1`) that tags every track with an `archetype` and optional `secondary_archetypes` from [archetypes.json](archetypes.json), the energy `game_states` it covers (explore, tension, combat, boss, resolve), usage `contexts` (menu, town, boss, racing…), an optional `world_flavor`, Suno IDs and review scores.

```
python tools/music_library.py validate   # check every folder's metadata against the taxonomy
python tools/music_library.py coverage   # archetype x game-state gaps worth generating next
python tools/music_library.py build      # write hub/data/music-library/index.json for the hub
```

The hub's **Music library** view browses the index by archetype family and biome style, shows a coverage matrix, and each game's Music tab lists library cues that already fit its archetype. Desktop playback reads the files in place (the Tauri asset scope includes the library root); nothing is copied into the repo.
