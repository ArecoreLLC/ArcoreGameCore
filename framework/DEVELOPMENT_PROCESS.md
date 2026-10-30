# Reusable development process

Use a small playable change as the unit of work. Keep the process proportional: a color adjustment needs a focused comparison; a save-system change needs recovery and relaunch checks.

## 1. Define the playable outcome

Start a game with the [project brief](templates/PROJECT_BRIEF.md). State the player experience, target platform, selected engine, first playable slice, and performance goal. Mark assumptions and unresolved choices explicitly.

For each iteration, record the trigger, desired result, scope, and behaviors that must survive. Example: improve a creature's flipper contact while preserving its head, palette, root position, and unrelated animation tracks. Separate creative feedback from technical implementation choices.

## 2. Establish a recoverable baseline

Inspect the working tree and identify existing work. Record the source revision plus any relevant uncommitted changes. Preserve the previous reviewed source, runtime export, settings, and evidence. Name the canonical starting asset; a script's presence does not prove it reproduces the latest externally edited model.

Use a new version directory for asset revisions. Keep original references and imported sources intact. For significant preservation requirements, compare hashes or relevant geometry, color, skeleton, and animation data.

## 3. Prove the behavior with a small implementation

Build a minimal playable path before increasing visual complexity. Keep movement and collision stable while swapping visual assets. Reuse existing animation, interaction, and audio systems when they support the intended result.

Create a development fixture that prepares prerequisites directly. Include a boundary state, such as one action before an unlock. Define cancellation and cleanup when the player respawns, changes scene, loads a save, or skips a cinematic. Test state transitions as well as the happy path.

## 4. Produce and integrate assets deliberately

For characters, review silhouette and proportions before dense detail. Keep named editable components, axis/scale assumptions, references, and scripts. Test deformation at multiple phases; add joints when they produce useful motion.

Export a new runtime derivative, then check the actual imported skeleton, clips, materials, vertex data, scale, and orientation. Keep authoring-only presentation objects out of the export. Review front, side, back, and three-quarter views, followed by close, gameplay-distance, and moving views in the engine.

For environments, verify visible shore/terrain and collision agree. For materials, compare brightness, palette, transparency, normals, and quality settings. For audio, preserve source text and recordings, use stable track IDs, and drive synchronization from playback position. A successful automated playback check does not verify the sung words or their timing.

Use the [asset record](templates/ASSET_RECORD.md) when an asset needs provenance or version tracking.

## 5. Validate the changed behavior and what it could break

Select checks from the [validation guide](VALIDATION.md). Separate functional results from art review, listening review, and performance evidence. Capture comparisons with consistent camera, lighting, pose, and quality settings where practical.

Investigate failures before updating expected values. If intended behavior changed, record the decision and fixture replacement. If an assertion is too broad, narrow it to the property it actually promises to protect. Preserve the old evidence as history.

## 6. Complete the iteration

An iteration is ready for review when:

- Its intended outcome is demonstrated and its scope is clear.
- Editable source and runtime derivative can be located and related.
- Affected checks have recorded results and evidence paths.
- Required visual or listening reviews have findings, including unresolved defects.
- Current instructions identify the active version and behavior.
- The next action is explicit; draft work is not described as approved or production-ready.

Keep implementation completion, review readiness, and creative acceptance distinct. Record actual feedback when available; silence is not an acceptance record. Routine work can continue within the agreed scope.

## 7. Improve the process after milestones

Review what reduced iteration time, what caused repeated rework, and what escaped checks. Choose one bounded improvement with a completion criterion. Update the guide, template, or maintained test selection that would prevent recurrence.

Useful measures are time to reach a test scenario, defects found after integration, failed attempts to reproduce a source asset, and frame-time changes in a fixed scenario. Establish a baseline before setting improvement targets; raw test counts and bone counts are not quality measures.
