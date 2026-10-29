# Phaser → Godot

**Status:** assisted workflow scaffold; no automated converter or verified game port is supplied. Initial scope is 2D Phaser gameplay. Choose GDScript or C# deliberately based on target export support; examples specify GDScript but do not migrate the legacy C# framework.

## Inputs

Use the [shared contract](../../shared/migration-contract.md), a working Phaser build, exact package versions, scene/component inventory, asset manifests and a chosen Godot version. Select one room instead of the whole game. Read the [2D catalog](../../2d/README.md).

## Mapping

| Source concept | Candidate target | Verify rather than assume |
|---|---|---|
| Phaser Scene lifecycle | Godot scene + lifecycle callbacks | Enter/exit, restart and resource ownership |
| Sprite + Arcade body | Sprite2D + suitable physics body | Units, collider dimensions and physics behavior |
| Keyboard/pointer handlers | InputMap actions + UI/touch events | Press/release, focus loss, remapping |
| Tween/event bus | Tween/signals | Cancellation, ordering and listener cleanup |
| Texture atlas and frame IDs | Imported textures/SpriteFrames | Pivot, filtering, scale and licensing |

## Checklist

- [ ] Run the source and capture expected behavior and tolerances.
- [ ] Inventory APIs and choose target nodes/resources; record incompatible behavior.
- [ ] Port the slice using named actions and separate game data from runtime code.
- [ ] Import assets with explicit scale/filter settings and verify collisions.
- [ ] Run restart, save isolation and behavioral parity checks before expanding.

## Outputs and acceptance

Deliver mapped files, a runnable target slice, test results and the evidence record from the shared contract. Use the [worked example](example.md) as a task template. The historical [mapping reference](../../docs/PHASER_TO_GODOT.md) and [porting CLI](../../porting/README.md) may help, but are C#-oriented; supply an explicit game manifest and do not treat `set done` as verification.

References: [Phaser concepts](https://docs.phaser.io/phaser/concepts), [Godot first 2D game](https://docs.godotengine.org/en/stable/getting_started/first_2d_game/index.html). Check documentation against the versions selected for the run.
