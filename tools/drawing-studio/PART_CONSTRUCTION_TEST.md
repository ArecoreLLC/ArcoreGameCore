# Part construction experiment

Baseline revision: cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc. Windows, Python 3.11 isolated vision environment, OpenCV 4.13.0. Scope: standalone 2D CLI experiment, no engine migration. Selected workflow context: phaser-to-godot / 2d.

Run: `tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/construct_parts.py`

Uses the supplied spider image, plain-background foreground extraction, local thickness maxima, priority flooding and moment ellipses. No trained part model or hand-authored positions. The spider prior currently supplies only coarse body/limb terminology; it does not enforce an anatomical graph. Adjacency is measured from regions, not verified anatomical connectivity. Semantic and visibility confidences remain null.

Executed result: six proposals, five region adjacencies, 1.057464 seconds for proposals, 73.086 MiB observed phase peak RSS, 1.921% mean machine CPU (20 logical processors); process GPU samples zero. Only three periodic samples: not a robust performance benchmark. Imports and export are excluded from phase time.

Acceptance: CLI export passed (JSON, PNG, draft lesson). Visual anatomical decomposition FAILED: one ellipse merges front body, abdomen and most legs; some left limb segments are recovered, but a shadow/background fragment is also proposed. The result is an experimental diagnostic and must not replace the authored drawing lesson. No pretrained segmentation model tested in this experiment.

Next required step: semantic part segmentation or user-selected part seeds before geometric fitting. Plain silhouette connectivity is insufficient for this image's overlapping parts. Draft exports require correction before rendering a how-to-draw aid.
