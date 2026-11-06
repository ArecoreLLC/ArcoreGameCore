# Florence CPU part grounding test

User acceptance target: results under 30 seconds on CPU. Tested on the existing Windows i7-12700K machine with eight Torch threads, float32, torch 2.10.0+cpu, transformers 4.57.6. Standalone 2D analysis, no engine migration. Baseline repository revision cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc.

Checkpoint: florence-community/Florence-2-base at 00921df66db728a9ceb750f5eca43e5c203a2051. This is the native Transformers conversion referenced by https://huggingface.co/docs/transformers/v4.56.0/en/model_doc/florence2 . No repository Python code executed; safetensors weights and local native model classes used.

Commands:

```
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/test_florence.py --download
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/test_florence.py
```

First command downloads and pins weights. Second runs offline from the local snapshot. All tasks use CAPTION_TO_PHRASE_GROUNDING, greedy decoding, 128 output tokens, a soft generation time limit of 28 seconds. This is not a hard process deadline. Prompts provide subject/part names; the model locates them. Authored guide coordinates are not supplied.

Measured run: cached model/processor load 0.497 seconds; four preprocessing/inference/postprocessing queries took 1.445, 1.301, 1.305 and 1.354 seconds. Whole measured benchmark, including imports, monitoring and overlays, took 9.580 seconds (excluding download, Python launch and final report serialization). All four timing checks passed the 30-second target in this one run. No repeated-run latency guarantee claimed.

Combined prompt: “The spider has a head, an abdomen, and legs.” Returned head box [423,155,823,460], abdomen [653,90,1027,345], leg-group [192,282,1086,649], plus whole subject. Visual overlay review found plausible head and abdomen locations. These are bounding boxes, not segmentation masks or precise anatomical contours.

Quality limitations: head-only query produced both a plausible head and an erroneous whole-subject head box. Abdomen-only query incorrectly labeled the head/whole subject as abdomen. Legs remained broad groups, not individual limb chains. Thus speed passes; reliable part identification remains partial and prompt-sensitive.

The combined query used 25.09% mean machine CPU (20 logical processors), observed 1537.848 MiB phase peak RSS, and zero own-process GPU utilization in its five periodic samples. Later queries reached about 1615 MiB RSS. GPU statistics refer to this process, not other applications. Exact per-phase metrics and raw samples are in output/florence-benchmark.json; overlays are output/florence-{parts,head,abdomen,legs}.png.

Next useful integration: use combined profile descriptions to propose part boxes, refine boundaries within those proposals, and retain rejection/review when prompts disagree. Do not treat a box-derived ellipse as a measured contour.
