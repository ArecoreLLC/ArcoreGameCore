# Drawing Atelier through GameCore MCP

For one animal manifest and resumable stages, discover `animal_guide`,
`animal_validate`, `animal_status`, `animal_resume` and `animal_review` on the same
`drawing_production` tool. Read [Animal pipeline v1](ANIMAL_PIPELINE.md) for the
manifest contract, artifact hashes, manual review gates and CLI commands.

Register **only the GameCore hub**, `hub/src-tauri/target/debug/gamecore-library.exe --mcp`.
The first-party `drawing_production` tool owns drawing preparation. **Draw & Paint**
(`mode: "trace"`, the default) starts with contours and paint, with no geometry needed.
**Shapes First** (`mode: "advanced"`) uses manually authored construction guides. Use
`video_production` for ArcoreCut editing; no second agent-facing server is needed.
After updating hub source, build it with `cargo build --manifest-path hub/src-tauri/Cargo.toml`
and reconnect your MCP client to refresh tool discovery. Set `GAMECORE_ROOT` if using
a relocated binary, and `GAMECORE_PYTHON` if Python is not named `python` on PATH.

## Start here

Call `drawing_production` with:

```json
{"operation":"tools/list","arguments":{}}
```

Then call `drawing_guide` with empty arguments. It returns the lesson contract,
local documentation paths, dependencies, outputs and boundaries. Every operation
has a typed schema with descriptions, required fields and bounded render settings.
Errors are MCP `isError` results with an actionable message.

| Operation | Input | Result |
|---|---|---|
| `drawing_guide` | none | Geometry-first order and contracts |
| `drawing_import_reference` | absolute `source`, `output_dir` | Original copy, fitted reference, coordinate mapping, editable lesson |
| `drawing_validate` | absolute `lesson` path, optional `mode` | Validation, stage counts, source hash; no writes |
| `drawing_render` | `lesson`, `output_dir`; optional mode/width/fps/duration/force | Persistent `job_file` immediately |
| `drawing_job` | returned `job_file` | Status, output paths, hashes and error/log information |

Example (replace local paths with your own):

```json
{"operation":"drawing_validate","arguments":{"lesson":"X:/MyGame/art/animal-lesson.json","mode":"advanced"}}
```

```json
{"operation":"drawing_render","arguments":{"lesson":"X:/MyGame/art/animal-lesson.json","output_dir":"X:/MyGame/art/reviews","mode":"advanced","width":800,"fps":8,"duration":48}}
```

Poll `drawing_job` using the exact returned `job_file` until `passed` or `failed`.
`interrupted` means the worker exited without finishing; call render again to retry
in a fresh job directory. Do not mistake a queued job for a completed render.
Jobs survive closing the MCP connection. Rendering has a ten-minute timeout.

Outputs: `study.gif`, `sheet.png` and `study.evidence.json`. Shapes First also produces
`study-palette.json` and `study-palette.png`. Each receipt records input/code/runtime fingerprints and
output SHA-256 hashes. Matching successful requests reuse verified outputs;
`force: true` creates a fresh run. A changed reference, lesson, tool source, setting,
Python/Pillow/Node version, missing output or altered output prevents reuse.
The input lesson is copied into the unique job directory before work starts.
Old outputs are preserved. Human visual review is separate from technical success.

## Geometry is authored, not guessed

The advanced lesson is JSON version 1 with a `name`, embedded PNG/JPEG/WebP
`image` data URL, and `guides`. Place guides on the **1280 × 698 display canvas**,
including the reference image's letterboxing. Each guide has `type` (`ellipse`,
`line`, `contour`), `stage`, optional `name` and sampled `[x,y]` `points`.

- Stage 0: large head/body masses, tail gesture and proportion axes.
- Stage 1: smaller ears, muzzle, eyes, feet and other construction forms.
- Stage 2: optional authored detailed contours. Automatic tracing supplies further contours.

An ellipse is a sampled closed curve, not a bounding-box declaration. The advanced
renderer uses construction ellipses as paint regions; line guides establish axes
and gestures but do not define closed paint regions. Author a body-part hierarchy
and review an overlay before rendering. Do not substitute generic starter ovals
for a reviewed custom lesson. Shapes First requires both stages 0 and 1 and at least
one construction ellipse; Draw & Paint accepts empty guides and skips both stages
without a blank construction lead-in. It reuses `core.mjs.validateLesson` and checks the actual
canvas height; it cannot verify whether a circle correctly matches an animal's eye.

This service does **not** generate reference illustrations, infer anatomy, write
a game's song timings, rig a character, create a playable quest or publish media.
Use the image tool or supplied artwork for the reference. Keep private game art
in the consumer repository, never in GameCore.

## Personal artwork: no shape-authoring requirement

Call `drawing_import_reference` with a local `source` PNG/JPEG/WebP and an absolute
`output_dir`. It copies the original byte-for-byte, fits an EXIF-oriented reference
onto a white 1280 × 698 canvas without cropping, and returns a `starter-lesson.json`
with empty guides. Pass that returned lesson to `drawing_render` with `mode: "trace"`.
Poofy's consumer can then use traced outlines and paint strokes directly. This is
the simple path for personal artwork, not automatic anatomical understanding.

For Shapes First, users or artists may add their own ellipses and guide lines in the
existing Drawing Atelier browser editor, save the lesson and select `advanced`.
The import tool never overwrites an edited starter lesson on repeat import. Originals
are content-addressed and checksum-verified. No external upload, perspective
correction, background removal or in-game upload screen is implemented by this tool.

## Song and editor handoff

See [Drawing to song workflow](../../workflows/game-music-video/drawing.md).
Use the exact song's audio clock and a game-owned adapter. Export a clean picture
without permanent lyric/instruction overlays. Import the finished soundtrack as
`audio_mode: mixed` through ArcoreCut; never add that same song again as stems.
Keep lyrics and instructional notes in nonoverlapping frame intervals. ArcoreCut's
caption lane currently accepts one active cue at a time. Place lyrics low in the
safe area; use instrumental gaps for context notes. Caption-only changes then need
only an editor export, not another engine capture.

## CLI fallback and checks

`production.py` accepts a single JSON object with `operation` and `arguments` on
stdin and returns `{ok,result}` or `{ok:false,error}`. This is the same dispatcher
used by the hub, useful for diagnosis, not a separate required MCP registration.

```powershell
python -m unittest discover -s tools/drawing-studio -p test_production.py -v
cargo test --manifest-path hub/src-tauri/Cargo.toml
```

Dependencies: Python 3, Pillow and Node. The standard/advanced drawing stages need
no browser, GPU, model weights, credentials or network. Optional vision tools are
separate experiments and do not replace authored construction lessons.
