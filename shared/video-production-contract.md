# ArcoreCut production handoff

ArcoreCut is the sibling Rust/Tauri application at `X:/Projects/ArcoreCut`. It owns
the video production UI, SQLite metadata and lossless split/reassembly validation.
GameCore owns the engine recorder and reusable workflow implementations. Media is
stored under `X:/Projects/GameVideo`, outside both source repositories.

## Ownership and invariants

- Keep the continuous capture immutable. Preserve separate continuous music and
  capture-effects sources; picture cuts do not split audio.
- Store integer, zero-based frame ranges with exclusive ends and rational FPS.
  No gaps, overlaps, zero-length shots or implicit timeline ripple are permitted.
- Splits use lossless FFV1 picture, not keyframe-only H.264 packet cuts. Validate
  decoded frame order and hashes; timestamp error is bounded by the intermediate
  container's millisecond precision, never a whole frame of tolerance.
- Preserve the exact game song file. A finished mixed MP4 must not receive the song
  again. Replacing picture keeps the continuous sound unless explicitly edited.
- Working outputs are revisioned. Store source hashes, commands, tool versions,
  project revision and validation evidence with each run. SQLite is authoritative;
  JSON alongside media is a frozen audit snapshot.

## Recorder markers

The existing human-readable `MUSIC_VIDEO_SHOT` marker remains compatible. Recorder
0.7.1 additionally emits:

```text
MUSIC_VIDEO_SHOT_FRAMES 0 0 558
MUSIC_VIDEO_SHOT_FRAMES 1 558 1014
```

Values after the shot index are actual process-frame boundaries relative to
`song_frame`. A raw Movie Maker capture includes setup frames; add its recorded
`MUSIC_VIDEO_SONG_START frame` as an explicit import offset. A song-trimmed output
uses offset zero. Older one-decimal-second markers cannot establish exact frames.
ArcoreCut rejects them for exact import rather than guessing.

## Workflow catalog

ArcoreCut reads `workflows/index.json` and the referenced `wizard.json` (or guide).
It caches metadata and source hashes in SQLite. Wizard stages are never duplicated
in app code. Beat-synced dancers and drum taps are cataloged through
[beat-synced-dance](../workflows/beat-synced-dance/README.md); runtime code remains in
[world-life](../3d/godot/world_life/README.md). Changing a displayed beat ruler does
not change baked animation; that requires a new engine capture at the same absolute
song clock and reviewed state setup.

## MCP and PhotoMaster

Only the GameCore hub is registered by ecosystem agents. Its `video_production`
tool routes through the `arcore-cut` entry in `shared/ecosystem.json`. Use
`operation=tools/list` to discover typed provider schemas. Long operations return
persistent job IDs; poll `video_jobs` and inspect evidence. UI and MCP share the
same Rust service and SQLite revision checks.

The `photo-master` registry entry inventories the sibling PhotoMaster's existing
stdio MCP for image adjustments, crop/resize and texture-set export. It can prepare
reference images, thumbnails, ground/bark samples and foliage cards. Source edits
are non-destructive. Normal/height maps are brightness-derived approximations,
roughness is a chosen constant, and lighting remains in base color. Its material
manifest records color spaces and OpenGL/DirectX normal convention. Engine import,
physical material validation and persistent PhotoMaster session routing are not
implemented by this handoff; no finished PBR-material claim is made.
