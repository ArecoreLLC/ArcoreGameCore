# Showcase new game assets and effects

Make a reviewable record of every new asset or effect in a game: one titled shot of about 6.5 seconds each. It
comes as screenshots while you build, and as a demo video over the game's music when the batch is done. The same
shot list serves both, so the screenshots the team reviews are the shots the video shows.

It runs on the [music-video recorder](../../3d/godot/music_video/README.md) and its showcase base
(`asset_showcase.gd`), driven by [`tools/game_music_video.py`](../../tools/game_music_video.py). It was derived from
the ShammyVerse world-life demo (see [example](example.md)).

## Ownership

| Owner | Responsibility |
|---|---|
| GameCore | This workflow, `asset_showcase.gd` (shot list, title cards, `--only`/`--snap`, framing helpers) and the `showcase` and `record` commands |
| The game | Its recorder adapter, the showcase fixture and one shot per asset (`add(id, label, fn)`) |
| Requester | Which assets to show and the final review |

## Pipeline

| # | Stage | Done when |
|---|---|---|
| 1 | Vendor | `tools/game_music_video.py vendor --project <game>` installs the recorder and `asset_showcase.gd` with a lock |
| 2 | Script | The game's showcase script extends `asset_showcase.gd`: the recorder adapter, `_setup_showcase()` (fixtures, saving off), `_build_showcase()` (one `add()` per asset, ids grouped by letter), `_clear_stages()` |
| 3 | Screenshots | `showcase --only <letters>` runs windowed at a fixed 30 fps without a movie, saves a PNG at 58 % of each shot, and tiles sheets of eight. Review them while building and fix the framing |
| 4 | Soundtrack | Join songs with short crossfades to cover the shots (6.5 s × shots), then trim with a fade. The script's `_beat_clock()` (or the adapter) maps video time to the song that is playing |
| 5 | Record | `record --song <id> --audio <soundtrack>` captures with Movie Maker, mixes, encodes, and writes a preview under 28 MB and a contact sheet |
| 6 | Review | Check frames from each shot's middle; list shots whose asset reads faintly, then reframe or accept them |

## Framing helpers (recorder base since 0.5.0; `gaze_out` in `asset_showcase.gd`)

| Helper | Use |
|---|---|
| `face_yaw(target)` | Looks past the hero toward the subject, swung by `SIDE` (0.42 rad) so the hero frames the subject instead of hiding it |
| `watch_point(spot, target_fn, until, pitch, distance)` | The hero stands at a spot; the camera tracks a moving subject |
| `hover_watch(home, center, target_fn, until, back, lift, pitch)` | The hero hovers beyond a subject over open water or terrain: no props between camera and subject |
| `overview(spot, target, until, pitch, distance)` | A slow high look straight down (shoreline foam, cloud shadows) |
| `gaze_out(island, angle, until, stage)` | The hero faces out to sea while an event is staged in view |

## Rules from the first showcase

- **Put the camera before the cut.** Call `camera(theta, …)` before `cut_to()`, or the hero turns their back to a
  close-up.
- **Never line the subject up behind the hero.** Use `face_yaw` (the `SIDE` swing).
- **Stage transient events at the shot start** (a whale, a dive, a salute) so they happen inside the 6.5 s.
- **Hover rather than stand** when props crowd a shore; stand back from crowded interiors.
- **Clear forced states after every shot** (weather, wind, night), and only show talk bubbles in the shot that needs
  them.
- **Turn off still-shot staging** (`stage_still = false`, the base default) so each shot shows only its own subject.

## Known limits

- Snap times are fixed at 58 % of the shot, so a brief event can fall outside the screenshot even when the video
  shows it.
- The tool tiles sheets of eight shots.
