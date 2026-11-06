# Worked example: one recorded game theme

This is a generic procedure. Original music and game-specific scripts remain in
the consumer repository. The local pilot and its measured results are described
in [pilot evidence](pilot-evidence.md); that record must not be read as listening
approval for this example.

## Inputs and first slice

An approximately three-minute stereo MP3 theme in a Windows Godot 3D consumer.
The objective is to preserve its singing while making the accompaniment editable.
The consumer supplies music rights metadata; if unavailable it stays Unspecified.

Inspect the installed Alchemist runtimes, pinned six-stem model, GeneralUser bank
and available SoundCore endpoint. Select the
[music reconstruction guide](README.md), then the [3D catalog](../../3d/README.md).
Freeze source hashes and record engine declarations/tool versions.

## Sequence

1. Run GameCore's consumer dependency checker and retain its JSON output.
2. Separate the entire recording into six aligned stems with Alchemist's worker.
3. Produce a gentle vocal-cleanup candidate, preserving the raw vocal and timing.
4. Analyze the original tempo/key and transcribe the four tonal stems separately.
5. Build separately labelled drum candidates; keep unreviewed status.
6. Export program-assigned MIDI and render the selected SF2 instruments.
7. Balance against stem RMS, combine with the cleaned vocal and apply sample-peak
   headroom. Export full-song instrumental and vocal mix.
8. Save a lightweight full-song project and 48-second editable section projects.
9. Reopen every project natively; rerender a representative section with Compose.
10. Publish source, bank and derived assets to the chosen SoundCore catalog with
    parent relationships, license text, recipes and a dedicated project manifest.
11. Audition and correct a representative verse and chorus before integrating the
    candidate into the game. Expand listening to the complete recording.
12. Generate the final [timing overlay and scholarly metadata](quality-review.md).
    Compare against the original recording without hidden alignment. Retain
    manual notes and creative exceptions; theory never rejects a candidate.

## Expected evidence

| Check | Required evidence |
| --- | --- |
| Tool identity | Revisions, dirty state, code/model/bank hashes |
| Separation | Successful worker log, six aligned WAVs, result.json |
| Cleanup | Raw and processed vocals, exact recipe and frame counts |
| MIDI | Raw transcription, edited render notes, instrument/program mapping |
| Rendering | Readable full-length WAVs, finite PCM, duration and clipping checks |
| Editability | Native project reload logs and successful Compose rerender |
| SoundCore | Capabilities, actual asset IDs, parent graph and project manifest |
| Sound quality | Named reviewer, comparison excerpts, findings and revisions |
| Game playback | Engine/platform, cue mapping and recorded playback checks |

Until the last two rows are supported, report “rendered reconstruction draft”
rather than “faithful reproduction” or “production ready.”
