# Example: switch-and-door room

**Illustrative work packet; no Unreal project or converter is provided.** Source: a generic Godot 3D room with a controllable character, switch, door and persistent door-open flag.

## Scope and mapping

- Source files: player input boundary, interaction signal, door state, save schema and room assets.
- Target plan: character/pawn input, switch and door actors with components, an interaction event and a SaveGame boundary.
- Stable data contract: `door_id = "room_a_exit"`; `open` is a boolean. Do not use editor instance names as persistent IDs.
- Save compatibility decision: either explicitly migrate the old payload into the new format or start separate test saves. A matching field name alone does not establish cross-engine save compatibility.
- Before import, record a known one-meter reference, axes and orientation. Check scale, collision and door pivot in both engines.

## Acceptance procedure

1. Fresh test save: door is closed. Outside interaction range, activation has no effect.
2. Enter range and activate once: one event opens the door; repeated activation leaves it open without duplicate rewards or effects.
3. Leave/re-enter the room: intended state persists. Restart and load the isolated test save: door remains open.
4. Compare interaction distance, camera behavior, opening duration and collision clearance against pre-agreed tolerances.
5. Capture target platform performance and visual differences; classify intentional changes separately from regressions.

Expected artifacts: asset/mapping ledger, source and target revisions, test logs/captures, unresolved differences and stop/go decision. **Current evidence status: all checks not_run; decision pending.**

See the [guide](README.md) and [shared contract](../../shared/migration-contract.md). Expand only after the slice is accepted, not because assets imported successfully.
