# Godot gameplay music-video recorder

`music_video_recorder.gd` (version 0.4.0) is the Godot 4 runtime of the
[game-music-video workflow](../../../workflows/game-music-video/README.md). It is a `SceneTree` script. A game
extends it with an adapter and its shot lists, then runs it with `--fixed-fps 30`. Add `--write-movie` to record.

Install it with `python tools/game_music_video.py vendor --project <game project>`, which copies it and
`asset_showcase.gd` to `addons/gamecore_music_video/` with a SHA-256 lock per file. Don't edit the vendored copy.

## What the base provides

| Area | Members |
|---|---|
| Video clock | `t()` counts frames since `start_song()`, never wall-clock time, so slow offline rendering cannot drift |
| Markers | `MUSIC_VIDEO_SONG_START frame=… length=…`, `MUSIC_VIDEO_SHOT i a-b blocked=n%[ CHECK]`, `MUSIC_VIDEO_END`, parsed by the tool |
| Input | `key()`, `tap()`, `release()`, `stop_moving()`; bindings in `KEY_FORWARD` … `KEY_FLY` (default WASD, Shift, Space, Ctrl, Q, E) |
| Steering | `camera(theta, pitch, distance)` sets the angle relative to travel; `steer()`, `travel()`, `fly()`, `hold_camera()` |
| Camera guard | Every frame, a physics ray and a bounding-box test against nearby props (within `prop_radius`, 25 m; many props have no collision), including a camera that ends up inside a prop. If blocked for more than 0.25 s the camera swings around, reversing after 2.5 s |
| Placement | `ground()`, `at()`, `shore()` (march outward from an island centre to the waterline), `cut_to()` |
| Shots | `stroll`, `run_front`, `jumps`, `takeoff`, `glide`, `low_glide`, `closeup`, `gaze`, `walk` |
| Edit plan | `cut_times()` cuts on caption starts at least `MIN_SHOT` apart and every `MAX_SHOT` in uncaptioned stretches; `play_shots(shots, from, final_shot)` |
| Ambient staging | Every held shot (`closeup`, `gaze`, any `hold_camera`) calls `_stage_ambient("still")` once, so an empty background gets something passing through it (`stage_still`, default on). With `stage_beats` = N, every Nth caption start calls `_stage_ambient("beat")`. Both print `MUSIC_VIDEO_STAGE` |
| Lyric staging | Set `lyric_stage` (lowercase keyword → kind). When a caption whose text contains a keyword starts, the base calls `_stage_ambient("lyric:"+kind)`, at most once every `lyric_spacing` seconds (3 s), and prints `MUSIC_VIDEO_STAGE lyric` |
| Beat clock | `_beat_clock(t)` is called every frame with the video time, so beat-synced systems (dances, drums) follow the song, not the game's muted player |
| HUD | `hide_hud()` hides every `CanvasLayer` except those `_keep_layer()` accepts, and keeps them hidden each frame. With `hide_world_labels` (default on) it also hides `Label3D` quest and debug markers |

## Adapter to implement

| Method | Contract |
|---|---|
| `_load_world()` | Instantiate the game, **disable saving**, mute the music bus, hide developer overlays, and **pause story sequences that start on their own** |
| `_produce(id)` | Per-song fixture, `start_song(id)`, `hide_hud()`, `play_shots(...)` |
| `_hero()`, `_camera()` | The controlled character and its gameplay camera |
| `_view_yaw()`, `_set_view(yaw, pitch, distance, snap)` | Read and drive the follow camera; ease pitch and distance unless `snap` |
| `_set_movement_yaw(yaw)` | For controllers that latch the movement frame while keys are held (otherwise leave empty) |
| `_set_flying(on)`, `_is_flying()` | Flight or other airborne mode, if the game has one |
| `_height_at(x, z)` | Terrain or ground height used for placement |
| `_teleport(position, facing_yaw, flying)` | Move the hero, face it, reset velocity and physics interpolation |
| `_end_activity()` | Leave swings, vehicles and menus before a cut |
| `_prepare_song(id)` | Load captions, stop the game's own player, return the song length |
| `_caption_starts()`, `_update_captions(t)` | Caption start times, and show the caption for video time `t`. Re-assert the recorded song every frame if game triggers switch tracks |
| `_keep_layer(layer)` | `true` for the caption layer(s) |
| `_caption_text(index)` | Optional. The text of caption `index` (same order as `_caption_starts()`), for lyric staging |
| `_beat_clock(t)` | Optional. Drive the game's beat clock from the video time (for example the world-life kit's `KIT.song_clock(id, t)`) |
| `_stage_ambient(kind)` | Optional. Put ambient life in front of the camera now (`"still"` or `"beat"`) and return whether anything was staged. Escorts for vehicle shots belong in the game's own vehicle shot |

Movement assumes camera-relative keys with Godot's forward = −Z convention. A game with other controls overrides
`steer()`.

## Asset showcase base

`asset_showcase.gd` (0.1.0) extends the recorder for the [game-asset-showcase workflow](../../../workflows/game-asset-showcase/README.md):
- a shot list (`add(id, label, fn)`) of titled shots, `SHOT` seconds each (6.5)
- a title-card layer that stays visible
- `--only=<letters>` and `--snap=<dir>` user arguments
- framing helpers: `face_yaw`, `watch_point`, `hover_watch`, `overview`, `gaze_out`

A game implements the recorder adapter plus `_setup_showcase()`, `_build_showcase()` and `_clear_stages()`. Still-shot
staging is off by default, so each shot shows only its own subject.

## Validation

`tools/tests/test_game_music_video.py` covers the tool: marker parsing, the shared override, mix and preview
commands, and the vendor lock. The GDScript base is exercised by the consuming game's dry runs. There is no
GameCore-side Godot test project.
