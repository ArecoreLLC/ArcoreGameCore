# Reconstruct recorded music as editable vocals and instruments

Status: exploratory. This workflow produces auditionable reconstruction drafts;
it does not establish faithful transcription, transparent vocal repair, or a
production-ready game soundtrack. Applicable to 2D and 3D consumers.

Read the [worked example](example.md), [integration workflow](../game-project-integration/README.md),
[shared contract](../../shared/migration-contract.md), and [sound catalog boundary](../../tools/integrations/sound-catalog.md).
The consumer owns source music, intermediate files, MIDI, projects and acceptance
records. Do not copy private songs or game-specific code into GameCore.

## Tool responsibilities

| Component | Responsibility | Boundary |
| --- | --- | --- |
| GameCore | Select workflow, check consumer declarations, define evidence and handoff | Does not perform audio inference or prove game playback |
| Sonic Alchemist | Pinned HTDemucs separation, Basic Pitch analysis, Repair Lab processing, SF2 synthesis and editable projects | Automatic notes and instrument guesses require review |
| SoundCore | Search assets, retain source/license metadata, catalog original and derived assets, snapshot dependencies | Cataloging a bank does not render MIDI |
| Consumer | Orchestrate operations, retain originals, choose instruments, build mixes, validate target playback | Owns artistic decisions and release acceptance |

Alchemist's local interfaces are documented in its `README.md`,
`docs/REPAIR_LAB.md`, `engine/worker.py`, `engine/analysis_worker.py`,
`crates/audio-core/src/composition.rs`, and `crates/audio-core/src/project.rs`.
Read the installed versions before using these development interfaces. SoundCore's
contract is in its `docs/agents.md`; discover live capabilities before writes.

## 1. Inventory and freeze the input

1. Enumerate source music, separating authoring assets from game-export duplicates.
2. Record absolute source path, encoded-file SHA-256, duration, sample rate,
   channels, available authorship/license evidence and intended game cue ID.
3. Preserve original files and existing game playback references. Use a new output
   directory per processing revision. Refuse resume if a source hash changed.
4. Record tool git revisions, dirty state, worker and renderer source hashes,
   model hashes, Python/package versions, sound bank hash and bundled license.
   A git commit alone does not pin a dirty checkout.
5. Register `Config/ArcoreProject.json` in the consumer. Run
   `python tools/ecosystem.py --project <consumer>/Config/ArcoreProject.json`
   from GameCore. This is a file/declaration check only.

Keep song assets, secrets, executable caches and catalog databases outside the
shared workflow repository. Use `Unspecified` for unknown music rights rather than
assigning a sound-library license to the song.

## 2. Separate original audio

Use Alchemist's inference Python and its version-1 JSON-lines worker protocol:

```json
{
  "protocol": 1,
  "action": "separate",
  "model": "htdemucs_6s",
  "input": "C:/Game/Assets/Music/source.mp3",
  "models": "C:/UserData/Alchemist/processing/models",
  "output": "C:/Game/Design/Audio/run-001/stems"
}
```

Pass one JSON line on stdin to `engine/worker.py`, retain stdout/stderr, and require
both a successful process exit and `result.json`. The installed worker verifies
the official checkpoint checksum, probes ROCm tensors/FFT, then performs GPU
inference with six-second windows and overlap-add. It has no silent CPU fallback.

Six-stem output is drums, bass, vocals, guitar, piano and residual Other at
44.1 kHz stereo. Four-stem `htdemucs` remains a useful comparison. Six-stem piano
can contain substantial bleed/artifacts; Other is not a clean string instrument.
Do not infer acoustic/electric guitar identity from the stem name.

Verify each WAV is finite and has the reported frame count, sample rate and
channel count. Record reconstruction RMS of the summed stems against the decoded
mixture. This residual is a mixture-consistency measurement, not a vocal-isolation
or perceptual-quality score.

### GPU cache failure observed in the pilot

The restricted execution attempt reached ROCm but failed with
`miopenStatusInternalError`; its log reported an inaccessible SQLite/kernel-cache
database. A permitted retry outside that filesystem sandbox succeeded. Preserve
the failed log and successful result separately. Do not reinstall drivers or
silently switch models/CPU merely to conceal the failure. In a restricted session,
request the specific required execution permission; do not bypass its boundary.

## 3. Preserve and gently clean vocals

Keep raw `vocals.wav`. Generate a separate candidate through Alchemist Repair Lab's
`gentle_vocal` built-in recipe:

| Stage | Settings |
| --- | --- |
| High-pass filter | 70 Hz |
| Compressor | -18 dB threshold, 2:1 ratio, 10 ms attack, 100 ms release |
| Limiter | -1 dB threshold, 100 ms release |

The pilot adapter calls the existing `repair_lab.effects_render` function on
45-second output chunks with up to two seconds of preceding context, staying
below the Repair Lab's 60-second input limit. Discard only the context from each
processed chunk, preserving source timing and full length. Check joins by listening;
context reduces processor-reset transients but does not prove transparency.

This treatment filters rumble and controls dynamics. It does not claim hiss
removal, de-essing, de-reverb, lyric reconstruction or tuning. The limiter is not
a true-peak guarantee. The pilot found a few clipped samples after limiting, so
recipe version 2 measures the complete float result and applies static attenuation
to a maximum -1 dBFS sample peak before writing PCM. Verify the decoded vocal file
again. Avoid gates that remove quiet syllables and tails.

Optional pitch repair is a separate decision: supply reviewed intended notes,
confirm isolated voice, cross-check pitch and disclose experimental WORLD/Rubber
Band limitations. Never treat detected MIDI as verified target pitches. Do not
resynthesize or tune vocals automatically from this reconstruction workflow.

## 4. Extract editable note candidates

Use `engine/analysis_worker.py` with actions `analyze` on the original and
`transcribe` on individual tonal stems. Requests have `protocol`, `action`,
`input` and `output`; keep `analysis.json`, `transcription.mid` and full worker logs.

The installed transcription engine is Basic Pitch 0.4.0 ONNX on CPU with a pinned
bundled checkpoint. Tempo/key/chord estimates come from librosa/template matching.
Activation strength is not a calibrated probability; template key/chord scores are
not reference truth. Dense accompaniment, doubling and stem bleed produce extra
notes and omissions.

The pilot transcribes bass, guitar, piano and Other separately. It keeps raw notes
and makes a separate render recipe. Render preparation clamps notes to source
duration, removes very short events, ends same-pitch overlaps at the next onset,
and removes bend contours from synthesis. Record these transformations; the
unmodified transcription must remain available.

Drums require their own model or manual work. The pilot's explicitly heuristic
fallback detects independent low/mid/high band onsets and maps them to kick 36,
snare 38 and closed hi-hat 42. It does not identify fills, toms, open hats or cymbal
types. Confidence is recorded as zero, and the output must remain unreviewed.

## 5. Assign instruments and render

Search SoundCore for suitable banks/sample packs and inspect returned license,
source and checksum. If its desktop service is unavailable, an isolated SoundCore
headless service can use a consumer-owned data directory with an ephemeral token.
This is a separate catalog, not an update to the desktop library. Document that
distinction and keep tokens out of logs.

The pilot uses Alchemist's prepared GeneralUser GS bank, retaining its exact bank
hash, manifest and license. Initial GM mappings use electric finger bass (33),
nylon guitar (24), acoustic piano (0), string ensemble (48) for Other, and the
standard percussion bank (128/program 0). These are zero-based program numbers
and provisional arrangements, not recognized source instruments.

The full-length adapter uses RustySynth 1.3.8, the same pinned synthesis engine and
settings as Alchemist: 48 kHz stereo, master volume 0.5, dry output, sample-position
note scheduling and the selected bank/program. It is a consumer adapter, not a
new Alchemist feature. Native Alchemist project reopening must be checked separately.

Export both individual lane MIDI and a multitrack MIDI with instrument programs.
Preserve seconds timing; fixed 120 BPM is an interchange timebase, not a claim
that the recording's tempo is 120. Retain estimated tempo separately and avoid
automatic quantization unless requested and reviewed.

Match each instrument render toward its separated stem's full-track RMS with a
bounded gain adjustment (0.125 through +6 dB linear gain in the pilot). This keeps
saved track gains inside Alchemist's supported range. It is an initial balance,
not loudness mastering.
Mix the reconstructed instruments with the cleaned original vocal. Apply a shared
gain reduction so the instrumental and combined mix remain below -1 dBFS sample
peak. Write 24-bit PCM WAV and measure the actual encoded/decoded deliverables.

## 6. Make useful editable projects

Alchemist holds decoded audio in memory (256 MiB per file and 512 MiB per session
in the inspected version). Muted tracks still consume memory. Avoid putting all
full-length stems, renders and references in one project.

Recommended outputs:

```text
song/
  source.json                    original identity and declared rights
  stems/                         six raw float WAVs, request/result/log
  vocals-clean.wav + .json        cleanup candidate and recipe
  analysis/                      tempo/key/chord proposals
  midi/<lane>/                   raw notes, raw MIDI, render recipe, program MIDI
  reconstruction.mid             all instrument lanes
  <lane>-instrument.wav          full-length instrument render
  instrumental.wav               balanced reconstructed accompaniment
  reconstructed-mix.wav          accompaniment plus cleaned original vocals
  Full-song.arcore               original muted, vocals, stereo instrumental
  Rhythm-and-vocals.arcore        raw vocals, drums and bass
  Harmony-stems.arcore            raw guitar, piano and Other
  sections/01-000s/               48-second editing section
    Editable.arcore              vocals and separate instrument tracks
    compose-pattern.json         editable note/preset recipe
  report.json                    measurements and explicit limitations
  verification-and-catalog.json   actual project reload and SoundCore identities
```

Section projects retain note metadata and composition provenance recognized by
Alchemist's **Edit saved pattern** workflow. Use Compose to change an instrument
or note and rerender layers. Piano-roll MIDI edits alone do not change rendered
audio. Sectioning cuts held notes at boundaries; rerendering a section can reattack
those notes. Full-length renders are scheduled continuously and do not use those
section cuts.

For Compose patterns, shorten each note's duration by one output sample (minimum
one sample). This prevents tiny JSON/floating-point differences from making
adjacent same-pitch notes appear to overlap in the native strict validator. Keep
the original MIDI timing and full-length synthesis unchanged by this pattern-only
adjustment. Verify with the actual native Compose renderer, not just a JSON parser.

Keep media with projects. The pilot's absolute paths reference the consumer's
working copy; they are not a portable embedded project archive.

The native inspection and Compose example sources can be compiled directly against
Alchemist's `arcore-audio` path dependency into the consumer's release build folder.
This avoids stale development binaries and slow debug decoding while exercising
the actual library. Do not modify the sibling source checkout just to build a
consumer verification tool.

## 7. Catalog through SoundCore

1. Call `get_capabilities`; read `soundcore://workflows/publish-derived`.
2. Search existing assets before publishing the bank.
3. Publish originals with truthful rights metadata; publish the bank with its
   bundled license text and source URL.
4. Publish cleaned vocals and reconstruction mixes with parent asset IDs,
   operation recipes, project ID and `not-auditioned` status.
5. Save a dedicated project dependency manifest containing every current asset ID.
   This replaces that named manifest's dependency list; do not reuse another task's
   project ID accidentally.
6. Retain returned IDs, hashes and manifests alongside the consumer outputs.
   A local catalog publication is not an upload to an external service.

Use a persistent desktop catalog only when connected and intentionally selected.
The isolated pilot catalog remains in the consumer workspace after its temporary
server exits. Do not claim those assets appear in the desktop library.

## 8. Acceptance and handoff

Finish with the [timing overlay and scholarly review](quality-review.md): compare
the original and candidate on one timeline, inspect drums independently, export
human notes, and preserve descriptive music-theory metadata. Theory is advisory
and never automatically restricts musical choices. Keep fidelity and creative
intent separate. The same guide documents Quality versus Performance drums.

Record each check as passed, failed, blocked or not_run with exact command and
artifact. Validate each stage before claiming completion:

- Source SHA-256 unchanged after processing.
- All six stems aligned, finite and readable.
- MIDI readable; events in bounds, velocities/programs valid; raw candidates kept.
- Rendered outputs have expected duration/rate/channels and no clipped samples.
- Every `.arcore` project loads through Alchemist's native project loader.
- At least one section rerenders through Alchemist's actual Compose engine.
- SoundCore publication returns real stable IDs and a saved dependency manifest.
- Loudness-matched listening: raw versus cleaned vocal; original versus rebuilt
  backing; vocal-plus-backing mix; quiet syllables, sibilance, transients and joins.
- Manual MIDI correction: melody/bass pitches, chord voicings, rhythm, overlaps,
  instrument identity, drum events, expression and section transitions.
- Game import/playback: cue selection, fades, loop behavior, level and concurrency
  on the named engine/platform; update game references only after acceptance.

Numerical checks cannot establish perceptual fidelity. A complete automated batch
is still an unreviewed reconstruction draft until listening and editing are done.
Keep original soundtrack references operational while evaluating candidates.

## Resume and failure recovery

Resume only stages with successful result artifacts and matching source/tool
identities. Checkpoint existence alone does not validate an interrupted WAV.
Use a new revision when changing recipes/models/banks, or explicitly regenerate
affected outputs and their downstream mixes, projects and catalog versions.
Retain failed logs, distinguish absent output from a silent valid render, and stop
publication if validation fails. Never label a later song successful because an
earlier song passed.
