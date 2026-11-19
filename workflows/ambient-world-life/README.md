# Add ambient world life to a game

A world can work and still feel deserted. This workflow takes a game from that note to a set of small, reusable
ambient systems: creatures, weather, props and close-up behaviour that make every shot feel inhabited. It runs
from review to backlog, then build, staging hooks, tests, a frame-cost check and a showcase.

It was derived from the ShammyVerse world-life work (see [example](example.md)). The Godot runtime is the
[world-life kit](../../3d/godot/world_life/README.md); the beat map is [`tools/song_beats.py`](../../tools/song_beats.py);
the showcase is the [game-asset-showcase workflow](../game-asset-showcase/README.md).

## Ownership

| Owner | Responsibility |
|---|---|
| GameCore | This workflow, the world-life kit, the beat-map tool and the staging hooks in the [music-video recorder](../../3d/godot/music_video/README.md) |
| The game | Its world contract (`height_at`, optionally `wave_at`), the root node and every module (which creatures, where, when), its tests and its showcase shots |
| Requester | The backlog priorities, spoiler policy and the final look |

## Pipeline

| # | Stage | Done when |
|---|---|---|
| 1 | Review | Footage (music videos, playthroughs) and lyrics or story text are reviewed. Held shots with empty backgrounds and promised-but-absent moments are counted |
| 2 | Backlog | A list of reusable assets, grouped (sea, sky, shores, close-ups, interiors, pipeline). Each item has what it does, what it reuses, the lyric or story line it brings to life, and an effort size |
| 3 | Vendor | `tools/game_music_video.py vendor --module world-life` installs the kit with a lock |
| 4 | Root and contract | The game's root node advances `KIT.time`, sets the beat clock and the effects volume, owns the modules and forwards quality |
| 5 | Build | Modules built on the kit, near-camera and nonblocking, each with `stage(kind)` and `set_quality()` |
| 6 | Beat map | `tools/song_beats.py` writes each song's tempo and first-beat offset; dances, drums and stomps follow it |
| 7 | Character attention | Characters glance at `KIT.ping` events and rest between glances; idle fidgets and visitors for still shots |
| 8 | Test | A headless test builds every module, exercises every `stage()`, and checks attention, night and quality levels. Earlier tests are rerun with the systems switched off (an environment switch) to separate old failures from new ones |
| 9 | Frame cost | Windowed, vsync off: frame time with and without the systems at the busiest spot |
| 10 | Showcase | One titled 6.5 s shot per asset ([game-asset-showcase](../game-asset-showcase/README.md)): screenshots while building, then a demo video |
| 11 | Recorder hooks | The game's music-video adapter answers `_stage_ambient("still" / "beat" / "lyric:<kind>")` and `_beat_clock()` |

## Backlog rules (from the ShammyVerse review)

- **Start from the shots where nothing moves.** Count the held shots (close-ups, gazes) and look at what is behind the
  character. In ShammyVerse 26 held shots faced an empty sea, so the sea came first.
- **Mine the lyrics.** Each line that names a creature, a place or an action the game never shows is a candidate:
  "pretzel fish leapt and flipped beside the dock", "with bubble crowns and stomping feet".
- **Leave out future story.** Moments saved for a later chapter (a reunion, a party) stay out, so the ambient
  layer gives nothing away.
- **Reuse before modelling.** Use the game's own models first, then the asset library, then primitives baked with
  `KIT.merge` (bears, puffers, kites, lanterns). Synthesise simple sounds with `KIT.tone`.

## Build rules

- One module per family, with species, counts, paths and timing as parameters.
- Pool everything; spawn near the camera; hide distant life; no shadows on small animals; use visibility ranges.
- Transparent effects on a transparent sea need `render_priority` above the water's.
- Attention pings should be occasional and the characters should rest between glances. A constant stream of pings
  pins the hero's head.
- Forced states for scripted shots (snow, streaks, wind) end on their own or through `stage("clear")`.
- A day/night toggle is a design decision. Expose it (a key, `set_mode()`) rather than adding a cycle unasked.

## Checks

| Check | How |
|---|---|
| Builds and runs | Headless test: every module present, counts as expected, no script errors through day, dusk and night at quality 0–2 |
| Staging | Every `stage(kind)` returns true where the world allows it, and the event is visible in a showcase shot |
| Attention | A ping in front turns the head; it rests after a glance |
| Regressions | Earlier tests pass; failures that also occur with the systems off are recorded as pre-existing |
| Cost | Windowed frame time on and off, recorded with the hardware; low quality trims the costly parts |
| Look | Showcase screenshots and the demo video reviewed by the requester |

## Known limits

- The kit assumes a Godot 4 Forward+ project and the world contract above.
- Decal-based cloud shadows skip a transparent sea.
- Beat maps assume a steady tempo; songs that change tempo need sections in the table.
