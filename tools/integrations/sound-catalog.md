# Game-sound catalog reference

SoundCore is a companion project for cataloging game sounds. This reference records that role only; it does not publish private repository contents or assume a live connection.

**Status:** planned integration. No catalog client, audio pipeline or MCP server is implemented by this scaffold.

## Proposed contract

- Resolve a sound by stable asset ID and record its provenance, license and permitted use.
- Discover the actual catalog capabilities before assuming search fields, previews, downloads or MCP tools exist.
- Return a compact record with artifact reference, media format, duration, sample rate/channel information when available, loop/cue metadata and validation warnings.
- Keep game-specific playback rules separate from catalog records. Validate the imported sound in the target engine and platform, including loop boundaries, volume, missing files and suspend/resume behavior where applicable.
- Save full analysis/import logs as artifacts; provide agents with concise results and links instead of repeated binary metadata dumps.

Example acceptance task: select a properly licensed switch sound for the [switch-and-door room](../../workflows/godot-to-unreal/example.md), map the same stable sound ID to each engine's imported asset, and verify one playback per activation without clipping or missing-resource errors. This example is **not_run**.

A unified catalog for sounds, models and textures is an open design option, not a decided repository merger or implemented feature. Coordinate with the [modeling integration](modeling-mcp.md) without assuming a final umbrella name.
