# Local vision test on the spider reference

Date: 2026-11-02. Source baseline: repository `cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc` plus the current uncommitted drawing-tool implementation. Selected repository orientation remains `phaser-to-godot`, dimension `2d`; the workflow guide/example, 2D catalog and migration contract were read. This is an isolated vision experiment, not an engine migration.

## Test design

Test the existing 1280 x 698 image using small pretrained local vision-language models. Image SHA-256: `dd0c66cae0225d5c5f68df3575107c769bff5e58dee94e4334c3c8f7f2e12be2`. The same four neutral prompts and same image pixels are used for both models. The model receives no filename, authored guides, reference lesson, part labels or spider keyword. The existing drawing renderer does not read these test answers.

Acceptance for this image: name the visible subject, choose a single isolated subject rather than a scene, provide a background description, and identify visible features. The construction question is exploratory: it asks for shape types, not numerical coordinates. No training or fine-tuning was performed. Whether either pretrained model previously encountered this image in its training data is unknown.

## Environment and model revisions

Windows 10.0.22631, Python 3.11.3 in the ignored `.venv-vision` environment, PyTorch 2.10.0+cpu, Transformers 4.57.6, huggingface_hub 0.36.2, Pillow 12.1.0. Exact installed packages: `requirements-vision-lock.txt`. CPU, float32, 8 threads, longest-edge preprocessing 1024, greedy decoding, output cap 128 tokens. No answer hit the token limit.

| Checkpoint | Resolved revision | Actual parameters |
| --- | --- | --- |
| HuggingFaceTB/SmolVLM-500M-Instruct | a7da5b986cb59b408707209984f360a5f4ad7e47 | 507,482,304 |
| HuggingFaceTB/SmolVLM-256M-Instruct | 7e3e67edbbed1bf9888184d9df282b700a323964 | 256,484,928 |

The public checkpoint model cards identify Apache-2.0 licensing. Model code is supplied by the pinned Transformers package, with remote model code disabled and safetensors weights required. The reference remains a user-supplied asset with no additional redistribution license asserted.

## Exact responses

| Question | 500M answer | 256M answer |
| --- | --- | --- |
| Describe the main subject of this image in one sentence. | Spider. | In this image, we can see a spider. |
| Is this image primarily a single isolated subject, multiple separate subjects, or an environmental scene? Choose one and briefly describe the background. | Single isolated subject. | The image is primarily a single isolated subject, multiple separate subjects, or an environmental scene. |
| List the main visible parts of the subject. Mention only parts you can see. | Eyes, legs, body. | The subject is a spider with large eyes and a round body. |
| Describe the largest basic shapes that could be used to sketch this image. Do not guess hidden parts. | Sphere. | The largest basic shapes that could be used to sketch this image are circles. |

## Manual assessment and measurements

- **passed**: subject recognition for both models on this image.
- **passed**: composition choice for 500M. **failed**: 256M repeated the choices and did not select one.
- **failed**: requested background description for both models; neither supplied one.
- **passed**: coarse visible-feature identification. Responses are sparse, not complete anatomical inventories. Exact eye/leg counts and part locations were not requested or assessed.
- **not_run**: coordinate/ellipse prediction, automatic mask generation, and construction-guide accuracy. Neither response supplies a positioned construction plan, and the shape-type prompt does not establish whether a more specific prompt would produce one.
- **not_run in the original runs**: multi-image accuracy, scenes, multiple subjects, CPU-memory profiling, GPU or mobile inference, and offline replay. Later CPU/RAM/GPU-counter and offline runs are recorded in [RESOURCE_PROFILE.md](RESOURCE_PROFILE.md). One test image cannot establish general accuracy or robust instruction following.

500M load/download: 13.720 s; per-prompt inference: 3.768, 3.715, 3.801, 3.670 s. Total: 29.072 s. 256M load/download: 9.442 s; per-prompt inference: 3.502, 3.579, 3.446, 3.507 s. Total: 23.851 s. Hardware model was not profiled. These are single observed runs with very short answers; they are not a general speed benchmark or token-efficiency comparison. Agent token usage is not exposed by the available session tools.

Decision: use 500M as the next candidate for a proposed subject/composition classification step with manual review. Do not automatically replace authored guides based on this experiment. Add a varied test set and more explicit output validation before routing real drawing lessons from model responses.

## Executed commands and evidence

From the repository root:

```powershell
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/analyze_reference.py --output tools/drawing-studio/output/spider-vision-smolvlm500.json
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/analyze_reference.py --model HuggingFaceTB/SmolVLM-256M-Instruct --output tools/drawing-studio/output/spider-vision-smolvlm256.json
```

Both commands completed inference and saved unedited responses. Native approval allowed model downloads; image pixels were processed locally rather than uploaded to a hosted inference service. Initial CPU PyTorch installation was blocked by the sandbox, then the approved attempt exposed old-pip metadata handling. Updating pip only inside the isolated environment and rerunning the pinned installation resolved it.

Artifacts in ignored `output/`:

- `spider-vision-smolvlm500.json`, SHA-256 `2b88e5a41a47b201df3c6c6825f35041cb8afaa64140323902a0aee8f2230c8e`.
- `spider-vision-smolvlm256.json`, SHA-256 `43a11dcc9dfcaa40fda195f549e4c694d8f4447483c539a9f3c84c3623fd3bce`.

These include exact model commits, image hash, runtime settings, every prompt, every generated answer, token counts and durations. Copies and the comparison are added to the existing private animation Page for remote review.

**passed**: `python -m py_compile tools/drawing-studio/analyze_reference.py`, `python tools/validate_workflows.py`, and `python -m unittest discover -s tools/tests -v` (20 tests). The scaffold test suite and document walker now exclude `.venv-vision` and `.model-cache`, so large downloaded dependencies and third-party documentation are neither copied into test fixtures nor treated as repository source. A regression test covers those exclusions. Other source links remain checked.

**not_run**: engine build/playtest; none applies. No claim that these recognition results complete automatic drawing-plan generation is made.
