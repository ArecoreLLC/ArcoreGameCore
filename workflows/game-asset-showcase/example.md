# Worked example: ShammyVerse world-life demo (November 2026)

The demo of every asset built in the [ambient-world-life example](../ambient-world-life/example.md). The game's
showcase script is `Design/Iterations/world-life-v001/record_world_life_demo.gd` in the ShammyVerse repository. Its
screenshots and videos are kept there too.

## Setup

| Item | Value |
|---|---|
| Shots | 73 titled shots of 6.5 s, ids by group (A sea, B sky, C shores, D close-ups, E caves/night, G lyric batch) |
| Screenshots | `showcase --only <group>` while building; one PNG per shot plus sheets of eight |
| Soundtrack | Shampoo Island Shanty, Shampoo Island and Plumpy's Teacup Party joined with 3 s crossfades, trimmed to the shot length with a 4 s fade |
| Video | 1920×1200 at 30 fps; preview 960×600 under 28 MB |

## Iterations

1. **First screenshots:** the camera looked straight through Poofy, hiding most subjects. The fix was the `SIDE`
   swing, now `face_yaw()`.
2. **Effects under the sea:** foam, bubbles and splashes drew beneath the transparent ocean. Fixed with `render_priority`.
3. **Moving subjects:** shore-based shots of a turtle, flotsam and a boat were blocked by props. Poofy now hovers over the
   water beside the subject (`hover_watch`), and a boat is re-routed past the camera.
4. **Leaks between shots:** forced snow and licorice streaks continued into later shots until each shot cleared them.
   The game's own ambient chatter appeared once talk bubbles were kept for the dock-chatter shot, so bubbles now
   show only there.
5. **First recording:** the video stopped at 6:17 while the audio ran on, because the soundtrack was longer than
   the shots. The soundtrack is now trimmed to the shot length with a fade.

## Review notes

Some assets read faintly in 6.5 s: a distant whale, a manta under the surface, subtle cloud shadows and foam from
above, a diving bird that leaves the frame, and turtles underwater. They are visible in play. The record lists them
so a later pass can reframe them.
