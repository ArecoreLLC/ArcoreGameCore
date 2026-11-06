# Quality kit, timing overlay and scholarly metadata

This extends the [music reconstruction workflow](README.md). Applies to 2D and
3D consumers. Keep song audio and song-specific reports in the consumer project.

## Kit choice

Sonic Alchemist now offers the original synthesized **Performance** kit and a
recorded **Quality** kit in Drum Studio. Stop before switching. Capture to Compose
and save the project to retain the choice. Compose can convert existing built-in
drum lanes or add acoustic articulations. Timing and velocities are preserved.
The Android app's local synthesis is unchanged; connected desktop playback uses
the selected desktop kit. MIDI live pads retain their existing ten-pad mapping.

Quality uses Glen MacArthur's AVL Black Pearl recordings from the official
[AVL plugin repository](https://github.com/x42/avldrums.lv2/tree/master/sf2).
Its five velocity layers are cached as stereo one-shots outside the audio callback.
Playback allows 128 overlapping one-shots, uses a 5 ms hat choke fade and retains
up to eight seconds of sample tail. Captured/offline rendering uses the same
samples and respects hat choking across separate acoustic lanes.

The bundled SF2 and attribution are under `resources/drums/` in Alchemist.
The sample license is CC-BY-SA 3.0 with the upstream exception for produced music;
retain the upstream notice when distributing the library. No LV2 plugin code was
copied. The sampler code uses the existing RustySynth dependency.

Limitations: no round-robin alternation, pedal openness controller, brush kit,
multi-microphone mixer, or streaming. Black Pearl has two recorded toms; three
desktop tom pads share those recordings. Additional pieces are available in
Compose, while live MIDI/tablet input still maps to the ten established pads.
Quality first use warms the cache; it is not loaded during a hit. Maximum decoded
cache before silence trimming is about 337 MiB. Live mode defaults to Performance
on a new session; saved Compose recipes retain Quality. Older Alchemist versions
do not understand the new acoustic recipe sound kind.

## Final overlay validation

Passing technical checks does not establish musical timing accuracy. Voice-limit
comparisons rule out a particular playback failure; onset correlation is a
coarse, timbre-dependent proxy. Missing hits, wrong notes, shortened articulation,
vocal separation residue and original expressive phrasing can still sound wrong.
Do not attribute mismatch to AI vocals without comparing the original, raw vocal,
cleaned vocal and reconstructed backing independently.

The reconstruction mix default is now **-3 dB for cleaned vocals relative to the
backing balance**. Apply it consistently to exported mixes and saved vocal-track
gains; keep the cleaned stem itself unchanged and record `vocalGainDb`. This is a
consumer reconstruction preference, not a global gain change for imported audio.
When revising a review mix, retain its backing/master gain so normalization does
not undo the comparison. Export a new version and retain the prior mix.

After each reconstruction revision:

1. Verify the source hash. Decode the original MP3 and the exported candidate onto
   the same seconds timeline; keep both original time origins. Do not silently
   align, stretch, quantize or trim to make the plots agree.
2. Overlay peak envelopes, with explicit normalization controls, zoom and seek.
   Display the resolution. Compare full mix and separated drums independently.
   Provide A/B listening at matching timeline positions and an export for notes.
3. Compare onset-envelope lag in local windows as well as across the full track.
   Report lag sign, window length, search range, correlation, method and caveats.
   Low correlation or inconsistent offsets request listening; they are not proof
   of incorrect performance. Reused vocals can inflate full-mix agreement.
4. Review attacks, sustained notes, fills, cymbals, joins and transitions by ear.
   Keep fidelity notes separate from deliberate creative departures.
5. Export notes, source/candidate hashes and tool identities. Keep the candidate
   labelled unreviewed until the musician accepts it. A working overlay is not a
   passed listening test.

The consumer implementation uses ~5 ms envelopes and 20-second onset-correlation
windows, searching ±197 ms at 11.61 ms resolution. These are review heuristics,
not universal musical timing tolerances. Browser A/B playback is not a
sample-accurate null-test engine. Standalone review packages carry MP3 listening
proxies; the full-resolution native WAVs remain the measurement source where
specified. Review proxies and envelope source identities must be documented.

## Scholarly metadata: advisory, never a creative gate

Use `arcore.music-theory-review.v1` for per-song descriptive records:

- Source identity/hash and the analysis artifact, implementation and tool version.
- Tempo candidate and beat times; retain half/double-time ambiguity and distinguish
  interval regularity from confidence. Meter may be unknown.
- Key candidate with the actual fit metric, not a probability. Global major/minor
  profiles can miss modulation, modes and other musical traditions.
- Time-stamped chord proposals, vocabulary and score semantics. Triad matching
  does not determine inversions, extended chords or harmonic function.
- Rhythm observations, source references, musician corrections and creative intent.
- Separate fidelity observations, theoretical interpretation and artist decisions.
- `policy.mode="advisory"`, `blocking=false`, `autoCorrect=false`. Never reject,
  reroute, quantize or reharmonize because a theoretical convention is not met.

Each observation should cite a reference ID and explain the method's applicability.
Use null for unsupported confidence or unestimated meter, rather than fabricating
certainty. A 4/4 interchange scaffold is not evidence of the source's meter.
Ask whether the musical effect is intentional before suggesting changes.

Reference catalog (`arcore.music-theory-sources.v1`):

- [Ellis, Beat Tracking by Dynamic Programming (2007)](https://www.ee.columbia.edu/~dpwe/pubs/Ellis07-beattrack.pdf):
  method context for beat tracking and its tempo assumptions.
- [Krumhansl, Cognitive Foundations of Musical Pitch (2001 edition)](https://academic.oup.com/book/40395):
  tonal hierarchy context; the local implementation's profile correlation remains
  an estimate, not a general theory of musical correctness.
- [Müller, FMP: Template-Based Chord Recognition](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C5/C5S2_ChordRec_Templates.html):
  chroma template methodology and vocabulary limitations.
- [Open Music Theory: Syncopation in pop/rock music](https://openmusictheory.github.io/syncopation.html):
  off-beat placement can be structural and intentional.

Store references with title, author, URL, edition/year when known, and the precise
scope of use. This reference layer informs review; it never claims scholarship
has certified a generated song.

## Repeated patterns and hybrid support

Before using a fixed quantization grid, measure whole-track and local tempo on
the original recording and corroborate it with separated drums/bass. Keep
half/double-time ambiguity, uncertain intros and unverified downbeats explicit.
The Shanty pilot's local estimates agreed around 130–132 BPM early, around
137–140 BPM later and approximately 142 BPM near the end, despite whole-track
estimates near 136–139 BPM. A single global number hid that pacing change.
Twenty-second windows summarize observations, not exact tempo-change boundaries.
Retain the original time axis and derive a reviewed beat/tempo map before nudging.
Do not change the 120 BPM interchange recipe directly: its beat positions encode
seconds and would need remapping to avoid rescaling audio. Detection alone must
not modify notes. The consumer stores `tempo-review/tempo-analysis.json`,
`tempo-map-proposals.json` and `TEMPO-REVIEW.md` alongside the source-song outputs.

Use the source beat map to compare recurring phrases rather than assuming every
bar is identical. Compare both harmonic and rhythmic features, reject overlapping
self-matches, suppress shifted duplicates, and retain time ranges, source hashes,
scores and method limitations. Musical structure comparisons can use
[feature self-similarity](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C4/C4S2_SSM.html).
Local thresholds are review heuristics, not calibrated confidence. Estimated
beats are not confirmed downbeats; never silently label an analysis window a bar.

The consumer pilot searches 8/16/32-beat phrases using chroma from original
bass/guitar/piano and three-band drum onsets, sampled at eight bins per estimated
beat. It found twelve candidate repeat pairs in a 210-second source, including
eight- and sixteen-beat motifs. It compares reconstructed hits across occurrences
to identify possible timing inconsistencies. No candidate is automatically copied,
quantized or substituted; verify fills, boundaries and musical intent by listening.

For a hybrid candidate, preserve original stem positions and add only a quiet,
explicitly documented support bed. The pilot adds original bass/guitar/piano at
-15 dB and drums at -21 dB, relative to source-stem level at the parent master.
It retains -3 dB vocals and saves the bed separately. Exclude the full original
mix to avoid deliberately adding a second vocal; separation bleed is still possible.
Check doubled attacks, bass phase coloration, clipping and perceived loudness.
Improvement from reused source material must not be reported as better transcription.
Record the difference from the prior mix and retain both versions for A/B review.

## Extending quality beyond drums

Inventory installed formats before acquiring more samples. The current Alchemist
evaluation libraries already include playable Salamander, YDP Grand and Upright
KW SF2 pianos. Bass, guitar and orchestral SFZ libraries are downloaded but need
an SFZ backend. A discovered library is not automatically a playable instrument.
Evaluate streaming, round robin, includes, release triggers and controller support
with each mapping; do not flatten expressive libraries to one-shot playback.

The Salamander SF2 conversion omits pedal/hammer/string-release noises and
amp_veltrack from the original SFZ design. Preserve those limitations and its
CC BY 3.0 attribution. Black and Blue Basses, Emilyguitar and VSCO CE are candidates
for a later SFZ integration; instrument identity and articulation still require
review. Select an instrument per part rather than treating every residual stem
as generic strings. The consumer's `INSTRUMENT-UPGRADES.md` records file sizes,
availability, official references and prioritized next steps.
