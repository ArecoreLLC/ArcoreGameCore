# Godot gameplay music-video recorder

`music_video_recorder.gd` (version 0.7.0) is the Godot 4 runtime of the
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
| Framing guard (0.6.0, `frame_guard`, default on) | Keeps the subject unblocked and fully in frame. Every frame it tests lines from the camera to points on the hero (`_subject_points()`: feet, chest, head, both sides) and to any watched subject (`frame_targets`) against colliders **and the real triangles of nearby meshes** (`Mesh.generate_triangle_mesh()`, cached), so batched props without collision count. It also checks the hero is inside the frame and the camera is not under the ground. At each cut it picks the nearest clear view before the first frame is drawn (orbit angle first, then a higher or closer camera). During a shot, if the view stays blocked for 0.15 s, it orbits slowly (`orbit_speed`, 0.55 rad/s) to the nearest clear angle. Offsets are added to the shot's own view through `set_view()` / `view_yaw()`. `frame_guard_shot = false` turns it off for one shot; `MUSIC_VIDEO_FRAME_DEBUG=1` prints what blocks each shot (`MUSIC_VIDEO_BLOCK`). The 0.2.0 swing guard remains for `frame_guard = false` |
| Placement | `ground()`, `at()`, `shore()` (march outward from an island centre to the waterline), `cut_to()` |
| Shots | `stroll`, `run_front`, `jumps`, `takeoff`, `glide`, `low_glide`, `closeup`, `gaze`, `walk` |
| Framing helpers (0.5.0) | `face_yaw(target)` (looks past the hero, swung by `SIDE`, 0.42 rad), `watch_point` (hero stands, camera tracks a moving subject), `hover_watch` (hero hovers beyond a subject over open ground or water), `overview` (slow high look down). Moved here from `asset_showcase.gd` so song shot lists can use them |
| Edit plan | `cut_times()` cuts on caption starts at least `MIN_SHOT` apart and every `MAX_SHOT` in uncaptioned stretches; `play_shots(shots, from, final_shot)` |
| Foreground clearing (0.7.0, `clear_foreground`, default on) | At each cut, after the framing guard picks its view, props nearer than the subject that cover more than `foreground_cover` (12 %) of the frame are hidden for the shot, and every 10 frames anything the moving camera brushes within 6 m is cleared too. Only individual props (under `foreground_max_size`, 25 m) are hidden, never anything holding the subject; all come back at the next cut. `MUSIC_VIDEO_CLEAR` lines name them in frame-debug mode |
| Planned edit (0.6.0) | `play_plan([[start, Callable(until)], …])` plays shots at planned times (each to the next row's start, the last to the song end), so a cue list written against the lyrics maps one row to one shot. Rows whose start has passed are skipped |
| Lyric-matched shots (0.5.0) | Set `lyric_shots` to `[keyword, Callable(until)]` pairs. When a cut's window holds a caption line containing a keyword (starting at least `lyric_shot_lead`, 1.5 s, before the cut ends), that shot plays instead of the next one in the list, once per pair, and the base prints `MUSIC_VIDEO_LYRIC_SHOT`. The song's own list continues where it left off, so lyric shots never skip list shots |
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
| `_camera_position_for(yaw, pitch, distance)`, `_camera_basis_for(yaw, pitch)` | Optional (0.6.0). Where the follow camera would sit and face, so the guard can test a view before showing it. Include the game's own camera-collision pull-in for exact framing. Defaults orbit 1 m above the hero |
| `_subject_points()` | Optional (0.6.0). Points on the hero that must stay visible |
| `_occluder_excluded(node)` | Optional (0.6.0). Geometry the guard ignores: the vehicle the hero rides, ability effects, moving life that is the subject of the shot |
| `_stage_ambient(kind)` | Optional. Put ambient life in front of the camera now (`"still"` or `"beat"`) and return whether anything was staged. Escorts for vehicle shots belong in the game's own vehicle shot |

Movement assumes camera-relative keys with Godot's forward = −Z convention. A game with other controls overrides
`steer()`.

## Asset showcase base

`asset_showcase.gd` (0.3.0) extends the recorder for the [game-asset-showcase workflow](../../../workflows/game-asset-showcase/README.md):
- a shot list (`add(id, label, fn)`) of titled shots, `SHOT` seconds each (6.5)
- a title-card layer that stays visible
- `--only=<letters>` and `--snap=<dir>` user arguments
- `gaze_out` (the other framing helpers come from the recorder base since 0.5.0)

A game implements the recorder adapter plus `_setup_showcase()`, `_build_showcase()` and `_clear_stages()`. Still-shot
staging and the framing guard are off by default, so each hand-framed shot shows only its own subject.

## Validation

`tools/tests/test_game_music_video.py` covers the tool: marker parsing, the shared override, mix and preview
commands, and the vendor lock. The GDScript base is exercised by the consuming game's dry runs. There is no
GameCore-side Godot test project.

## Optional capture lighting

`capture_lighting.gd` is a small engine-specific sampler for ArcoreCut-exported `gamecore.lighting.v1` plans. Load the versioned plan, then call `sample(song_seconds, night_amount)` with the recorder clock. Apply `sunlight` and `ambient` multipliers to saved time-of-day baseline values, never multiply the previous frame’s values. Multiply the original Environment `tonemap_exposure` once by the profile’s `capture_exposure` for a video-only overall look. Keep gameplay defaults unchanged unless explicitly adopting the look.

Scene overrides use exclusive integer frame ranges and rational FPS; blends are deterministic smoothstep transitions from the preceding look at each range boundary. Prefer ranges at least as long as the blend. `preserve_dusk_night` fades scene changes back to neutral over night amount 0–0.55; exposure remains global. This helper does not alter shot clocks, music, shadow algorithms, geometry or camera paths. The game adapter remains responsible for loading the world and applying the sampled values. Plans are metadata, never executable script input.

Engine acceptance: `Godot_console.exe --headless --path <Godot project> --script <absolute path to tests/capture_lighting_test.gd>`. Capture validation must compare original frame counts, exact shot markers and continuous audio; do not infer gameplay equivalence from the sampler test.

Optional `capture_fill.gd` is a single shadow-free SpotLight3D following the active camera. Call `configure(character_roots, unused_layer)` (default layer 20), then set `light_energy` from the sampled `camera_fill` (0–1, neutral 0). Only opted-in character geometry receives the fill; call `release_targets()` while the scene is alive before removing the fill to restore mesh layers (do not mutate renderer layers during tree teardown). The sampler’s dusk/night protection returns fill to zero. Adapters must reserve an unused render layer and keep camera cull masks compatible. The fill adds no shadow algorithm changes and leaves the environment untouched.


## Live lighting studio (Godot 4, 3D)

`lighting_studio.gd` provides the shared Godot UI and acknowledged MCP mailbox. It uses the same
`gamecore.lighting.v1` sampler as recording. ArcoreCut owns saved profiles in SQLite; slider changes
are drafts until **Save lighting to ArcoreCut**. Exposure is global; fill edits the selected default
or existing scene override. The sample frame selects profile timing, **not gameplay simulation time**.
Day/dusk/night is a preview condition; the saved profile retains dusk/night protection.

To integrate another game, start with `examples/lighting_studio/project.godot` and
`examples/lighting_studio/studio_adapter.gd`. This runnable second-game example uses procedural
geometry only. The game adapter is a SceneTree script that loads a safe scene, configures a camera
and optional character-only `capture_fill.gd`, then adds the shared studio and calls:

```gdscript
studio.configure(OS.get_environment("ARCORE_STUDIO_SESSION"), apply_look, set_day, night_amount)
```

The three callbacks are the entire game-facing contract:

- `apply_look(settings: Dictionary, exposure: float)`: apply sunlight, ambient and camera_fill
  to saved original values, plus original Environment tonemap_exposure times exposure. Never
  multiply last frame's values. Run the game's time-of-day system after these baseline updates.
- `set_day(name: String)`: choose `day`, `dusk` or `night` immediately in the game's sky system.
- `night_amount() -> float`: return 0 for day, 0.55 for dusk and 1 for night (continuous values work).

Keep game names, assets, scene setup, poses, camera positioning and save isolation in the adapter.
Reserve an unused mesh layer for character fill. Disable autosave before scene setup. Do not restore
mesh layers during scene teardown. The studio's UI runs while paused; the adapter decides whether
the world should run. No new Godot addon, HTTP server or editor plugin is needed.

Use the GameCore hub `video_production` operation `video_lighting_studio`. First `open` specifies
`project_id`, `godot` executable, `game_project` folder and `adapter` script; the connection is
remembered per production. The native ArcoreCut lighting panel exposes these same connection fields.
`status` returns the actual Godot heartbeat, draft `generation`, profile, dirty flag and effective look.
`update` accepts `exposure` (0.1-2), `camera_fill` (0-1), `scope` (-1 for default, otherwise override
index), sample `frame`, `time_of_day` and `compare` (original game look). `update`, `save` and `reload`
require `expected_generation`. Poll `status` with returned `command_id` until Godot acknowledges it;
queued does not mean applied. `save` also checks loaded lighting version and timeline revision.
`reload` loads the latest SQLite profile and discards draft edits. `screenshot` captures the engine
viewport including studio controls; `close` shuts down only that preview. Media is never modified.

Session plans, commands, heartbeat, screenshots and logs live beneath the production's
`lighting/studio/<session>` folder in GameVideo. Local file IPC keeps slider edits in-process;
only Save invokes the Rust backend. This first implementation targets local desktop Godot 4,
not Godot web exports, remote hosts or arbitrary full-scene timeline scrubbing.
