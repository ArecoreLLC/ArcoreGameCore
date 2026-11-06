# Subject identification and three input variants

Executed 2026-11-02 on the existing Windows i7-12700K CPU environment, eight Torch threads, float32. Standalone 2D drawing-tool experiment; baseline revision cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc. Model and versions are pinned in the generated report and prior FLORENCE_TEST.md.

Command:

```
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/compare_florence_inputs.py
```

The parent allows the worker 29 seconds and terminates it on timeout. The final successful run took **10.913643 seconds** including worker startup, imports, cached model loading, identification, preprocessing, all three queries, comparison image, metrics and report export. One-time model download and final parent receipt write are excluded. This is one measured run, not a guaranteed latency distribution.

Identification uses DETAILED_CAPTION on original color pixels without supplying a subject name or authored guide. The answer named a cartoon-like 3D jumping spider. It also described a white background and arms; those details are imperfect and were not adopted as anatomy. An explicit keyword rule selected the arachnid profile from the word spider. That profile supplied the same grounding text for every variant: “The spider has a head, an abdomen, and legs.” Other subjects currently fall back to the generated caption; this is not a complete general profile classifier.

| Phase | Seconds | Result |
|---|---:|---|
| Imports | 3.649 | Local libraries |
| Cached loading | 0.445 | CPU model and processor |
| Identify subject | 1.794 | Jumping spider; arachnid profile selected |
| Preprocessing | 0.016 | Grayscale and Gaussian blur radius 2 original pixels |
| Color grounding | 1.487 | Subject, head, abdomen, grouped legs |
| Grayscale grounding | 1.423 | Same four labels |
| Smoothed grayscale grounding | 1.289 | Subject and head only |

Grayscale versus color box IoU: head 0.9836, abdomen 0.9881, legs 0.9939. Smoothed head versus color: 0.9910. Missing detections are null, not zero-overlap boxes. Label matching removes leading a/an/the. IoU measures agreement between predictions, not accuracy against ground truth.

Visual review of all three panels found plausible head and abdomen locations in color and grayscale. Legs remain a single broad group. Smoothing lost the abdomen and legs, so it did not improve this image's model grounding. Keep color as the default; grayscale is a useful agreement check. This does not rule out smoothing for downstream edge extraction or other subjects.

Mean machine CPU during the three grounding calls was 24.5-26.1% across 20 logical processors. Highest observed phase RSS was 1635.043 MiB. Inference is CPU-only. Raw process/system GPU samples and CPU/memory telemetry are retained in the JSON; they are sampled observations rather than continuous peak measurements.

An initial run exposed a native-parser compatibility issue: the slow tokenizer inserted whitespace between location tokens, and native parsing produced empty boxes despite valid raw coordinates. The runner now removes whitespace only between adjacent special-token boundaries before parsing, retains both raw and parser text, and was rerun end to end. The final overlay was visually checked. The timing above belongs to the corrected run, not the combined development session.

Artifacts: output/florence-input-comparison.json, output/florence-input-comparison-receipt.json and output/florence-input-comparison.png. Acceptance: total time under 30 seconds PASSED; automatic subject identification PASSED for this sample; full individual-leg detection NOT ACHIEVED. No claim that classification improves accuracy follows from this comparison because the parts prompt matches the earlier supplied-subject prompt.
