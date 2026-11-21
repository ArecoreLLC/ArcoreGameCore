# Horde Defense RTS: design packet for designers aged 10 to 12

A starting design for a real-time strategy game where the player builds a base and defends it against waves of enemies. It is written for a young designer working with a helper. Everything here is a *starting point*: the designer's own ideas replace the examples. Names, theme and art are placeholders, with no private game content.

Companion printable: [Horde_Defense_RTS_Design_Workbook_Ages_10_12.docx](Horde_Defense_RTS_Design_Workbook_Ages_10_12.docx) (build it with `build_horde_defense_rts_workbook.py`). It follows the same conventions as the other [kids workbooks](../README.md): trigger / condition / action rules, drawing boxes and a paper playtest.

## 1. Pitch and pillars

**One sentence.** "Gather, build and command a small team to protect your Heart Tower from bigger and stranger waves of enemies until dawn."

| Pillar | What it means | How we test it |
|---|---|---|
| Prepare, then react | Calm build time between waves, tense fight time during waves. | In a playtest the player uses build time and does not just click through it. |
| Readable at a glance | A player can tell enemy types and what is winning from the screen. | A new tester names each enemy's job after one wave. |
| Every choice has a cost | Resources are always a little short. | Testers say "I had to choose". |
| Fair losses | When the base falls, the player can say why. | Tester names one thing to do differently. |

**Audience note.** Ages 10 to 12 can handle two or three resources, 4 to 6 unit or tower types and a rock-paper-scissors counter system. Avoid hotkeys-per-unit complexity and very long matches. A full match should take 12 to 20 minutes.

## 2. Core loop

```
Prepare (build, gather, train) -> Wave arrives -> Command and fight
      ^                                                  |
      |  spend rewards on upgrades <- Wave cleared <-----+
      +------ base falls: see what went wrong, retry
```

- **Match goal:** survive 10 waves (about 15 minutes), including a boss on wave 5 and wave 10.
- **Lose:** the Heart Tower reaches 0 health.
- **Scale:** one map, one base, optional second outpost unlocked later.

## 3. What the player does (controls)

Mouse or touch first; keyboard shortcuts are optional extras.

| Action | Mouse | Touch |
|---|---|---|
| Select a unit | Click, or drag a box | Tap, or drag a box |
| Move or attack | Right-click ground or enemy | Tap ground or enemy with a unit selected |
| Build | Pick from the build menu, click ground | Same, tap |
| Call a wave early | Button "Send next wave" | Same |
| Pause and plan | Space | Pause button |

Design rules: at most 12 on-screen buttons, a pause that still allows planning, and big targets (at least 48 px) for touch. See [workflow index](../../../../workflows/index.json) before porting to Android; do not assume desktop input is enough.

## 4. Economy: three resources

| Resource | Source | Spent on | Why it exists |
|---|---|---|---|
| Wood | Workers at trees | Walls, basic towers, workers | Early steady supply. |
| Stone | Workers at quarries (farther, riskier) | Strong towers, upgrades | Gives a reason to expand and defend an outpost. |
| Sparks | Dropped by defeated enemies, plus a bonus for clearing a wave without losing a building | Heroes and special abilities | Rewards good defense, not just banking. |

Starting stock: 200 Wood, 50 Stone, 0 Sparks. Worker: 50 Wood, gathers 5 Wood per 10 seconds. (All numbers are a first draft; see section 9.)

## 5. Buildings and towers

| Name (placeholder) | Cost | Job | Strong against | Weak against |
|---|---|---|---|---|
| Heart Tower | n/a | Win condition. 500 health. Can be repaired by workers. | n/a | Everything |
| Wooden Wall | 10 Wood | Blocks and slows enemies | Runners | Smashers |
| Arrow Tower | 60 Wood | Steady ranged damage | Runners, flyers | Armored |
| Boulder Thrower | 80 Wood, 40 Stone | Area damage, slow fire | Swarms | Flyers, fast units |
| Spark Totem | 50 Stone, 20 Sparks | Slows enemies in a circle, heals nearby allies | Everything a little | Needs support |
| Barracks | 100 Wood | Trains soldiers | n/a | n/a |
| Workshop | 80 Wood, 50 Stone | Unlocks upgrades | n/a | n/a |

Placement is the main skill: choke points, walls that funnel, towers that cover each other. Limit: 20 buildings at once to keep it readable.

## 6. Units you command

| Unit | Cost | Role | Counter note |
|---|---|---|---|
| Worker | 50 Wood | Gather, build, repair. Does not fight well. | Protect it. |
| Guard | 60 Wood | Tough frontline, short range. | Good versus runners. |
| Archer | 60 Wood, 20 Stone | Ranged, fragile. | Good versus flyers. |
| Mender | 40 Wood, 30 Stone | Heals nearby units. | Keep behind the Guards. |
| Hero (one at a time) | 30 Sparks | Strong, has one special move on a cooldown. Respawns after 30 seconds. | The comeback tool. |

Army cap: 15 units. Keep commands simple: move, attack, hold position.

## 7. Enemy horde

Counter triangle, taught in the first three waves: **Runners beat Archers, Armored beat Runners, Flyers beat Armored.** Towers and units counter differently, which is why mixing matters.

| Enemy | Health | Speed | Behavior | First seen |
|---|---|---|---|---|
| Scuttler (swarm) | 10 | Fast | Many at once, go for nearest building | Wave 1 |
| Runner | 25 | Very fast | Dashes past walls toward workers | Wave 2 |
| Brute (armored) | 120 | Slow | Resists arrows, smashes walls | Wave 3 |
| Glider (flyer) | 40 | Medium | Ignores walls, attacks towers | Wave 4 |
| Spitter | 30 | Slow | Ranged, outranges Guards | Wave 6 |
| Boss: Hollow King | 600 | Slow | Spawns Scuttlers every 10 seconds, area stomp warns with a red circle first | Wave 5, return stronger Wave 10 |

**Telegraphing:** every big attack shows a warning (red circle, sound cue, 1.5-second delay). This makes losses feel fair.

## 8. Wave script (first draft)

Enemies come from 2 gates marked on the map. Show an arrow and a preview icon list before each wave.

| Wave | Contents | Prep time | Lesson |
|---|---|---|---|
| 1 | 8 Scuttlers | 60 s | Build a tower, gather. |
| 2 | 10 Scuttlers + 3 Runners | 50 s | Walls and funneling. |
| 3 | 8 Scuttlers + 2 Brutes | 50 s | Armored needs a different answer. |
| 4 | 6 Runners + 4 Gliders | 45 s | Anti-air. |
| 5 | Boss: Hollow King + 10 Scuttlers | 60 s | Hero and focus fire. |
| 6 | 3 Brutes + 4 Spitters | 45 s | Outranging; use Archers. |
| 7 | 15 Scuttlers + 6 Gliders | 45 s | Area damage. |
| 8 | 5 Brutes + 8 Runners | 40 s | Mixed defense. |
| 9 | Everything, from both gates at once | 40 s | Split attention. |
| 10 | Hollow King (stronger) + escorts | 60 s | Final test. |

Difficulty is tunable with three settings: Easy (enemy health × 0.8, prep time × 1.3), Normal, Hard (health × 1.25, prep × 0.8). Ask: "Does losing teach something?"

## 9. Upgrades and progression

Between waves, spend Sparks or stone at the Workshop. Pick one of two paths per tower (for example Arrow Tower: **Rapid** shoots faster, or **Piercing** hits two enemies). Choosing, not just buying more, is the point. Up to 3 upgrade tiers. Unlock new types of building every two waves so the game keeps changing.

## 10. Map and level design

One 40 x 40 tile map: the Heart Tower in the middle-south, two gates in the north, a forest to the west (Wood), a quarry to the east (Stone, farther away, exposed), rivers or cliffs forming two choke points. Rules of thumb:

1. The player should always see where enemies will come from.
2. Provide 2 good defense spots and 1 tempting but risky spot.
3. Paths exist after walls are placed (never fully block the path; enemies then attack walls).
4. Keep the safest resources near the base so early waves are not unfair.

## 11. Screens and feedback

- **HUD:** resources top-left, wave number and countdown top-center, Heart Tower health bar top-right, build menu bottom, selected unit info bottom-left, minimap bottom-right.
- **Feedback:** hit flashes, health bars over damaged things only, floating "+5 Wood", a clear sound for "wave starting", "building destroyed" and "wave cleared". The adaptive music workflow in the repo ([adaptive-music-stems](../../../../workflows/adaptive-music-stems/README.md)) can supply calm and battle layers.
- **Accessibility:** do not rely only on color; give each enemy a distinct shape, with a text label option. Offer a slow-motion setting.

## 12. Rules the designer must write (trigger, condition, action)

Use the workbook's rule boxes. Starter examples:

1. WHEN an enemy enters a tower's range, CHECK is it the nearest enemy? YES: fire. NO: keep targeting the nearest.
2. WHEN a building's health reaches 0, CHECK is it the Heart Tower? YES: lose screen. NO: remove it and drop 50% of its cost as rubble resources.
3. WHEN the wave timer reaches 0, CHECK is it wave 5 or 10? YES: boss warning, special music. NO: normal wave.
4. WHEN a worker is idle for 5 seconds, CHECK is a resource close? YES: auto-gather. NO: show an idle icon.

## 13. Facilitated schedule (six 45-minute sessions)

| Session | Designer does | Helper does | Output |
|---|---|---|---|
| 1. Pitch | Names the game, theme, heroes and enemies (workbook pages 1 to 4). | Asks "why", keeps scope small. | One-sentence pitch, picks 3 pillars. |
| 2. Economy and base | Picks resources, towers, units (pages 5 to 8). | Checks costs are never all free. | Cost table. |
| 3. Enemies and waves | Designs 4 enemies and a 10-wave script (pages 9 to 11). | Points out the counter triangle. | Wave table. |
| 4. Map | Draws the map and gates (page 12). | Checks for a safe start and choke points. | Map. |
| 5. Paper playtest | Runs waves on the map with tokens and dice (page 14 and the section below). | Plays as the enemy or tester. | Playtest notes. |
| 6. Change and plan | Fixes the top 3 problems, chooses a first digital version (pages 15 to 16). | Writes the build plan. | Updated design and next steps. |

## 14. Paper prototype rules

Needs: a printed map grid, coins for the Heart Tower, colored tokens for towers and enemies, paper slips for resources, and one six-sided die.

1. Each turn is 5 seconds. Enemies move their speed in squares (Slow 1, Medium 2, Fast 3).
2. A tower hits the nearest enemy in range once per turn (roll 4 or more on the die, or auto-hit if you want simple).
3. Gathering: each worker gives 1 resource per 2 turns.
4. Fill in a table: wave, what was built, what broke, how it felt.

Success check: after 3 waves, the tester can say what each enemy does and make a plan unprompted.

## 15. Balance checklist

- [ ] A player who builds nothing loses by wave 3.
- [ ] A player who builds only one tower type loses by wave 6 (mixing is rewarded).
- [ ] No upgrade is chosen by every tester.
- [ ] Prep time lets a new player build two things.
- [ ] Every loss has a visible cause.
- [ ] A match lasts 12 to 20 minutes.

Adjust one number at a time and write it in an [iteration record](../../ITERATION_RECORD.md).

## 16. From design to a playable game

This packet defines design only. When the designer is ready for a digital build, start with the [project brief](../../PROJECT_BRIEF.md) and the [migration contract](../../../../shared/migration-contract.md) and pick the engine through the workflows index. Smallest playable version (MVP):

1. One map, Heart Tower, 1 resource, 2 tower types, 2 enemy types, 3 waves.
2. Add the second resource, the Barracks and units, then waves 4 to 10.
3. Add the Hero, the boss with telegraphed attacks, upgrades.
4. Add touch controls and sound only after the loop is fun.

Build and test claims must come from commands actually run. Nothing in this packet has been implemented or playtested yet.

## 17. Open questions for the designer

1. What is the theme (fantasy, space, robots, animals)? Why do the enemies attack?
2. What is the one thing that makes your game different?
3. Who is the hero, and what does their special move do?
4. Single player only, or a friend can play as the horde?
5. Where will it run first: PC, tablet, or both?

## 18. Safety and age notes

Keep enemy defeat cartoonish (poof, not gore). Offer a calm mode with longer prep time. Prefer original characters and avoid copying existing game assets. Do not collect personal info from child testers; use first names or initials only.
