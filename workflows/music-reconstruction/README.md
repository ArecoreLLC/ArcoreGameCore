# Reconstruct recorded music as editable vocals and instruments

Status: exploratory. This workflow produces auditionable reconstruction drafts;
it does not establish faithful transcription, transparent vocal repair, or a
production-ready game soundtrack. Applicable to 2D and 3D consumers.

See the [2026-11-09 maintenance review](review-2026-11-09.md) for current
validation limits, implementation gaps and prioritized improvements. Historical
pilot results do not certify later revisions. A batch must return a failing exit
status for validation failures as well as processing exceptions; an empty batch
must not be reported as successful.

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

### Timing and note-loss pitfalls (measured in the second pilot pass)

The first pass sounded slightly behind the beat and missed notes. Each cause was
measured per lane against the separated stem (onsets at ~1.5 ms resolution, matched
within 50 ms):

- **Causal band filters delay drums.** `scipy.signal.sosfilt` on 4th-order band-pass
  filters adds group delay, most in the kick band. Use zero-phase `sosfiltfilt`.
- **Onset-strength peaks are late.** Report the backtracked energy rise, not the
  flux peak. Detect with a ~46 ms window (a ~23 ms window produced many false hits),
  then snap each event to the nearest precise stem attack. Together these moved
  drums from +17 ms late to ~0 ms with a 90th-percentile error near 3 ms.
- **Basic Pitch's defaults drop short notes.** `predict()` defaults to a 127.7 ms
  minimum note length, longer than a 120 BPM sixteenth. Default thresholds also add
  false notes. Run inference once, then score a small grid of onset threshold, frame
  threshold and minimum length against the stem's own onsets per song and lane; no
  single setting won across songs or lanes.
- **Frame-quantized note starts.** Basic Pitch starts land on an 11.6 ms grid. Snap
  each note start to a stem attack within ~35 ms; keep notes without one unchanged.
- **Presets speak late.** Measure each preset's attack delay per pitch (time to 25% of
  peak RMS after note-on) and start notes that much earlier, capped (80 ms in the pilot).
- **Bleed-only stems add wrong instruments.** Six-stem guitar/piano can sit 20–35 dB
  below the other stems. Transcribing them renders hundreds of notes from bleed.
  Gate lanes by stem level relative to the sum of stems (−24 dB in the pilot); render
  them for review but leave them out of the mix.

### Double hits (found by listening to the third pass)

- **Independent drum bands stack.** Kick, snare and hat band detectors each fire on the
  same hit (a snare's low end triggers the kick band, its noise the hat band), giving
  2–3 drums per real attack, sometimes a few ms apart (flams). Detect each attack once on
  the full drum stem, then classify it by how much each band rises relative to that
  band's typical hit; add a second drum only when its band also rises strongly. All
  drums of one attack share one start time.
- **Drum bleed becomes pitched notes.** Remove pitched notes that start on a drum attack
  with no attack in their own stem, and merge same-pitch retriggers within 90 ms.
- **Mono/legato SFZ instruments slide.** Overlapping notes on a mono bass glide instead
  of re-attacking; end each note just before the next when rendering such libraries.
- **Measure compensation with the checks' own onset definition, in context.** Use the
  same backtracked onset detector the timing checks use, but calibrate each pitch inside a
  short line (0.4 s notes, 40 ms gaps, neighbouring pitches), not on one note in silence.
  Fingered-bass samples start with a faint click ~2 ms after note-on and swell in ~22 ms
  later. In silence the detector finds the click, so compensation was ~2 ms; in a real line
  the previous note masks the click and every note was heard ~22 ms late. This caused five
  songs' bass failures in revision 6. Rendering a known line (the remix renderer, whose note
  times are exact) is the quickest way to isolate this: compare its detected attacks with
  the planned starts, and subtract a two-note render from the first note alone to rule out
  voice interaction.

### Wrong-timed hits on struck instruments (found by listening to the fifth pass)

- **Transcribers turn blur into note-ons.** 42–57% of a marimba part's notes had no
  attack within 50 ms in the source stem; timing checks missed it because offsets are
  measured only on notes that match. Classify each sound once as percussive or sustained
  (decay of more than 9 dB between 0.3 s and 1.3 s after the attack). Percussive sounds
  only play notes that have a source attack within 35 ms; sustained sounds keep every
  note, because a soft entry doesn't read as a wrong hit.
- **Detect pitched attacks inside each lane's own range.** Broadband spectral flux barely
  registers low plucks (a whole bass stem gave 53 attacks). Use bass 30–500 Hz,
  guitar 80–5000 Hz, piano 30–8000 Hz and other 60–8000 Hz.
- **Don't let timbre win on its own.** A candidate whose onset F1 is under half the best
  candidate's is not eligible, however similar it sounds.
- **Legato sources have few attacks.** For sustained sounds, the share of notes without a
  source attack is recorded but not graded, since smooth bass lines change notes without
  new attacks.

### Validation gate

Run an automatic validator on every song of every revision before anyone listens, record
pass/warn/fail with value and limit, and do not export failing songs for review. The
ShammyVerse pilot's `validate_reconstruction.py` checks drum hits per attack, flams, drum
and pitched retriggers, drum bleed in pitched lanes, per-lane median and 90th-percentile
attack offsets, and doubled attacks in the rendered instrumental versus the original
stems. Revision 3 (the first pass with stacked drums) failed on all 11 songs; record such
failures rather than tuning limits to pass. Passing is a precondition for listening, not
a substitute for it.

Report recall, precision, F1 and median/90th-percentile offset per lane for every
revision, alongside the previous revision. Onset matching against separated stems is a
consistent proxy, not ground truth, and does not replace listening.

**Before fixing a timing fail, check it with a second, independent measure.** One guitar
failed as "10 ms early" for two revisions while its render played its notes within 0.01 ms.
The grade came from a broadband onset detector. On that separated guitar stem it found only
34 attacks, placed 8.7 ms after the attacks in the guitar's own frequency range. Measured
in the guitar's own range, the render was 0.0 ms from the stem over 87 pairs. A
detector-free check agreed: the time each note's envelope reaches half its rise was 0.5 ms
apart. Grade pitched timing with attacks in the lane's own range, the same family of
detector that placed the notes, and keep the broadband figure as information. This changes
the measurement, not the limits. Do not move notes to satisfy a detector that disagrees with
two others.

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

Fixed per-stem assignments were a major source of wrong-sounding parts (for example
strings on a percussive Other stem, whose slow swell also blurs timing). The second
pass renders a short candidate list per lane and keeps the preset whose output best
matches the stem (onset F1 plus mean log-mel spectral similarity), recording every
candidate's scores. That is a measured proposal, not instrument recognition; a
musician still decides.

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

### Missing soundscape (found by listening to the seventh pass)

Fixing timing by dropping notes can empty the mix. Measure coverage, not just timing.

- **A support filter must not delete held parts.** The "other" stem carried 60-92% of the
  500 Hz-6 kHz energy. Played on a struck sound that keeps only attacked notes, 54-80% of the
  part disappeared. Render the dropped notes with a second, sustained sound (chosen by timbre
  on those notes), and fit both layers' gains to the stem's band envelopes together.
- **One detection per broadband attack misses quiet hi-hats.** In Captain Poofy, 371 attacks
  covered about 500 beats, and the top end was 12 dB low 58-66% of the time. Detect hats in the
  5-16 kHz band, keep 70 ms between hats, and count drums stacked per hit time rather than per
  broadband attack.
- **Gate coverage.** For each band, record the share of the original's active time where the
  render is more than 12 dB quieter, and the band's level difference after matching overall
  level. In revision 8 this took Captain Poofy's worst band from a 64% gap to 28%.
- **Default the vocal well below the backing.** Listening asked for 30% lower than −3 dB
  (−6.1 dB). Set remix part levels against the vocal at unity, so the default changes the balance.

### Missing drum beats (found by listening to the eighth pass)

- **The double-hit guard went too far.** Detecting each attack once and adding a second drum only
  on a very strong band rise (the revision 5 guard against stacked hits) dropped most kicks under a
  hi-hat or snare. Only 26-39% of the source's kick hits were played in two songs, although 95% of
  broadband attacks had some drum. Detect kick, snare and hat attacks in their own bands, merge
  them with broadband attacks into shared hit times (30 ms), and play a drum where its own band
  attacks.
- **Grade each drum on recall and precision, not drums per attack.** Recall is the share of the
  source's strong hits in that drum's band that are played; precision is the share of played hits
  with an attack in that band (leakage). Real kick+hat hits make about two drums per hit legitimate.
  In the pilot this took kick recall to 86-99% with precision of 84% or more.

### Rough-sounding parts and missing toms (found by listening to the ninth pass)

- **Measure the MIDI, not only the audio.** "Still a bit rough" turned out to be chord notes
  starting 5-45 ms apart: the transcriber staggers the notes of one chord, and a struck or strummed
  sound renders each as its own attack (a flam). 12-32% of guitar and "other" onsets were such
  doubles in every pilot song. Grade doubles per part (lane plus bed): warn above 3%, fail above 8%.
- **Align chord onsets after moving notes to their stem's attacks.** Note starts within 45 ms in one
  part become one onset, the one sitting on an attack of the part's own stem, else the earliest. Then
  merge same-pitch retriggers again, because alignment can bring two re-strikes closer together.
- **Don't snap everything to the drums.** The original playing was itself loose against the drums
  (most bass and guitar attacks near a drum hit were 8-45 ms off it). Moving notes with no attack of
  their own onto drum hits also made them look like drum bleed. Record looseness against the drums
  (render and source side by side) without grading it.
- **Toms need their own detector.** A tom's low end fires the kick band and its overtones the snare
  band, so per-band kick/snare/hat detection never produces a tom. Treat a hit as a tom when the
  drum stem has a tonal 85-300 Hz peak, louder than 35-85 Hz, that starts at the hit and keeps
  ringing, with little snare noise, and when the bass stem isn't louder at that pitch (bass bleed).
  Pick the pad from the peak pitch. Keep the snare at a tom hit, and drop the kick only when the low
  end is clearly the tom's: replacing both cut snare recall to 64-75% in two pilot songs. A
  non-commercial drum transcriber is acceptable only as a rough local reference while tuning.

### Phantom parts (found by listening to the tenth pass)

- **Check for sound the original doesn't have, not only sound it lacks.** Problems heard "around one
  minute" were a bass rendered through a section where the bass stem was silent (22 dB too loud) and
  a near-empty guitar stem rendered as a full part. Coverage checks only catch missing sound. Grade
  each part on the share of its audible time where it is more than 12 dB louder than its stem: in
  the pilot this was 8-76% for bass before the fix.
- **Gate notes on their stem's level and let velocity follow it.** Transcribers find notes in
  separation residue. Drop a note when its stem is more than 24 dB below that stem's loud level, and
  scale the rest by the stem's local level instead of one gain per song.
- **Distortion isn't always the culprit.** Before changing attack detection for a distorted part,
  check the stem's level and whether its attacks fall on the beat grid more than chance: a stem far
  quieter than the others with attacks at chance is residue, not a part.
- **The hybrid mix hides lane errors.** It swaps in the original drums and bass, so judge rendered
  lanes on the fully rendered mix.

### Song map from the full mix

- **Measure the whole song before the stems.** A tempo map, feel, downbeats, sections, key and a
  chord per bar come out better from the full mix (and the backing stems for chords) than from any
  one stem. Use them as constraints and checks, never as a source of notes.
- **Tempo is not constant.** One pilot song sped up from about 138 to 151 BPM; a fixed-tempo MIDI
  export drifted by bars. Write the tempo map into MIDI and check every note reads back within 1 ms.
- **Detect the feel before using a grid.** Drum attacks sat on straight 8ths 77-92% of the time in
  most songs, but one song scored 35% on 8ths and 70% on triplets. Pick the subdivision whose grid
  holds the most drum attacks beyond chance.
- **Use a full-mix transcription as a vote, combined with other evidence.** It confirmed 63-88% of
  stem notes against 21-53% by chance, but alone it did not separate good notes from residue. Drop
  only notes with no evidence at all: no full-mix vote, not a chord tone, no own-stem attack (0-9%
  of a part).
- **Compare against the original song as well as the stem sum.** The stem sum already lost what
  separation dropped.
- **Ride each rendered part's level against its stem.** Velocity scaling assumed loudness follows
  velocity squared; sampled basses have a much narrower range, so quiet notes stayed too loud. Turn a
  part down wherever it exceeds its stem by more than 6 dB, with the level constant from one heard
  attack to the next and changes fading in on the attack itself. A gain ramp across an attack
  reshapes it, and a rise placed at the MIDI note-on (earlier than the heard attack by the sample's
  attack delay) is detected as an attack of its own.
- **Close the timing loop after rendering.** A calibration that is cached per run gave the same bass
  ~27 ms of compensation in one run and 3-26 ms in another. Measure the rendered attacks against the
  heard notes per pitch, correct, re-render once, and re-measure anything computed from the old render.
- **Grade nothing on a handful of matches.** A source-vs-render timing check built on one or two
  matched attacks flipped from 0 to 30 ms with no change in the notes; record it below 10 pairs.
- **A rough vocal split can still place the vocal.** Lead + backing sum to the original, so the lead
  can sit centred with the backing widened (a 12 ms inter-channel delay costs about 3 dB of backing
  in a mono sum) even when neither part is usable alone.

### Original remix mode (optional)

Instead of reconstructing the backing, compose a new one around the unchanged vocal. The
detected notes and instruments serve only as inspiration. The reference implementation is
Alchemist `engine/remix.py` for theory, composition, fit checks and export, with
ShammyVerse `remix_v1.py` for rendering and the timing gate. Lessons from the pilot:

- **Fix the beat grid before composing.** Frame-based beat trackers report onset-envelope
  peaks; one song's beats sat 48 ms after the drum hits, so every new part would land
  late. Move each beat onto the nearest drum-stem attack within 80 ms, median-smooth the
  shifts, and confirm the drum attacks then sit on the eighth-note grid (95% within 35 ms
  in the pilot) and the vocal attacks well above chance (66% against 34%).
- **Judge pitch on stable sung notes.** pYIN frames include glides and scoops between
  notes; counting them made a quarter of the song look like clashes.
- **Make composition vocal-aware.** Choose every bass, chord and arpeggio note against
  what is sung at that moment. Leave out or swap tones a semitone away (a tritone, for the
  bass), split held chords and bass around the melody, keep voicings below or above the
  local vocal range, and play counter-melodies only in vocal rests. This took Captain
  Poofy from 26% clashes and 39% range overlap to passing in pop, ballad and orchestral
  styles.
- **Follow the song's harmony; be original in the arrangement.** Melody-only
  re-harmonisation passed every fit check, yet listening found it poorly matched to the
  vocals. It agreed with the original backing's chords on only 25-51% of sung bars and changed
  chord about twice as often. Use the backing's bass-weighted chroma per bar as a strong prior
  and keep its harmonic rhythm. Check the analysis key against the backing's pitch set: one
  song detected as G major was C major. Gate agreement with the backing (60% warn, 40% fail
  when following) and the chord-change ratio.
- **Gate the remix like a reconstruction, plus fit checks.** The fit checks are sung
  chord-tone share, clashes, range overlap, counter-melody overlap and vocal on the grid.
  Rendered attacks against planned starts use the same limits as the reconstruction.
  Because remix note times are exact, sustained parts are graded too.

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
- Validation gate passes (no fails) for every exported song: drum hits per attack, flams,
  retriggers, drum bleed in pitched lanes, attack offsets and doubled mix attacks.
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
