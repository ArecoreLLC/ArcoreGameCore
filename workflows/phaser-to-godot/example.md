# Example: coin-and-jump room

**Illustrative work packet, not shipped executable game code.** Target: Godot/GDScript, 2D. Source: a generic Phaser room with a player, a floor, one raised ledge and a coin worth 10 points.

## Scope and mapping

- Source inventory: room scene, player controller, coin overlap handler and score display. Do not load unrelated chapters.
- Target plan: one scene with CharacterBody2D player, StaticBody2D terrain, Area2D coin and score label.
- Input contract: `move_left`, `move_right`, `jump`, `restart`; positive Y points downward. Document speed, jump impulse, collider sizes and fixed-step settings from the actual source rather than copying numbers blindly.
- State contract: score starts at 0; first overlap yields 10; repeated overlap does not add more; restart resets score and restores the coin.

## Acceptance procedure

1. Record source run and agree jump-height/apex-time tolerances before target changes.
2. Move left/right, jump onto the ledge and collect the coin. Compare the recorded trajectory within agreed tolerances, not pixel identity across engines.
3. Stay in the overlap area for 20 physics ticks: score remains 10.
4. Restart twice: each run begins at score 0 with exactly one collectible.
5. Hold movement while losing/regaining focus: no stuck movement after release.

Expected artifacts: source capture, target capture, state assertions, exact revisions/engine versions and a passed/failed/blocked/not_run report. **Current evidence status: all checks not_run.**

Follow the [workflow guide](README.md) and [shared evidence contract](../../shared/migration-contract.md). A future runnable fixture should live in the consuming game or an explicitly tested example package, not be represented by this document alone.
