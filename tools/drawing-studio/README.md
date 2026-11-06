# Drawing Atelier

A local, dependency-free drawing and painting simulator. The supplied spider study starts with hand-placed head/body masses, face axes, eye circles and leg segments. A textured pencil pass follows structural contours extracted from the reference; hatching builds the values, then broad and fine color-sampled brush strokes paint the subject. This is a reference-driven simulation, not a recording of a human artist or a generative art model.

## CLI and animated GIF export

Requires Python with Pillow and Node.js. The verified environment uses Python 3.14.0, Pillow 12.1.0 and Node v24.11.0. If Pillow is missing, install it with `python -m pip install Pillow==12.1.0`. No browser or server is needed for this route.

Run the supplied spider study from the repository root:

```powershell
python tools/drawing-studio/render_gif.py --output tools/drawing-studio/output/spider-study.gif --sheet tools/drawing-studio/output/spider-study-sheet.png
```

Default export: a looping 960-pixel-wide GIF, 24 seconds of drawing at 12 fps, then a 2-second hold. The frame includes a stage caption and progress indicator. The optional `--sheet` writes a six-step PNG teaching sheet. An adjacent `.evidence.json` records dimensions, decoded frame count, duration, loop setting, checksum, runtime and stroke counts. Generated files live in ignored `output/`.

Other examples:

```powershell
python tools/drawing-studio/render_gif.py --input path/to/reference.png --output tools/drawing-studio/output/custom.gif --width 640 --duration 18 --fps 10
python tools/drawing-studio/render_gif.py --lesson path/to/drawing-atelier-lesson.json --output tools/drawing-studio/output/lesson.gif --no-cursor
python tools/drawing-studio/render_gif.py --help
python -m unittest discover -s tools/drawing-studio -p test_render_gif.py -v
```

Use the browser editor below to author custom construction guides, then pass its saved lesson to `--lesson`. An arbitrary `--input` uses generic starter guides. The CLI reuses the existing JavaScript stroke engine through a small Node bridge. Its raster renderer thins structural edges and adds sampled graphite tone strokes before hatching. Pillow rasterization differs from Canvas 2D, so exports are not pixel-identical to browser playback. A shared GIF palette reduces color flicker. Rendering is offline and deterministic within the recorded tool versions. GIF limits color to 256 palette entries; large exports can be sizable. The CLI caps its estimated retained frame data at 450 MB.

## Advanced CLI mode and color mixing

```powershell
python tools/drawing-studio/render_gif.py --advanced --width 640 --fps 6 --duration 36 --output tools/drawing-studio/output/spider-advanced.gif --mixing-output tools/drawing-studio/output/spider-color-mixing.gif --sheet tools/drawing-studio/output/spider-advanced-sheet.png
```

Advanced mode follows the construction ellipses, finishing the base coat and smaller strokes of each part before moving to the next. The supplied spider groups its 32 ellipses into body, head, eye and jointed-leg regions, plus ground/uncovered areas: 15 painted regions. Each brush footprint is clipped to its exclusive region so adjacent regions remain graphite until their turn. Each region gets equal painting time; 40% of the movie is construction/graphite and 60% is painting. The current foreground/background mask is still derived from the reference. Regions are approximate construction geometry rather than automatic anatomical segmentation.

Custom images use the generic oval unless you supply a saved `--lesson` with authored ellipses. Custom ellipses become numbered paint regions. Advanced mode supports up to 64 construction ellipses, with smaller shapes reserving areas inside larger shapes. Custom contour strokes remain in the drawing but do not define closed paint regions.

The exporter generates six digital stock colors, including a light stock, a dark stock and four chromatically diverse colors from the reference candidates and fallback stock colors. It groups sampled colors into small RGB bins, then calculates a nonnegative recipe of at most four stocks for every required bin. Advanced paint strokes use the calculated mixture colors. Each recipe contains integer quantities totaling **100 equal stock parts**, its target RGB, resulting RGB, and per-channel RGB approximation error. Parts link back to the guide indices used in the sketch and the recipes used to paint them.

The deliberately simplified digital model is `mixed channel = exp(sum(weight * log(base channel)))` on positive normalized RGB channels. The solver searches mixtures of one to four stocks in this optical-density coordinate space, then rounds to whole parts. These ratios are for the simulated stock colors. They are **not calibrated physical pigment recipes**; real pigments, binders, brands, opacity and substrate change the result. Target/mixed swatches and RGB errors expose approximation limits.

Advanced exports also write `OUTPUT-palette.json` (all recipes, guide indices and paint order) and `OUTPUT-palette.png` (six stocks and representative recipes). Set `--palette-output path.json` to choose their location. The palette chart shows 12 diverse recipes; the separate mixing GIF demonstrates eight, rather than animating every recipe.

`--mixing-output path.gif` is optional and separate from the drawing output. It shows ratio-sized paint portions, folding/blending, target/result comparison, and which object parts use the mixture. To generate only this lesson and its palette:

```powershell
python tools/drawing-studio/render_gif.py --mixing-only --mixing-output tools/drawing-studio/output/color-mixing.gif --width 640 --fps 6
```

`--mixing-output` without `--advanced` leaves the main drawing in standard mode. The browser interface continues to use its existing drawing sequence; these new advanced and mixing options are CLI features.

## Optional local vision test

`analyze_reference.py` runs SmolVLM on image pixels with four fixed, subject-neutral questions: subject description, composition, visible parts, and basic sketch shapes. It does not import drawing guides or pass the image filename to the model. Answers are saved verbatim with prompts, the exact checkpoint revision, input hash, versions and timing. This is a separate experiment; it does not replace the authored lesson or generate paint-region coordinates.

Create an isolated Python 3.11 environment on Windows:

```powershell
py -3.11 -m venv tools/drawing-studio/.venv-vision
tools/drawing-studio/.venv-vision/Scripts/python.exe -m pip install --upgrade pip
tools/drawing-studio/.venv-vision/Scripts/python.exe -m pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple
tools/drawing-studio/.venv-vision/Scripts/python.exe -m pip install -r tools/drawing-studio/requirements-vision.txt
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/analyze_reference.py --output tools/drawing-studio/output/spider-vision-smolvlm500.json
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/analyze_reference.py --model HuggingFaceTB/SmolVLM-256M-Instruct --output tools/drawing-studio/output/spider-vision-smolvlm256.json
```

The first run downloads public weights from Hugging Face; image inference is local on CPU. Downloads and the virtual environment are ignored by Git and excluded from scaffold link validation and test-fixture copies. Model cache: `.model-cache/`; the Hugging Face processor may also use its normal user cache. No remote model code or paid inference endpoint is enabled. The installed dependency versions are recorded in `requirements-vision-lock.txt`.

Use `--input path/to/image.jpg` for another reference. `--revision COMMIT` pins a checkpoint; `--offline --revision COMMIT` requests cached files only. The tested 500M revision is `a7da5b986cb59b408707209984f360a5f4ad7e47`; the tested 256M revision is `7e3e67edbbed1bf9888184d9df282b700a323964`. Default vision preprocessing uses longest edge 1024, float32, greedy decoding and up to eight CPU threads. Both models require substantially more runtime memory than the GIF renderer.

The first image test found that both checkpoints named the spider. The 500M checkpoint selected a single isolated subject; the 256M checkpoint repeated all composition choices without choosing one. Coarse part and shape responses were brief. This single-image result supports trying 500M for classification; it does not establish general classification accuracy or automatic construction-guide generation. See [VISION_TEST.md](VISION_TEST.md) for exact results, commands and limitations.

### Resource and latency statistics

The vision runner now samples process CPU, resident RAM, system CPU/RAM and Windows GPU counters, by default every 0.25 seconds. It records separate phases for runtime imports, model loading, image preprocessing, token generation and answer decoding. Each answer includes time to the first generated token, time to the complete answer, generated token count and throughput including image/prompt processing inside generation. The first-token hook ignores the initial prompt supplied to the streamer.

CPU is reported both as a percentage of one logical CPU (can exceed 100%) and as a percentage of total logical CPU capacity. RAM is the whole Python process, not just model weights. Peaks are sampled observations and can miss shorter spikes. GPU statistics distinguish all-application activity from activity and dedicated/shared memory attributed to the benchmark process. Windows PDH measures the busiest GPU hardware engine after summing processes on each engine; it does not add parallel engine percentages. Unavailable counters are `null`, rather than zero. This GPU counter backend is Windows-specific. Other platforms retain CPU/RAM sampling and report GPU counters as unavailable.

```powershell
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/analyze_reference.py --offline --revision a7da5b986cb59b408707209984f360a5f4ad7e47 --output tools/drawing-studio/output/spider-vision-smolvlm500-profiled.json
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/analyze_reference.py --model HuggingFaceTB/SmolVLM-256M-Instruct --offline --revision 7e3e67edbbed1bf9888184d9df282b700a323964 --output tools/drawing-studio/output/spider-vision-smolvlm256-profiled.json
```

Each run writes the answer/resource report, a `.telemetry.json` with timestamped raw samples, and a `.metrics.csv` with phase statistics and prompt latency. `--sample-interval` accepts 0.1-2 seconds. Offline mode sets both Hub and Transformers offline flags before imports so processor sub-loads cannot perform metadata network checks. Download weights once before using offline mode. Profiled runs should be sequential to avoid competition between benchmark processes.

`--device cpu` remains the default. Explicit `--device cuda` requires a compatible installed PyTorch build/device and fails rather than silently reverting to CPU. CUDA timing synchronizes work before recording completion. The present machine has an AMD GPU and the installed CPU-only PyTorch build; GPU inference was not run. Whole-machine GPU utilization is not evidence that the model used GPU acceleration.

See [RESOURCE_PROFILE.md](RESOURCE_PROFILE.md) for the recorded spider comparison, hardware, exact conditions and limitations. Hardware sampling is instrumented; no uninstrumented overhead control, repeat-run confidence intervals or controlled system-idle baseline is claimed.

## Image tracing and geometric support scores

`measure_shapes.py` proposes circles, ellipses, triangles and rectangles from image contours without reading the hand-authored spider guides, VLM answers or semantic labels. It also measures supplied traces. OpenCV is a CPU-only optional dependency; the detector needs no model weights or PyTorch. Install `requirements-shapes.txt` in the isolated environment before running:

```powershell
tools/drawing-studio/.venv-vision/Scripts/python.exe -m pip install -r tools/drawing-studio/requirements-shapes.txt
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/measure_shapes.py --input tools/drawing-studio/assets/spider-reference.jpg --output tools/drawing-studio/output/spider-shapes.json
tools/drawing-studio/.venv-vision/Scripts/python.exe -m unittest discover -s tools/drawing-studio -p test_shape_geometry.py -v
```

The routine traces grayscale thresholds and edges at three blur scales, plus color-cluster contours. It fits ellipses/circles and simple polygons, measures how well they match the trace and image, merges near-duplicate results, and ranks candidates. Shape names are geometric, not anatomical: `circle` does not mean `eye`. For a nearly uniform border, a candidate also needs at least 85% foreground-like interior pixels; this reduces background-gap proposals. That border-color assumption is disabled for nonuniform borders, and it does not perform full scene segmentation.

The **geometric support score is not a calibrated probability**. Ellipse evidence includes RMS distance from the trace to its fitted ellipse, normalized fit error, angular coverage, image-edge support with aligned gradients, filled trace/shape overlap, and repeatability across tracing settings. Weak image boundaries reduce the score even for a mathematically perfect supplied ellipse. A low visible-boundary score can reflect soft edges or occlusion rather than an incorrect artist's construction mass. Real confidence calibration would require labeled examples and held-out evaluation; synthetic regression tests alone do not establish that calibration.

`--min-score` defaults to 0.72 and `--max-shapes` to 24. The JSON exposes the component metrics, exact score formula, normalized 1280 x 698 coordinates, circle/ellipse geometry, proposal sources, background test and resource/timing measurements. Ellipse geometry is `[center_x, center_y, major_semiaxis, minor_semiaxis, rotation_radians]`. Scores of 0.85 or higher are called strong support, 0.72-0.85 moderate, and lower scores weak; these are heuristic bands, not empirical accuracy rates.

Outputs alongside the report:

- PNG overlay with candidate IDs, scores, and RMS pixel errors.
- SVG using editable native circles/ellipses and polygon primitives. This follows the SVG-primitive direction used in ShapeMotion; direct project/package integration is not implemented.
- `NAME-lesson.json`, a review-required Drawing Atelier lesson. Open it in the browser editor to review or adjust the proposed guides. Small or nested details are excluded by default. Existing authored lessons are not replaced.
- `NAME-telemetry.json`, sampled CPU/RAM/Windows GPU activity. Detection timing excludes Python imports and output rendering; a separate field includes monitor setup and optional trace assessment. Short detection runs have few samples, so resource peaks are coarse observations.

To measure your own traces, pass `--traces path.json`. Supported inputs are `{ "traces": [{ "points": [[x,y], ...] }] }` or the `guides` from a saved lesson, using normalized 1280 x 698 coordinates. Those assessments are saved separately from automatic proposals. Three points are needed for polygon measurement and at least five for ellipse fitting; sparse two-point axes do not produce a shape fit. The routine refuses output paths that would overwrite the input image or trace file.

See [SHAPE_MEASUREMENTS.md](SHAPE_MEASUREMENTS.md) for the reviewed spider result, local ShapeMotion/ShapeSmith source findings, scoring details and executed acceptance checks. In this first image test, clearly bounded eye-region geometry is much easier than occluded body masses and furry leg segments.

## Browser interface

From the repository root:

```powershell
python -m http.server 8765 --bind 127.0.0.1 --directory tools/drawing-studio
```

Open <http://127.0.0.1:8765>. Stop the server with Ctrl+C. Serve the directory over HTTP; opening `index.html` as a `file://` URL does not support its JavaScript modules consistently. No install, API key, account, external fonts or network service is required. JavaScript and Canvas 2D are required; target current desktop Chrome, Edge, Firefox and Safari. Touch/pointer handlers and a narrow-screen layout are implemented but require device verification.

## Use

- Play or pause the 60-second sequence, scrub to any mark, change speed, restart, or loop. Space plays/pauses; left/right arrows move between completed steps. Keyboard shortcuts yield to focused controls.
- Click a lesson stage to see its completed drawing and instructions. Keep construction lines toggles their persistence after construction; the initial construction stages always show them.
- Compare reference temporarily overlays the source. It does not appear in exported frames.
- Open a JPEG, PNG or WebP (up to 12 MB / 40 megapixels). The image fits the fixed 1280 × 698 drawing space without distortion. Other references receive generic teaching prompts and a starter oval/axes, not automatic anatomical decomposition.
- Select Ellipse, Axis or Contour to draw guides over a faint reference. Drag on the paper. Ellipses and axes appear in stage 2; freehand contours appear in stage 3. View returns to the simulation. Undo and Reset guides affect only lesson guides. Guides can be added up to a 500-guide limit.
- Save this frame exports a clean 1280 × 698 PNG. The six-step sheet exports a 1800 × 2370 PNG with six completed stages and instructions for printing or sharing. It is an image, not a PDF.
- Save editable lesson exports JSON containing the normalized reference and construction guides. Open lesson restores it. Files are processed in browser memory; there is no upload, automatic persistence or cloud storage. Save before closing the page.

The source is never simply faded over the drawing: paint consists of sampled brush strokes. Complex textures and transparent or nonuniform backgrounds can produce extra contours. The final result is a painted approximation; image analysis cannot infer a universal artist-quality instructional sequence. Custom semantic shapes and teaching instructions require authoring. The first sample is the user-provided spider reference, included for this requested study; no ownership or redistribution license is asserted. Do not use it as a generic framework example asset or publish it without appropriate rights.

## Implementation and verification

`core.mjs` contains deterministic geometry, edge extraction, sampled stroke generation and lesson validation. `app.mjs` supplies the Canvas renderer, playback, guide authoring and exports. Drawing operations are cached in offscreen layers so animation advances through individual strokes. This tool is isolated from Godot/C# runtime code; no migration or game-port parity is claimed.

```powershell
node --test tools/drawing-studio/core.test.mjs
node --check tools/drawing-studio/app.mjs
node --check tools/drawing-studio/core.mjs
```

See [VALIDATION.md](VALIDATION.md) for executed checks and remaining browser acceptance work.
