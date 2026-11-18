# Example: one game, three tracks

1. Add `{"id": "example-dungeon", "archetype": "dark-fantasy", "setting": "crypt", "has_music": false}` to `games.json`.
2. Run `python tools/adaptive_music_prompts.py --games workflows/adaptive-music-stems/games.json --out out/music`.
3. Open `out/music/example-dungeon-A.md`; paste the style box and lyrics box into Suno Custom Mode.
4. After listening, split stems and keep `Brass`, `Strings`, `Taiko`, `Timpani` (the `keep_stems` list; `Cello` and `Choir` are optional and non-core).
5. Map sections to states in Sonic Alchemist: `[Intro]`/`[Verse 1]` → explore, `[Pre-Chorus]` → tension, `[Chorus]` → combat, `[Bridge]` → boss, `[Outro]` → resolve.
6. Update `manifest.json` `status` and test transitions on the target engine/platform, then record evidence under the [shared contract](../../shared/migration-contract.md).
