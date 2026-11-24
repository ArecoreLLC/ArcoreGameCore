# Reuse review — 0.1.0

Boundary: extracted stroke storage, polyline math, point-cloud and DTW distances,
window statistics, and SPARC/time-series primitives. Pressure calibration bands,
pressure weights, trimming eligibility, motion aggregation, baseline deficits,
pause-score weights, recognition policy, and all tuning remain in the game.

Existing InkStroke, InkGeom, PDollar, Dtw global names are only declared in old
wrapper paths. PressureModel and Smoothness delegate math while retaining policy.
Shared scripts register no global names. Dependencies stay within this module.

Valid-input formulas and ordering are preserved. Explicit edge fixes: resampling
one point avoids division by zero; an empty point cloud no longer indexes -1.
Tests use non-glyph shapes and varied sampling rates. A frozen direct-DFT oracle
checks the extracted Goertzel implementation. The existing game tests were left
unchanged; parent must run them after concurrent contributions converge.

Limitations: this is not a general malformed-live-input validator, optimized DTW
service, or arbitrary-size streaming library. Pressure presence/timestamp repair
are retained heuristics. No benchmark or new score-policy claim is made.
