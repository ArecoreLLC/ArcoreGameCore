# Ambient chatter from bystanders

Let bystanders say short one-liners when the player comes close (dock parrots asking "Which way?", puffers calling "Where's your boat?") without ever interrupting the game's own dialogue.

A small pipeline in the [ambient-world-life](../ambient-world-life/README.md) family. Its Godot component is
[`ambient_chatter.gd`](../../3d/godot/world_life/ambient_chatter.gd) (Node), vendored with the world-life kit:
`python tools/game_music_video.py vendor --module world-life --project <game project>`. See the [example](example.md).

## Pipeline

| # | Step | Detail |
|---|---|---|
| 0 | Vendor | Install the world-life module (kit and components) with a SHA-256 lock per file; don't edit the vendored copies |
| 1 | Wire | Give `speak(actor, who, text)` (the game's talk bubble) and `is_free()` (no other line showing). |
| 2 | Sources | `add_source(key, actor, who, lines, radius, cooldown, condition)` per bystander group; `condition` can require flying, a quest stage and so on. |
| 3 | Write lines | Short, in character, quoting the song or story where it fits; rotate through two or three. |
| 4 | Review | Read every line in context; keep cooldowns long (about a minute). |
| 5 | Test and review | A headless test drives the component on a fixed clock; the requester reviews it in play or in a [showcase](../game-asset-showcase/README.md) shot |

## Component

`player`, `speak`, `is_free`, `add_source(…)`; signal `said(key, text)`; `said_count`.

The world contract, clock and helpers are in the [world-life kit README](../../3d/godot/world_life/README.md). The
component is exercised by `3d/godot/world_life/tests/components_test.gd` (`tools/tests/test_world_life_godot.py`,
run with `$GODOT` set).

## Checks

| Check | Kind |
|---|---|
| No line while another line is showing; one line per cooldown | automatic |
| Every line read in context by the requester | human |

## Known limits

- Plain text lines; voiced lines need the game's voice pipeline.
