# Example: hand off one recorded game theme

A Windows Godot 3D consumer wants editable accompaniment while preserving the
recorded vocal. The consumer retains the original and supplies truthful rights
metadata, its cue ID, source hash and a new output directory.

1. Check the consumer declarations using the [integration workflow](../game-project-integration/README.md).
2. Hand the source and output locations to [Sonic Alchemist's pipeline](https://github.com/ArecoreLLC/ArcoreSonicAlchemist/blob/main/docs/music-reconstruction/README.md).
3. Review Alchemist's resulting MIDI/audio, validation and listening evidence.
   Keep failures and manual corrections visible; do not infer approval from a render.
4. Import an approved candidate into the consumer and test the cue, fades, loop
   behavior, level and concurrency on the named engine/platform.
5. Record the accepted revision and playback evidence under the
   [shared contract](../../shared/migration-contract.md).

Audio-processing details, native editability checks, and optional SoundCore
publication are owned by Alchemist. GameCore does not repeat that stage list.
