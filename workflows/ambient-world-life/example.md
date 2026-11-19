# Worked example: ShammyVerse world life (November 2026)

The first run of this workflow. ShammyVerse (Godot 4.7.2) had ten gameplay music videos that the owner liked, but
said the world felt deserted. The game's code and design logs stay in the ShammyVerse repository
(`Design/Environment/WORLD_LIFE_ASSET_LIST.md`, `Design/Iterations/world-life-v001/DESIGN_LOG.md`). This page
records the process, decisions and lessons.

## Review and backlog

- The music-video recorder held Poofy still in 26 shots (15 close-ups, 11 gazes), about 5 minutes across the album,
  nearly all with open sea behind him. None of the 17 sailing shots had anything near the ship.
- The existing wildlife was small (a 0.52 m dolphin model), underwater, or tied to one beach patch.
- The lyrics promised pretzel fish by the dock, puffers bobbing in rows, gumdrop bears dancing, lantern bugs and
  bubbles.
- Backlog v001 had 59 items in six groups: sea and ship, sky, shores, close-ups, caves/canyon/night, pipeline. A second
  backlog came from comparing the lyrics with the game's song-to-story review: 12 more items, plus lyric-cued
  staging.

## What was built

| Group | Examples |
|---|---|
| Sea and ship | Dolphin escort and passing pods; leaping pretzel fish; wake and bow spray; gulls trailing the ship; a distant whale; puffer flotillas; candy sailboats; a manta; turtles; night-glowing jellyfish |
| Sky | Flocks, parrots between palms, soap bubbles, cloud-shadow decals, peppermint ribbons, marshmallow snow, a rainbow, kites, sun glints |
| Shores | Gumdrop-bear villagers, a puffer drum circle, animated shoreline foam, crab parades, gulls on dock posts, lanterns, bunting, campfire smoke, shell chimes with a synthesised tone, tide pools, pier fishers |
| Close-ups | Poofy and Plumpy glance at pings; idle fidgets; visitors (a butterfly on the snout, a bubble sneeze, a gull, a crab); petals near the camera |
| Caves, canyon, night | Fireflies, light shafts, drips, baby spiders, steam vents, wobbling gumdrops, Day/Dusk/Night (F5) with moon and stars |
| Lyric batch | Singing Stones (pentatonic notes and a chord), the Teacup party set (beat-synced drums, a gummy dragon on a leaf slide), bubble crowns and stomps, peppermint wind lanes that boost the ship, a candy armada and confetti salutes, dock chatter, Plumpy's spark sneeze, friends practising |

No new model or texture files: the game's models, the ModelForge library's own dolphin, and primitives baked
with `KIT.merge`.

## Decisions

- The game is the priority; the music videos use the systems through recorder hooks, not the other way round.
- Night is a player toggle and a scripted mode, not a cycle. Adding a cycle is the owner's call.
- The Shampoo Island reunion and party stay out: they belong to a future chapter.
- A JSON beat table was swapped for a generated GDScript constant, so it always exports.

## Commands

```powershell
python tools/game_music_video.py vendor --module world-life --project game
python tools/song_beats.py --song shanty=game/assets/audio/shampoo_island_shanty.mp3 --out game/scripts/song_beats.gd
godot --headless --path game --script res://tests/world_life_test.gd
godot --path game --script res://tests/world_life_test.gd -- --perf
python tools/game_music_video.py showcase --project game --script <showcase.gd> --out <snaps> --only A
```

## Lessons

- **Headless frames run far faster than real time.** Tests that count frames cover far less time than intended;
  count real seconds instead.
- **Transparent effects vanish under a transparent sea** until they draw after it (`render_priority`).
- **Square particles read as pixels.** Give foam, smoke and sparks a soft round texture.
- **Constant ambient pings pin the hero's gaze.** Glance about 2.5 s, rest 3.5 s, and ignore weak pings unless they
  are close.
- **Forced scripted effects leak into the next shot** unless they expire or are cleared after each shot.
- **An additive light shaft fills the screen when the camera is inside it.** Fade it by distance to the camera.
- **A rainbow present in every shot becomes wallpaper.** Make rare things come and go.
- **Measure the frame cost with vsync off**, or both readings show the refresh cap.
- **Separate old failures from new.** Four earlier tests failed identically with the systems switched off
  (`SHAMMYVERSE_WORLD_LIFE=0`).

## Results

| Check | Result |
|---|---|
| World-life test (headless) | 36/36 |
| Open-sea test | 18/18 |
| Ship routes (existing) | 31/31 |
| Frame cost | +2.4 ms per frame at the busiest spot on the development PC (6.35 ms against 3.91 ms); the integrated-GPU target is not measured |
| Earlier failing tests | `fresh_route_test`, `spider_caves_integration`, `camera_animation_polish`, `tickles_music` fail the same way with the systems off |
| Demo | One titled shot per asset (see [game-asset-showcase example](../game-asset-showcase/example.md)) |
