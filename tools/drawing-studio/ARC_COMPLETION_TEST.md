# Partial arc completion

Standalone 2D experiment at baseline cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc; Windows, Python 3.11 / OpenCV 4.13.0 in the existing vision environment. Same workflow context as PART_CONSTRUCTION_TEST.md. No engine changes.

Run `tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/complete_arcs.py`.

Multi-scale smoothed gradient Hough proposals complete circles from partial arcs. A second pass stretches image height by 1.35 to propose horizontal ellipses. These fixed shape/size hypotheses are generic search constraints, not authored spider coordinates. This is not an unrestricted ellipse fitter. At normalized image size 1280 x 698, the circle radius range is 90-250 pixels.

Green overlay samples have nearby normal-aligned edges within eight original-image pixels; orange dashed samples complete the shape without that evidence. Support can come from unrelated neighboring parts. Scores combine perimeter support and angular spread; they are not probabilities or semantic confidence. Ellipse scores are measured in the stretched image.

Actual spider run: 12 hypotheses, 0.4714 seconds proposal time, 84.727 MiB observed phase RSS, 1.989% mean machine CPU, one periodic GPU sample with zero own-process activity. Too few samples for a reliable GPU peak. Imports/export excluded.

Visual review: abdomen-sized circle recovered; head-sized candidates remain approximate, with competing circles around eyes and leg groups. The full overlay intentionally exposes false positives. No automatic anatomical identification or reliable best-head selection is claimed. JSON and draft lesson exports require review before use.

Acceptance: partial synthetic circle recovered within 15 pixels of center and radius; blank image rejected. Test command: `tools/drawing-studio/.venv-vision/Scripts/python.exe -m unittest discover -s tools/drawing-studio -p test_complete_arcs.py -v`. This establishes arc completion behavior, not accuracy across real subjects.
