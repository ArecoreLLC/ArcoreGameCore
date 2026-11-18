# Example: short fur for a creature, shell budget 16

A Godot 3D consumer needs short brown fur on one creature, mobile target, at most 16 shells.

1. Check the consumer declarations using the [integration workflow](../game-project-integration/README.md)
   and run the version check described in the [guide](README.md#version-and-update-check).
2. Ask [HairLab](https://github.com/ArecoreLLC/ArcoreModelForge/blob/main/texture-lab/README.md) for a
   shell-fur set (`fur_short` family, 16 shells) and the brown palette. Record the returned asset id,
   version, seed and the HairLab version from `pin.json`.
3. Review it in ModelForge's Shell Fur Lab at the consumer's shell count and mesh triangle count; keep the
   triangle-cost readout with the evidence.
4. Import the approved version into the consumer, apply the Godot shader recipe from HairLab, and test on
   the target device: layering at grazing angles, overdraw, frame time.
5. Record the accepted revision and playback evidence under the
   [shared contract](../../shared/migration-contract.md). Failures stay in the record.

Generation, shader recipes and the lab tooling are owned by HairLab. GameCore does not repeat them.
