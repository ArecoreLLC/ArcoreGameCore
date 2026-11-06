# Example: AreCore V3 Pro sting at 1.5x

This is the production record for `AreCore_Logo_V3_Pro_1.5x.mp4`, made in November 2026: a 10.67 s 1080p24 studio sting with a soundtrack and a "MADE WITH ARECORE FOUNDRY" end card. It follows every stage of [the workflow](README.md).

All source paths below are relative to `ArcoreModelForge/design/arcore-logo/`. A copy of the finished MP4 also sits in this repository's `LogosStyles/` folder.

## Record

```yaml
sting_id: arecore-v3-pro-1.5x
brand: AreCore
source_scene: v3-pro/AreCore_Logo_V3_Pro.blend   # built from v3/Arcore_Logo_V3_Lamp.blend
output_folder: v3-pro-15x/
resolution: 1920x1080
fps: 24
frames: 1-256                                     # 10.67 s; source is 1-384 (16 s)
speed: 1.5
tools:
  blender: 5.2.3 (Cycles, AgX), device HIP (AMD)
  ffmpeg: 8.1.1 (gyan.dev full build)
  python: 3.14.0, numpy 2.5.4, scipy 1.18.1, tinysoundfont 0.3.7, pillow
sound_sources:
  soundfont: ArcoreSonicAlchemist/.runtime/sound-libraries/generaluser-gs/bank.sf2 (GeneralUser GS)
  foley: ArcoreSoundCore/sounds (Kenney, CC0)
end_card:
  line_1: MADE WITH ARECORE FOUNDRY
  line_2: Game Development Acceleration Framework
  font: fonts/Montserrat-Variable.ttf (SIL Open Font License)
checks:
  frames_complete: passed          # 256 of 256, none zero-size
  mp4_validation: passed           # 1920x1080, 24/1, 256 frames, audio 10.666 s, full decode clean
  contact_sheet_reviewed: passed
  audio_auditioned: not_run        # sync checked on a level plot only; nobody had listened yet
  end_card_copy_approved: not_run
```

## Version lineage

| Version | Script | What changed |
|---|---|---|
| V3 | `v3/build_v3.py` | The original lamp story: the lamp hops in, trips on its cable, falls and the bulb bursts |
| V3 Pro | `v3-pro/build_v3_pro.py` | Polish pass: stacked AreCore / GAME STUDIOS / ARECORE LLC lockup, darker stage lit by the lamp, no visible beam cone, a local bloom and MULTIPLY exposure pop instead of a white-out, and the emblem's cyan core ignites for a hero hold (16 s) |
| V3 Pro 1.5x | `v3-pro-15x/*.py` | Re-rendered at 1.5x, scored, end card added (10.67 s) |

## Commands, in order

From `ArcoreModelForge/design/arcore-logo/`:

```powershell
# 1. Scene (already built for V3 Pro)
blender -b --factory-startup -P v3-pro/build_v3_pro.py
# 3-4. GPU render with 3 -> 2 time remapping; run again to resume after a crash
blender -b v3-pro/AreCore_Logo_V3_Pro.blend -P v3-pro-15x/render_15x.py
# 5. Soundtrack and stems (tinysoundfont installed with --no-deps; it otherwise pulls in pyaudio)
python v3-pro-15x/soundtrack.py
# 6. End card frames
python v3-pro-15x/endcard.py
# 7. Composite, mux, validate
python v3-pro-15x/finish_15x.py
```

## Timing map

Source frames are V3 Pro's 24 fps frames. Time in the cut is `t(f) = f / 36 - 1 / 24`.

| Source frame | Cut time | Beat |
|---|---|---|
| 17, 65, 127, 175 | 0.43, 1.76, 3.49, 4.82 s | Lamp take-offs (175 is the big hop) |
| 46, 96, 155 | 1.24, 2.62, 4.26 s | Landings |
| 104-117 | 2.85-3.21 s | Curious glance |
| 201 | 5.54 s | Foot catches the cable ("uh-oh") |
| 219.5 | 6.06 s | Lamp hits the floor |
| 224 | 6.18 s | Bulb bursts |
| 252 | 6.96 s | Emblem core starts to ignite |
| 266 | 7.35 s | End card starts (cut frame 177) |
| 284 | 7.85 s | Hero hit, logo fully lit |
| 352 | 9.74 s | Fade to black begins (cut frame 235) |

## Cue sheet as built

| Beat | Music (GeneralUser GS program) | Effects |
|---|---|---|
| Lamp act, 0-5.5 s | Warm pad (89) in D, chord change on each landing | Room tone |
| Each hop | Pizzicato (45): grace note on the crouch, climbing note on take-off, lower note on landing | Creak on the crouch, metal click on take-off, light metal impact on landing; panned left to right with the lamp |
| Glance | Celesta (8) question figure | |
| Big hop | Harp (46) run up to the apex | |
| Trip | Two pizzicato notes ("uh-oh"); pad cuts out | Light metal hit, cloth drag for the cable, creak on the teeter |
| Fall | Silence | Synthesized electrical buzz following the spotlight flicker, accelerating whoosh |
| Impact and burst | | Heavy metal and plate impacts, bounces, heavy and medium glass, zap, seven glass fragments, low thump, power-down sweep |
| Ignition | Celesta flickers; reversed crash cymbal swells into the hit | Rising air, then a low hum (D, 73.4 Hz) that stutters with the core |
| Hero | D add9 on strings (48), choir (52), contrabass (43), timpani (47), crash; tubular bells (14) four-note AreCore motif, celesta sparkle | Hum carries the hold |
| Fade | Everything fades with the picture | |

Master: music reverb 2.6 s, effects reverb 0.9 s, tanh soft clip, -1 dBFS peak, about -21.6 dBFS RMS. Stems: `music.wav`, `sfx.wav`. QA plot: `soundtrack-timeline.png`.

## End card as built

- Cut frames 177-256, starting after the bulb bursts and the core ignites.
- A cobalt rule (RGB 120, 165, 255) draws out from the centre to ±240 px at y = 997.
- "MADE WITH" in Montserrat 400, soft grey, and "ARECORE FOUNDRY" in Montserrat 800, platinum, 40 px, baseline y = 975. The line rises 14 px into place while its letter spacing settles from 17 to 9 px.
- "Game Development Acceleration Framework" in Montserrat 500, 25 px, cobalt, baseline y = 1036, fading up 11 frames later.
- A blurred shadow behind both lines. Everything fades out from cut frame 235 with the picture.

## What went wrong and how it was handled

| Problem | Fix |
|---|---|
| The first V3 Pro render ran on the CPU at about 21 s per frame | Standalone renders ignore the user's GPU preferences. Added a render script that enables HIP |
| The HIP render stopped at frame 144 with "Launch failed in HIP queue" | Ran the same command again. Placeholders and no-overwrite skipped the 143 finished frames |
| ffmpeg `drawtext` crashed (fontconfig) | Drew the end card with Pillow as PNG frames |
| `pip install tinysoundfont` failed building pyaudio | Installed with `--no-deps`; offline rendering does not need pyaudio |
| The burst flash washed the frame grey under AgX | Changed the compositor mix from MIX to MULTIPLY |

## Outputs

In `v3-pro-15x/`: `AreCore_Logo_V3_Pro_1.5x.mp4`, `soundtrack.wav`, `music.wav`, `sfx.wav`, `frames/`, `endcard/`, `mp4-validation.json`, `final-contact.png`, `soundtrack-timeline.png`, render logs and the four scripts.
