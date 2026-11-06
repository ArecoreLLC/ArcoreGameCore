# Drawing Atelier work packet and evidence

Date: 2026-11-02. Platform: Windows, local browser application. Source baseline: repository `cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc`, plus pre-existing working-tree changes belonging to other work. Target: uncommitted files under `tools/drawing-studio/`; no engine runtime edits. Workflow selected for repository orientation: `phaser-to-godot`, dimension `2d`; its guide, example, dimension catalog and shared migration contract were read. This is a new independent tool, not a Phaser/Godot migration.

Versions: Node v24.11.0; Python 3.14.0; browser version not available because local browser access is disabled in Work settings. No third-party runtime libraries. No prior drawing-tool behavior or performance baseline exists. Scope: one spider study plus local-reference authoring, six-stage playback, PNG frame and instructional-sheet exports, and editable JSON lessons. Input: supplied 1280 × 698 JPEG; asset rights are not established beyond the user supplying it for this task.

## Executed checks

| Status | Command / procedure | Evidence |
| --- | --- | --- |
| passed | `node --test tools/drawing-studio/core.test.mjs` | 7 tests: stage boundaries, guide geometry, edge extraction, foreground stroke generation, blank-image behavior, lesson roundtrip/rejection, deterministic randomness. Initial sandbox run blocked child-process spawning; approved rerun passed. |
| passed | `node --check tools/drawing-studio/app.mjs` and `node --check tools/drawing-studio/core.mjs` | Exit 0 for both modules. |
| passed | `python tools/validate_workflows.py` | Final result: `{"status":"passed","errors":[]}`. Fixed the initially missing validation record and a Windows code-page issue in that record before the successful run. |
| passed | `python -m unittest discover -s tools/tests -v` | Final approved run: all 19 tests passed. Initial sandbox run could not access temporary fixtures; intermediate runs exposed the missing record and its Windows code-page issue, both corrected. |
| blocked | Open local browser with `cua.createBrowserTab('iab', 'about:blank', {visible:true})` | Tool returned "Local browser use is disabled in Work settings." No browser build, visual playback, download or pointer check is claimed. |

## Browser acceptance remaining

Start with `python -m http.server 8765 --bind 127.0.0.1 --directory tools/drawing-studio`, then open `http://127.0.0.1:8765`.

1. First Play starts from blank paper and draws the two body masses before axes and eye/leg shapes. Every later stage accumulates distinct pencil or paint strokes. Scrub backwards, restart, change speed and loop without stale marks. Status: **not_run**.
2. Compare all six steps against the reference; assess contour quality, fur, eye highlights, pencil feel and paint realism. Automated image-processing tests do not establish artistic quality. Status: **not_run**.
3. Toggle guidelines after construction; compare reference, then return to the drawing. Export frame and sheet: inspect resolution, six distinct stages, text layout and absence of drawing cursor/reference overlay. Status: **not_run**.
4. Load a portrait and a landscape image, add ellipse/axis/contour guides, undo and reset, save/reopen JSON. Verify input image proportions and guide alignment. Check corrupt and oversized input feedback. Status: **not_run**.
5. Check mouse, keyboard and touch at desktop and 390px widths in named browsers/devices, and record frame times on named hardware. Status: **not_run**.

No game build or playtest was applicable or run. No completed-port claim, performance parity claim, or measured token/time savings is made.

## CLI GIF export, 2026-11-02

Scope extended to headless Python/Pillow rendering, using `export-strokes.mjs` to reuse the shared geometry and stroke analysis. Source baseline remains `cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc` plus uncommitted drawing-tool changes. Versions: Python 3.14.0, Pillow 12.1.0, Node v24.11.0. No engine migration or browser access needed. The reference ownership limitations above continue to apply.

Acceptance: render the supplied image from blank paper through all six stages, loop the GIF, retain a final hold, decode every saved frame, and produce a readable six-step PNG. Also check custom-reference fit, output timing, and invalid settings.

- **passed**: `python tools/drawing-studio/render_gif.py --output tools/drawing-studio/output/spider-study.gif --sheet tools/drawing-studio/output/spider-study-sheet.png`. Final export decoded successfully: 960 x 600, 289 frames, 26,000 ms including final hold, infinite loop, 21,010,156 bytes. Rendering and verification took 15.15 seconds on this Windows host; hardware was not profiled. SHA-256: `51a7ce1b1cf65547cec07a8aa0c31bd4642d236a23e7da30b2b34df6b820357d`. Initial sandbox temporary-directory access was denied; approved execution succeeded. An intermediate timing drift was corrected before the final render.
- **passed**: final 1800 x 2240 teaching sheet visually inspected using the local image viewer. Six distinct stages, readable captions/instructions, graphite values, and a final painted approximation are present. This is static frame inspection, not a real-time playback review.
- **passed**: `python -m unittest discover -s tools/drawing-studio -p test_render_gif.py -v`. Three tests cover aspect-ratio fit, a real end-to-end export with decoded loop/duration/frame differences and PNG output, and early rejection of invalid settings.
- **passed**: `node --check tools/drawing-studio/export-strokes.mjs`.
- **not_run**: real-time playback in a GIF player; no browser UI claim is made. Browser acceptance items above remain separate.

Artifacts: ignored `output/spider-study.gif`, `output/spider-study-sheet.png`, and `output/spider-study.evidence.json` within this directory. The evidence JSON includes the exact output checksum and decoded properties. No comparable previous CLI runtime existed; no efficiency improvement or token savings is claimed.

## Advanced region painting and mixture lesson, 2026-11-02

Baseline: the working CLI exporter above, on repository `cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc` plus the uncommitted files in this tool directory. Platform and versions remain Windows, Python 3.14.0, Pillow 12.1.0, and Node v24.11.0. New implementation: `advanced.py`, CLI options and renderer clipping in `render_gif.py`, construction-guide metadata in `export-strokes.mjs`, and `test_advanced.py`. Browser code and legacy engine implementations were not changed. Scope: shape-based paint ordering, six digital stocks, whole-part mixture ratios, palette JSON/PNG, and an optional separate mixing GIF. Real pigment calibration is outside this scope.

Acceptance: preserve standard export, map paint strokes to construction regions, finish each region before the next, clip brush footprints at region boundaries, generate six stocks, use nonnegative whole-part recipes totaling 100, show target/result differences, and support both combined and mixing-only CLI outputs.

- **passed**: `python tools/drawing-studio/render_gif.py --advanced --width 640 --fps 6 --duration 36 --output tools/drawing-studio/output/spider-advanced.gif --mixing-output tools/drawing-studio/output/spider-color-mixing.gif --sheet tools/drawing-studio/output/spider-advanced-sheet.png`. Final run completed in 8.85 seconds, including analysis, both animations, sheet, and decode verification. Advanced GIF: 640 x 461, 222 decoded frames, 38,000 ms, infinite loop, 9,958,711 bytes; SHA-256 `eb419d429a4b2a612b8fb5a59977f71ac098c2804fb1dc2700db6978cf4b2469`. Mixing GIF: 640 x 433, 120 decoded frames, 29,600 ms, infinite loop, eight representative recipes; SHA-256 `88fc15e311921736ec0a76ad87efe74271be9a31c1dde55309cfdec29228c9a9`.
- **passed**: generated palette has six stocks, 200 recipes and 15 painted regions; weighted mean per-channel RGB RMSE 2.58 / 255. The per-recipe target, result and error are retained in JSON. All advanced paint operations use calculated mixture colors. This is a digital approximation metric, not a perceptual or physical-pigment accuracy claim.
- **passed**: `python -m unittest discover -s tools/drawing-studio -p test_advanced.py -v` (4 tests). Covers known optical-density mixtures and recovery of base stocks, whole-part recipe normalization, monotone equal-time region scheduling, brush footprint clipping, decoded advanced export and separate mixing-only export.
- **passed**: `python -m unittest discover -s tools/drawing-studio -p test_render_gif.py -v` (3 tests) and `node --test tools/drawing-studio/core.test.mjs` (7 tests), covering standard CLI and shared-engine regression behavior.
- **passed**: `node --check tools/drawing-studio/export-strokes.mjs` and `python tools/validate_workflows.py`.
- **passed**: static visual inspection of the final six-step advanced sheet and palette chart, plus a mixing-animation frame. Construction, contour and graphite stages are distinct; a partly painted frame retains gray unfinished regions; the completed frame is painted. A first sheet timing/caption mismatch was corrected before the final export. A first recipe preview that overrepresented brown tones was changed to choose more diverse target colors.
- **passed**: uploaded the advanced GIF, mixing GIF, palette PNG and all-recipe JSON to the existing private ChatGPT Page, then read it back to verify the saved references and descriptions. Original animation retained. Page: `https://chatgpt.com/space/page_6ab0d9b077808191a6a1f148d32ef570`. Cloud upload byte hashes matched local output hashes.
- **not_run**: real-time playback in a GIF player and rendered online Page inspection; browser access remains unavailable. Physical pigment mixture matching was not tested or claimed. No engine build or game playtest applies.

The simplified model, whole-part rounding and approximation limits are documented beside the palette and in the README. Current custom-region limit is 64 ellipses. Runtime is a single observed run on the current host, not a comparative performance benchmark; agent token totals are not available from this session's tools.
