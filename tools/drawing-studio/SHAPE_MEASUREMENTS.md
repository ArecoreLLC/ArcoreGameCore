# Image-only shape proposal and trace measurement evidence

Date: 2026-11-02. Baseline: repository `cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc` plus the uncommitted drawing-tool work. Selected orientation: workflow `phaser-to-godot`, dimension `2d`; guide, example, dimension catalog and migration contract read. No engine runtime migration is involved.

Scope: propose basic primitives from image contours, measure their geometric/image support, measure supplied traces separately, export a review overlay, SVG and draft lesson, and capture detection/resource statistics. Scores must expose their ingredients and must not be represented as probabilities of correct semantic parts.

## Related local source review

- `X:/Projects/Repo-Library/ArecoreLLC/ArcoreShapeMotion`, revision `1e5e60b2167c54f28bde30454d3e0bfe3b74f98a`: read the root README, `studio/src/modules/tracing/TracingCanvas.tsx`, tracing-tool file inventory and `studio/src/utils/simplifyPath.ts`. It contains manual Bezier tracing, SVG layer construction and SVGPathCommander coordinate rounding/optimization. That helper is path optimization, not automatic image-to-primitive detection or scored ellipse fitting.
- `X:/Projects/Repo-Library/ArecoreLLC/ArcoreShapeSmith`, revision `ac0cb58de062113bba2defa204d05ed6ae26daba`: this local checkout contains only its root README. No detector was available there to reuse.

These statements concern the inspected local snapshots; remote changes were not fetched. External repositories were not modified and their source was not copied into this generic tool. The new implementation follows their editable-SVG direction using OpenCV geometry rather than claiming a pre-existing detector integration.

## Method and scores

The detector receives image pixels only. It traces Canny edges and seven grayscale thresholds at three blur scales, then contours from eight Lab color clusters. OpenCV AMS ellipse fitting and polygon approximation propose primitives. Near-circular ellipse fits are compared with an actual circular geometry before assigning the circle label. Near-duplicate proposals are merged across parameter settings.

Ellipse base score:

```text
fit_quality = exp(-(normalized_rms / .075)^2)
base = .35 * fit_quality
     + .30 * gradient_aligned_boundary_support
     + .15 * trace_angular_coverage
     + .20 * filled_trace_shape_iou
if boundary_support < .45:
    base *= boundary_support / .45
final = base * (.95 + .05 * min(1, (source_count - 1) / 4))
```

RMS uses nearest points on the fitted ellipse in normalized image pixels. Edge support requires a nearby image edge with a gradient approximately normal to the candidate boundary. Polygon base score is `.65 * filled_trace_shape_iou + .35 * boundary_support`, with the same weak-boundary penalty and automatic-candidate repeatability multiplier. Supplied trace fits expose their base measurements without the cross-setting repeatability multiplier.

For a uniform border, foreground-like pixels are estimated by Lab distance from the median border color. At least 85% of candidate interior pixels must pass that test. This rejects the two triangular negative-space gaps found in the initial spider pass, while retaining the 11 circular/elliptical candidates. Small or nested detail candidates remain visible in the report but are omitted from the draft lesson.

These weights, tolerances, thresholds and score bands are heuristics. Repeatability across blur/threshold settings on the same image is not independent ground truth. A score of 0.98 means strong measured geometric support under this rule, not a 98% chance of an eye or an empirically calibrated probability. The tests below validate mechanics and known geometry, not real-image accuracy rates.

## Final spider run

Runtime: Python 3.11.3, OpenCV 4.13.0, numpy 2.4.6, Pillow 12.1.0 and psutil 7.2.2; CPU, four OpenCV threads, i7-12700K host. No model weights, VLM prompts, GPU kernels or authored-guide coordinates enter automatic proposal generation.

```powershell
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/measure_shapes.py --traces tools/drawing-studio/output/spider-authored-traces.json
```

The optional trace file was produced from the existing lesson's 32 ellipses solely to exercise the separate supplied-trace measurement path. It does not seed the automatic detector.

**passed**: 576 eligible traced contours produced 118 preliminary proposals. Final automatic result: **11 candidates, seven circles and four ellipses**, with scores 0.8884-0.9784. Four small/nested details were omitted from the review-required draft, leaving seven guides. The final detection phase took **0.6582 s**, excluding Python imports, monitor setup, optional trace assessment and output encoding. Peak observed process RSS was **83.395 MiB**. This is one short instrumented run with few resource samples, not a comparative speed benchmark.

**passed**: static PNG review against the reference. The seven larger candidates lie around visible eye-region contours; four smaller candidates lie around reflection details. The partly hidden left lateral eye outline was not recovered as a full ellipse. No large head/abdomen or leg construction masses were recovered at the selected threshold. The initial negative-space triangles were removed by the uniform-background interior gate. The final overlay identifies geometric candidates without assigning anatomy.

**passed**: 32 supplied construction ellipses were assessed separately. The abdomen/head traces scored approximately **0.26 / 0.45**, mainly because their idealized, partially occluded boundaries have little image-edge support. The eye construction traces scored approximately **0.84-0.99**. Low body scores do not mean those artist-authored construction ovals are wrong; they demonstrate that visible-boundary evidence and useful inferred construction are different criteria.

**passed**: the SVG parses as XML and contains the expected 11 primitives; exported draft lesson passes the existing `validateLesson` contract with seven guides. Coordinates stay in the existing normalized drawing space. Opening/editing that lesson in the browser was **not_run** because browser access remains unavailable.

## Tests and remaining work

```powershell
tools/drawing-studio/.venv-vision/Scripts/python.exe -m unittest discover -s tools/drawing-studio -p test_shape_geometry.py -v
```

**passed**: seven tests cover rotated-ellipse parameter recovery, perfect trace versus absent image evidence, reduced support under occlusion, triangle/rectangle measurement, blank-image rejection, deduplicated circle recovery, input-image preservation and reviewable lesson/SVG/PNG output. No private game assets are used in these synthetic fixtures. Resource sampling uses the previously tested `vision_metrics.py` module.

**not_run**: labeled real-image precision/recall, calibrated confidence probabilities, robust occluded-body decomposition, automatic semantic part naming, direct ShapeMotion package import, and general scene segmentation. Future real-image labels and held-out data are required before treating scores as empirically calibrated confidence. Automatic proposals do not replace the existing authored spider lesson.

Artifacts in ignored `output/`: `spider-shapes.json`, `spider-shapes.png`, `spider-shapes.svg`, `spider-shapes-lesson.json`, `spider-shapes-telemetry.json` and the optional measurement fixture `spider-authored-traces.json`. The JSON contains all component scores, contour source settings, supplied-trace results, and resource samples summary. No engine build or game playtest applies; no token-savings claim is made.

**passed**: `python tools/validate_workflows.py`, Python compilation of both new modules, and `python -m unittest discover -s tools/tests -v` (20 scaffold/inventory tests). Uploaded the reviewed PNG, measurement JSON, native SVG and draft lesson to the existing private ChatGPT Page and read back the saved section and file references. Page: `https://chatgpt.com/space/page_6ab0d9b077808191a6a1f148d32ef570`. Rendered online Page inspection remains **not_run**.
