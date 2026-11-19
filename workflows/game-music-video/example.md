# Worked example: ShammyVerse soundtrack videos (November 2026)

The first production of this workflow: ten gameplay music videos (one per in-game song) and a finale review for
ShammyVerse, a Godot 4.7.2 island adventure. The game's scripts and videos stay in the ShammyVerse repository, under
`Design/Iterations/music-videos-v001/` and `finale-review-v001/`. This page records the commands, decisions and
lessons, not game source.

## Setup

| Item | Value |
|---|---|
| Engine | Godot 4.7.2 stable, console executable, Forward+ |
| Capture | Movie Maker, `--fixed-fps 30`, window 1920×1200 via a temporary `override.cfg` (the game's 16:10 base is 1280×800) |
| Audio | Exact runtime MP3s (stem-separated masters, about 2–3 dB quieter than the earlier mixes), game effects at −4 dB, no normalization |
| Captions | Draft ASR-aligned lyric cues (421 across eight songs); two songs have no captions |
| Output | MP4 H.264 CRF 20 / AAC 192 kb/s, about 230 MB per 4-minute song; previews 960×600 under 28 MB |

## Decisions from owner review

1. **First sample (single take):** the candy-ship challenge, then a long victory flight, then the voyage. The owner
   rejected "a lot of flying in circles" and asked for no gameplay spoilers, because the videos may be used as
   trailers.
2. **Second sample (trailer montage):** the title screen with PRESS START, then about 18 short shots cut on lyric
   starts, with the HUD hidden. Mechanics were capped: two ball whacks, never the finished ship. Purposeful flights
   only, ending on a close-up. Accepted with framing fixes: a swing post and palm trunks filled the frame in three
   shots. That led to the camera guard and the contact-sheet review.
3. **Settings per song (spoiler-light):** the voyage past the salt and sweet islands; the sweet-island friends and the
   canyon seen only from outside (never the riddles); the companion's charge at a plain rock (never the one hiding the
   quest item); friends' abilities on their island; the spider caves without the finished web; sea and coast for the
   two uncaptioned story songs.

## Commands (as run before the GameCore extraction)

```powershell
# Dry-run every song headless (minutes for the album)
Godot --headless --path game --fixed-fps 30 --script <record_music_video.gd> -- --song=<id>
# Record and encode one song (15–25 min each; two streams in parallel)
python Design/Iterations/music-videos-v001/make_music_video.py <id>
```

With GameCore the equivalent commands are `tools/game_music_video.py dry-run` and `record`, using the vendored base.

## Lessons

- **Movie Maker ignores `--resolution`.** It records at the window size, so set
  `window/size/window_width_override` and `window/size/window_height_override` in a temporary `override.cfg`. Two
  parallel recordings once raced on that file. The tool now reference-counts it and restores any pre-existing file.
  A killed run can still leave it behind: check for it after interrupting a recording.
- **Count frames, not milliseconds.** The first finale recorder used a wall-clock deadline. Offline rendering is
  slower than real time and would have cut it short.
- **Mute the music bus and remux the exact song.** Region and story triggers in the game switch tracks. Driving
  captions from the video clock keeps them frame-accurate.
- **Auto-centring cameras fight scripted angles.** Turn auto-centring off. Movement then follows camera yaw, and the
  keys are chosen from the angle between the camera and the direction of travel.
- **Story sequences start on their own.** In the first full batch, two videos dropped into a story cinematic (a
  spoiler) once the hero stood near a camp with every friend unlocked, which the fixture had set up. Docking at that
  island also switched the radio track, so the captions changed songs. The adapter now pauses the story node and
  re-asserts the recorded song every frame. Each song's dry run prints a story check.
- **Props without collision block the camera.** Stone arches, giant gumdrops and candy eggs filled the foreground,
  and one shot ended with the camera inside an egg. The physics-ray guard could not see them, so recorder 0.2.0 also
  tests nearby props' bounding boxes.
- **World-space labels are UI.** A floating quest label ("CENTER TRAPDOOR … three riddles") appeared in a canyon
  shot. Recorder 0.2.0 hides `Label3D` nodes with the HUD.
- **Debug fixtures can call save.** Confirm the save function honours a disabled autosave before using them.
- **Empty backgrounds read as a deserted world.** The owner found the videos good but the world deserted: 26 shots
  held Poofy still in front of open sea. Recorder 0.3.0 adds `_stage_ambient("still")` at the start of every held
  shot and optional `"beat"` staging on caption starts, and the tool gained `motion` to flag shots that barely move.
  ShammyVerse built ambient systems to answer the hook (a dolphin escort, passing pods, flocks, a whale, a manta).
- **A sharing limit applies.** The app shares files up to 30 MiB, so the full-quality MP4s needed the preview copy.

## On the GameCore recorder

After extraction, ShammyVerse vendored the base (`tools/game_music_video.py vendor --project game`) and moved
its adapter and the ten shot lists into a script that extends it (about 450 lines, down from the original single
file). Through `tools/game_music_video.py dry-run`, all ten songs finished with no script errors and no camera
CHECKs, with the same shot counts as the original recorder. A throwaway second Godot project (flat ground, a capsule
hero and a follow camera) also passed `vendor`, `dry-run` and a full `record` at 640×400. That run caught and fixed a
base bug: the cut planner had appended to the game's own caption list.

## Status

Dry runs: ten of ten songs finished with no script errors. One camera `CHECK` (24 % blocked) was fixed by moving
the shot. One fixture warning (the ship's wheel refused on later routes) was handled with a logged fallback.
The first full batch, recorded with the original single-file recorder, failed the contact-sheet review: two videos
showed a story cinematic, there were foreground props, and a floating label appeared. Those fixes went into recorder
0.2.0 and the ShammyVerse adapter, and the album was re-recorded through `tools/game_music_video.py record`. Owner
review of the final ten is not yet recorded.
