# Characters dancing to the music

Make characters hop, squash and swing their limbs on the beat of whatever song is playing, and stomp up dust, tap drums or play footsteps on each landing.

A small pipeline in the [ambient-world-life](../ambient-world-life/README.md) family. Its Godot component is
[`beat_dance.gd`](../../3d/godot/world_life/beat_dance.gd) (Node (child of the dancer)), vendored with the world-life kit:
`python tools/game_music_video.py vendor --module world-life --project <game project>`. See the [example](example.md).

## Pipeline

| # | Step | Detail |
|---|---|---|
| 0 | Vendor | Install the world-life module (kit and components) with a SHA-256 lock per file; don't edit the vendored copies |
| 1 | Beat map | `tools/song_beats.py --song id=path … --out <game>/song_beats.gd` writes each song's tempo and first-beat offset (a GDScript constant always exports). |
| 2 | Beat clock | The game's root node calls `KIT.set_beat(BEATS, song_id, song_seconds)` every frame. In music videos the recorder adapter's `_beat_clock(t)` calls `KIT.song_clock(id, t)` so dances follow the video. |
| 3 | Dancers | Add `beat_dance.gd` under each dancer: `body`, optional `limbs` (arms then legs), `hop_height`, `beats_per_hop`, and `phase_offset` to stagger a group. |
| 4 | Stomps | Connect `stomped(at)` to dust puffs, drum taps (`KIT.tone`) or footsteps. |
| 5 | Test and review | A headless test drives the component on a fixed clock; the requester reviews it in play or in a [showcase](../game-asset-showcase/README.md) shot |

## Component

`body`, `limbs`, `hop_height`, `squash`, `swing`, `beats_per_hop`, `phase_offset`, `enabled`; `set_rest(position)`; signal `stomped(at)`; reads `KIT.beat_phase`, `KIT.on_beat`.

The world contract, clock and helpers are in the [world-life kit README](../../3d/godot/world_life/README.md). The
component is exercised by `3d/godot/world_life/tests/components_test.gd` (`tools/tests/test_world_life_godot.py`,
run with `$GODOT` set).

## Checks

| Check | Kind |
|---|---|
| Landings coincide with the song's beat (watch with sound) | human |
| Stomp signal fires once per hop | automatic |

## Known limits

- Assumes a steady tempo per song; a song that changes tempo needs sections in the table.
