# Geometry-first art to a song-driven game painting

Use the implemented [animal manifest runner](../../tools/drawing-studio/ANIMAL_PIPELINE.md)
to track and resume consumer adapters with artifact-bound review gates. The
[assisted shapes walkthrough](assisted-shapes.md) specifies vertical mirror-line,
horizontal cross-guide and three-click oval authoring for a future user UI.

This extends the [game music video workflow](README.md) with an authored Drawing
Atelier lesson. Scope: reference illustration → advanced study → timed sand/paint
maps → character brush tracks → clean engine capture → editable ArcoreCut captions.
The game's playable quest and unlock conditions remain consumer-owned.

Personal artwork has a simpler path: `drawing_import_reference` preserves the
source, then `drawing_render` with default `mode: "trace"` skips construction and
draws contours before color. `mode: "advanced"` is optional and requires user/artist
authored shapes. Never block personal-art playback on manual geometry unless the
user chooses Shapes First. The butterfly and red panda authored studies use it.

The existing `wizard.json` remains the video workflow's source of truth. This art
preparation is an MCP/CLI capability, not an additional implemented wizard or Flow
node. Do not claim that an end-to-end generic game adapter exists.

## Responsibilities

| Owner | Responsibilities |
|---|---|
| Artist / agent with review | Original reference and manually placed main/small geometry |
| GameCore Drawing Atelier | Validate lesson, trace contours, advanced graphite/paint study, stock-color recipes and evidence |
| Consumer game | Region names, song windows, reveal-time maps, brushes, camera, movement and quest rewards |
| GameCore recorder | Deterministic clock, capture and completion/camera diagnostics |
| ArcoreCut | Immutable imports, frame-timed editable captions, continuous soundtrack and export validation |

## Practical sequence

1. Preserve the reference in the consumer project with provenance. Use a clear
   silhouette and an uncluttered background. Reference generation is a separate tool.
2. Author **stage 0 main masses/axes** and **stage 1 smaller shapes**. Inspect them
   alone and over the picture. Match their coordinates to the 1280 × 698 letterboxed
   lesson canvas. Geometric validity does not establish correct anatomical placement.
3. Discover `drawing_production` → `tools/list`; use `drawing_guide`,
   `drawing_validate`, `drawing_render`, then poll `drawing_job`. Review the sheet
   and GIF. Advanced mode finishes each region's graphite and paint before the next.
4. In the game adapter, reuse `export-strokes.mjs` with that same lesson. It exports
   stages, guides and instructions on the 1280 × 698 display canvas. Converting to
   its 640 × 349 analysis canvas requires dividing stroke coordinates/widths by two.
5. Assign region strokes to explicit windows of the exact song. Preserve both main
   and small construction phases before detailed outlines; lighten guides before
   color. Encode reveal times without lossy compression. Record artwork ID, dimensions,
   song duration, source hash, windows and position tracks in metadata.
6. Drive brush/stick positions from those timed strokes. Avoid averaging distant
   strokes into a point on empty canvas. Check ordering, bounds and pauses. Keep
   previous artwork selectable; use separate output folders rather than replacing it.
7. Rehearse headless, then record clean engine footage with save writes disabled.
   Validate completion, scripts and camera checks; inspect actual geometric, sketch,
   brush-contact and finished frames. Technical completion is not visual approval.
8. Import the finished mix through `video_production` into ArcoreCut. Put lyrics and
   stage explanations in **nonoverlapping exclusive-end integer frame intervals**.
   Use lower safe-area captions and instrumental gaps. Export captions without
   remixing the already-finished audio. Confirm frame count, presentation timing
   and continuous audio equality in the editor's evidence.

## Efficient iteration

- Fingerprint the lesson, renderer/exporter code, runtimes and settings. Cache only
  when every required output still matches its stored hash. Preserve failed runs.
- Geometry/reference edits invalidate the study. Song-window edits invalidate the
  game's timing maps/tracks. Camera edits require a new engine capture. Caption
  placement/text edits require only ArcoreCut export. Keep those boundaries separate.
- Review a teaching sheet and short construction/brush samples before full capture.
- Return absolute artifact paths, a persistent job handle, status and logs through
  MCP. Avoid long synchronous tool calls or treating a launch receipt as success.
- Keep hand-authored geometry review explicit even when automatic tracing improves.

## Consumer evidence

The first two consumer studies are a butterfly and a red panda sand painting on
Canvas Cay. Their private drawings, cue maps and game scripts stay in ShammyVerse.
The red panda reuses the same construction-first contract and an independent
artwork directory; its clean recording is edited in ArcoreCut. This demonstrates
a second artwork in one game, not portability to a second game or engine.

Read [MCP quickstart](../../tools/drawing-studio/MCP.md) for exact calls and boundaries;
[Drawing Atelier](../../tools/drawing-studio/README.md) for renderer behavior;
[video example](example.md) for capture commands. A future in-game reward should
use the song clock while leaving movement available; a directed film does not
establish that interaction requirement.
