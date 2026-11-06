# Grounded construction and appendage separation

## Palp exclusion update

The latest run adds a separate grounding request for short pedipalps beside the mouth and long walking legs. Florence returned a whole-subject box for pedipalps; the size/position plausibility gate rejected it. Three mouth-adjacent segments are now marked unresolved and excluded from walking-leg grouping; 18 other segment candidates remain eligible. These are segment counts, not leg counts. No palp was confidently localized. The exclusion zone is a front-facing head-relative heuristic and can also exclude front-leg portions. Body subtraction still hides parts overlapping the head ellipse, so complete palp outlines remain unresolved.

Role labels and walking-leg eligibility are preserved in the editable lesson as well as the analysis JSON. Purple is reserved for plausible model-supported palp candidates; amber means unresolved. Blue eligibility does not certify a segment as a walking leg.

Latest full pipeline: **24.563009 seconds**, including 17.618649 seconds importing libraries. Palp grounding took 1.500942 seconds and construction/export 0.678253 seconds. The 29-second worker watchdog remains active. Previous measurements below describe the earlier run without the palp query and are retained for comparison. The current timing receipt and report supersede those artifacts.

Regression test: `tools/drawing-studio/.venv-vision/Scripts/python.exe -m unittest discover -s tools/drawing-studio -p test_fit_detected_parts.py -v`. Checks reject whole-subject palp boxes, quarantine ambiguous mouth regions, and permit only plausible local boxes as palp candidates.

Windows CPU test, 2026-11-02. Baseline cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc. Standalone 2D tool; existing phaser-to-godot workflow context, no engine migration. Uses the same pinned Florence snapshot and Python environment recorded in FLORENCE_INPUT_COMPARISON.md, plus OpenCV 4.13.0.

Run:

```
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/compare_florence_inputs.py --construction
```

The worker identifies the subject, selects the arachnid prompt from its caption, obtains color-image part boxes, fits body ellipses, separates exposed appendage regions and exports a review overlay, lesson JSON and telemetry. The parent terminates the worker after 29 seconds. The final measured run completed in **8.637724 seconds**, including startup, imports, cached loading and all exports except the final parent receipt. One-time downloads excluded.

Body fitting searches centers, radii and rotations near each model box. It measures proximity to smoothed image edges with compatible gradient orientation and penalizes scale departure from the box. Result: head center (623,307.5), radii (200,152.5), angle 0.15 rad; abdomen center (832.52,217.5), radii (187,114.75), angle 0.15 rad. Supported sampled perimeter fractions were 0.500 and 0.639. These are evidence fractions, not probabilities. Dashed orange completes unsupported portions. Visual review found these much more useful than unconstrained circle proposals, but the abdomen remains a simplified visible-region construction.

Appendages: use the plain-background mask, reject background-colored shadow using chroma distance to median body/background colors, subtract body ellipses expanded 7%, and partition remaining foreground by geodesic distance to local thickness maxima. Moment ellipses summarize the partitions. This yielded **21 exposed appendage-region candidates**. These are segments, not anatomical leg counts; neighboring segments can belong to the same leg, and overlapping legs can remain merged. Small round regions are filtered. The current lower-body and chroma assumptions are specific to this class of upright, isolated subject and are not general scene segmentation.

Visual acceptance: body construction improved; ground shadow removed from appendage proposals; several visible limb sections separated. Anatomically verified individual-leg chains and hidden roots remain unresolved. Exported lesson is explicitly review-required and does not replace authored guides. ShapeMotion manual tracing may support corrections; no external ShapeMotion implementation was imported.

Final phase seconds: imports 3.6153; cached load 0.4338; identification 1.7749; preprocessing 0.0183; color grounding 1.3891; construction plus export 0.5828. Highest observed phase RSS 1676.426 MiB. CPU/GPU samples remain in the report. No repeated-run performance guarantee.

Artifacts: output/florence-construction.png, output/florence-construction.json, output/florence-construction-lesson.json, output/florence-construction-receipt.json. Synthetic body recovery and blank-boundary rejection tests are in test_fit_detected_parts.py. Lesson compatibility is checked with core.mjs validateLesson. No scaffold files changed.
