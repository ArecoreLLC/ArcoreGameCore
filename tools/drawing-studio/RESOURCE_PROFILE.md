# Spider vision resource and latency measurements

Date: 2026-11-02. Repository baseline: `cdd5732ea9ad99755ec9ad11b55c1d38649ba3dc` plus the current uncommitted drawing-tool work. Orientation remains workflow `phaser-to-godot`, dimension `2d`; the selected guide/example, dimension catalog and shared contract were read. This is a local model experiment with no engine migration or game runtime changes.

## Conditions

CPU: Intel Core i7-12700K, 12 physical cores / 20 logical processors. Installed RAM: 63.75 GiB. Display adapters: AMD Radeon RX 7900 GRE and Meta Virtual Monitor. Execution: CPU-only PyTorch 2.10.0+cpu, Python 3.11.3, Transformers 4.57.6, Pillow 12.1.0, psutil 7.2.2. Model and image hashes are retained in the per-run JSON. Same four neutral prompts, same image and exact checkpoint revisions as [VISION_TEST.md](VISION_TEST.md).

Runs were sequential, using cached weights with offline flags, float32, 8 CPU threads, a 1024-pixel longest-edge setting and greedy decoding. Sampling interval requested: 0.25 s; observed 75 samples for 500M and 70 for 256M. The sampler measures this Python process plus system-wide activity. GPU engine counters and GPU process memory were available through Windows PDH, including on the AMD adapter. The separate GPU execution path was not run because the installed PyTorch build is CPU-only; these are not CPU-versus-GPU inference benchmarks.

## Observed results

| Metric | SmolVLM 500M | SmolVLM 256M |
| --- | --- | --- |
| Load processor/model from cache, excluding runtime imports | 0.613 s | 0.416 s |
| Mean first generated token, excluding external preprocessing | 3.492 s | 3.086 s |
| Mean complete answer, including preprocessing and decoding | 3.792 s | 3.568 s |
| Process CPU during generation, share of all 20 logical CPUs | 24.12% | 22.55% |
| Peak sampled process CPU, entire measured run | 33.18% | 29.27% |
| Peak sampled resident process RAM | 2997.809 MiB / 2.93 GiB | 2033.223 MiB / 1.99 GiB |
| Peak model-process GPU engine utilization | 0% | 0% |
| Peak model-process dedicated GPU memory | 0 MiB | 0 MiB |
| Machine-wide busiest GPU engine mean / peak | 0.406% / 0.995% | 0.411% / 30.504% |
| Entire measured analysis, including imports and load | 19.431 s | 18.193 s |

CPU generation means are calculated from summed process CPU-seconds divided by summed generation wall time and 20 logical processors. They are not averages of process percentages normalized to a single core. For example, 24.12% machine capacity corresponds to about 482% on the one-core scale. RSS includes the interpreter, dependencies, tensors and retained buffers.

The device-wide GPU peak during the 256M run belongs to overall system activity, not the model: the benchmark process GPU counters and GPU memory remained zero. Device-wide utilization is calculated from engine counters for all applications. The first PDH intervals can be shorter than the requested polling interval, and peaks are observations over the driver's counter windows. Sampling cannot reliably attribute other applications' work or estimate model GPU performance from a CPU run.

## Prompt latencies

| Prompt | 500M first token / complete answer | 256M first token / complete answer |
| --- | --- | --- |
| Subject | 3.464 / 3.664 s | 2.946 / 3.302 s |
| Composition | 3.502 / 3.822 s | 3.151 / 3.747 s |
| Visible parts | 3.505 / 3.923 s | 3.160 / 3.643 s |
| Construction shapes | 3.497 / 3.758 s | 3.088 / 3.580 s |

Answers matched the earlier unprofiled test. The 500M model still selected a single isolated subject; 256M still repeated the choices. Resource profiling does not change those quality findings.

## Commands and verification

```powershell
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/analyze_reference.py --offline --revision a7da5b986cb59b408707209984f360a5f4ad7e47 --output tools/drawing-studio/output/spider-vision-smolvlm500-profiled.json
tools/drawing-studio/.venv-vision/Scripts/python.exe tools/drawing-studio/analyze_reference.py --model HuggingFaceTB/SmolVLM-256M-Instruct --offline --revision 7e3e67edbbed1bf9888184d9df282b700a323964 --output tools/drawing-studio/output/spider-vision-smolvlm256-profiled.json
```

**passed**: both instrumented runs completed inference and produced per-phase process CPU-seconds/utilization, sampled RAM peaks, available Windows GPU utilization/memory, first-token timing, complete-answer timing, tokens and overall analysis time. Raw samples and report sample counts matched; every first-token time was less than its complete-answer time. CSV phase exports were generated from these measured reports using the runner's `write_metrics_csv` helper, after adding that final export feature. Report JSON, raw `.telemetry.json`, and phase `.metrics.csv` files are under ignored `output/`; a derived `vision-profile-comparison.json` records the table inputs.

An initial offline attempt still made processor metadata HEAD requests because a Transformers sub-load did not propagate the expected setting. That owned process was stopped; the offline flags were set before importing Transformers/Hub, and the two final cached runs above succeeded. The stalled attempt is excluded from these performance numbers.

**passed**: `python -m unittest discover -s tools/drawing-studio -p test_vision_metrics.py -v` (4 tests): per-engine process attribution, missing counters versus idle values, elapsed-time weighted sample means, and prompt-excluding first-token timing. `python -m py_compile tools/drawing-studio/analyze_reference.py tools/drawing-studio/vision_metrics.py` passed.

**not_run**: GPU-accelerated model execution, repeated-run distributions, memory/allocation profiling finer than the polling interval, energy/temperature measurements, controlled idle baseline or instrumentation-overhead comparison. Current data are two individual instrumented runs, not general speed or efficiency claims. Agent token usage is not available through this session's tools. Engine build/playtest does not apply.
