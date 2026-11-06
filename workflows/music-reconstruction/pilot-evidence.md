# Local reconstruction pilot — November 5, 2026

Consumer: ShammyVerse. Sources and private game content remain in its own folder.
Local workspace: `X:/Projects/ShammyVerse`.

The consumer's `scripts/music-reconstruction/reconstruct.py` orchestrates the
existing Sonic Alchemist workers and Repair Lab function. Its `renderer` adapter
uses Alchemist's pinned RustySynth 1.3.8 instrument engine. The companion
`catalog_and_verify.py` uses SoundCore's native service/API and Alchemist's native
project inspection executable. These consumer paths are local references, not
code shipped by this generic GameCore workflow.

## Reproduction commands

Run from the consumer root after inspecting the scripts and preparing the existing
Alchemist runtimes/models. No model or package download was needed in this pilot.

```powershell
cargo build --offline --release --manifest-path scripts/music-reconstruction/renderer/Cargo.toml
& X:/Projects/ArcoreSonicAlchemist/.venv-repair/Scripts/python.exe -B -u scripts/music-reconstruction/reconstruct.py --all
& X:/Projects/ArcoreSonicAlchemist/.venv-repair/Scripts/python.exe -B -u scripts/music-reconstruction/catalog_and_verify.py
& X:/Projects/ArcoreSonicAlchemist/.venv-repair/Scripts/python.exe -B -u scripts/music-reconstruction/prepare_review.py
python -X utf8 -B X:/Projects/ArcoreGameCore/tools/ecosystem.py --project Config/ArcoreProject.json
```

For one source, replace `--all` with `--song "Shampoo Island Shanty"`.
Outputs are under `Design/Audio/Reconstruction`, with bank/license copies under
`libraries/generaluser-gs`, native project reload logs beside projects, and a
separate `soundcore-data` catalog. The service's token is ephemeral and unlogged.

## Observed processing and corrections

- Eleven unique authoring MP3s discovered, approximately 41 minutes total.
- Consumer GameCore dependency/declaration check passed.
- Pinned local instrument renderer compiled successfully offline.
- Initial restricted GPU run failed when MIOpen could not open its cache database.
- Authorized retry succeeded on AMD Radeon RX 7900 GRE / ROCm.
- First source: 210 seconds, six stems, 9,261,000 frames per stem at 44.1 kHz.
- Observed first separation inference/overlap-add time: approximately 29.30 seconds,
  excluding full process/model setup. This is one run, not a performance benchmark.
- First source mixture reconstruction RMS: approximately 0.011234, which does not
  measure perceived isolation quality.
- All 11 full-song reconstruction renders completed. Final native/catalog checks
  are recorded separately below and in the consumer's machine-readable evidence.
- The first native Compose attempt rejected near-adjacent same-pitch notes. The
  pattern-only one-sample end adjustment resolved that precision issue.
- Native Alchemist Compose rendered five instrument layers / 1,127 notes for the
  first 48-second section, with its normal two-second tail, and reopened the project.
- Native inspection found seven full-scale samples in the first cleaned vocal
  inspected. Cleanup recipe version 2 added measured static -1 dBFS headroom;
  vocal files and downstream mixes were regenerated.
- Initial GameCore checks hit existing Windows default-encoding and sandbox
  temporary-directory errors. Running with UTF-8 mode and permitted temporary
  fixture access passed the workflow validator and all 29 tests.

The native validation binaries compile Alchemist's actual `inspect-project.rs`
and `render-song.rs` examples against its current `arcore-audio` library, with
release artifacts kept in the consumer. The original soundtrack references in the
game are unchanged. The 256 kbps MP3 review copies include an additional 1 dB of
headroom and must pass finite-sample, peak and duration checks after decoding.

## Final measured batch results

The consumer's final native/catalog verification completed successfully:

| Measurement | Observed result |
| --- | --- |
| Source songs | 11, total 2,465.84 seconds (41 minutes 5.84 seconds) |
| Extracted stems | 66 aligned stems |
| Instrument MIDI lanes | 55, containing 64,859 automatically proposed events |
| Native project reloads | 91 passed, plus the separate native Compose round trip |
| Final PCM mixes | 11 finite, readable files; zero full-scale/clipped samples |
| Final cleaned vocal PCM files | 11 finite, readable files; zero full-scale/clipped samples |
| Original source identity | All 11 source hashes unchanged |
| SoundCore dependency snapshot | 34 assets: 11 originals, 11 clean vocals, 11 mixes, one bank |
| Listening/MIDI correction/game playback | not_run; candidates remain unapproved |

The high MIDI event count includes transcription artifacts and heuristic drum
proposals; it is not an accuracy metric. The final SoundCore project ID is
`shammyverse-music-reconstruction` in the isolated workspace catalog. Earlier
intermediate asset versions may remain in that catalog; the final saved manifest
identifies the current 34 dependencies without deleting prior history.

## Final evidence locations

All locations are relative to the consumer root:

- `Design/Audio/Reconstruction/batch.log`
- `Design/Audio/Reconstruction/batch-status.json`
- `Design/Audio/Reconstruction/toolchain.json`
- `Design/Audio/Reconstruction/gamecore-check.json`
- `Design/Audio/Reconstruction/verification-summary.json`
- `Design/Audio/Reconstruction/soundcore-project-manifest.json`
- `Design/Audio/Reconstruction/<song>/report.json`
- `Design/Audio/Reconstruction/<song>/verification-and-catalog.json`
- `Design/Audio/Reconstruction/native-compose-validation/render-report.json`
- `Music Review/README.md`
- `Music Review/Play All.m3u8`
- `Music Review/review-manifest.json`

Listening, note correction and game-engine playback remain not_run unless a later
dated record explicitly supplies that evidence. Original game music references
remain unchanged. SoundCore's desktop service was unavailable; the isolated local
catalog is not the user's desktop catalog.

## Quality review extension — 2026-11-05

The consumer audit compared all 55 first-pass lanes at 64 and 256 synth voices:
all were PCM-identical. An overloaded control differed and a six-note chord
equalled summed single-note renders. Polyphony was not the cause in these files.
The three-band drum detector and automatic tonal transcription remain limiting.
Full details and per-song measurements stay in the consumer's
`Design/Audio/Reconstruction/QUALITY-AUDIT.md` and `quality-audit/summary.json`.

Alchemist now contains Performance and Quality drum modes. Native tests cover
velocity samples, overlapping hits, tails, hat choking, recipe roundtrip and
live/offline PCM equality. Frontend and native desktop builds passed. Quality
uses licensed AVL Black Pearl recordings; attribution ships with the samples.
See [kit limitations and review contract](quality-review.md).

The consumer generated overlays and source-linked theory metadata for all eleven
songs. A browser test loaded all 22 original/reconstructed audio links and checked
zoom, seek, A/B playback and exported notes. A 30-second same-note kit comparison
is ready for listening. This does not establish fidelity or listening acceptance,
and all eleven full-song drafts have not yet been rerendered with corrected notes.

A subsequent 210-second full-song Quality candidate was rendered with the
acoustic kit, Salamander piano and bounded, per-hit source-based drum timing
proposals. The original and candidate were compared directly, and a separate
Quality overlay was generated. The drum envelope's best lag changed from about
11.61 ms to 0 ms at 11.61 ms analysis resolution. This is proxy evidence, not a
claim of perfect timing. The candidate MP3 decoded to exactly 10,080,000 stereo
frames at 48 kHz with no clipped samples; its native three-track project reopened.
Bass, guitar, residual Other and cleaned vocals retained their first-pass parts.
Listening acceptance and manual correction of all instrument parts remain pending.
The consumer records exact recipes, hashes, attribution and metrics in
`quality-pass-shampoo-island-shanty/quality-pass-report.json`.
