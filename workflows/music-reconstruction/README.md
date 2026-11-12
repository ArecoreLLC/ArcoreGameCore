# Recorded music → editable instruments: Alchemist handoff

Status: exploratory; applicable to 2D and 3D consumers.

[Sonic Alchemist owns the reconstruction pipeline](https://github.com/ArecoreLLC/ArcoreSonicAlchemist/blob/main/docs/music-reconstruction/README.md):
separation, transcription, song maps, instrument selection, rendering and audio
validation. GameCore coordinates the handoff and game playback acceptance.
Do not duplicate the processing stages or their implementation in GameCore.

## Handoff

1. Record the consumer project, original audio paths/hashes, rights metadata,
   intended cues, and a consumer-owned output directory. Preserve originals.
2. Follow the linked Alchemist pipeline guide to process and review the recording.
   Send source/output locations and the requested continuation stage; Alchemist
   chooses its runtimes and maintains processing details.
3. Receive the selected revision's MIDI/audio/project paths, validation report,
   provenance, listening decisions, unresolved issues and catalog IDs if published.
4. Only integrate approved assets. Verify cue mapping, fades, loops, level and
   concurrency on the actual target engine/platform. Keep existing playback
   references operational until acceptance.

Failed or unauditioned output is a review candidate, not a faithful reproduction
or release-ready soundtrack. A numerical pass is not listening approval.

Use the [worked handoff](example.md), [integration workflow](../game-project-integration/README.md)
and [shared contract](../../shared/migration-contract.md). For connected tooling,
use GameCore's hub and registered system boundaries; this handoff does not add
a downstream MCP connection or a duplicate audio runner.

Detailed [processing](https://github.com/ArecoreLLC/ArcoreSonicAlchemist/blob/main/docs/music-reconstruction/PROCESSING.md),
[quality review](https://github.com/ArecoreLLC/ArcoreSonicAlchemist/blob/main/docs/music-reconstruction/quality-review.md) and
[historical evidence](https://github.com/ArecoreLLC/ArcoreSonicAlchemist/blob/main/docs/music-reconstruction/pilot-evidence.md)
are maintained in Alchemist.
