# Centered formation reuse review (2026-11-24)

Workflow: game-project-integration, 3D, Unreal 5.8.4 Win64. Existing working-tree work is preserved.
Decision: extract-adapter. Stable rectangular slot math belongs in GameCore; role selection, navigation, combat distances and mesh animation remain in Pebblekin Command.
Inputs: index, population, maximum columns, spacing. Output: centered planar offset, with partial rows centered independently. Empty/invalid inputs return origin. No engine, asset, story or coordinate-axis dependencies. Bounded to 4096 slots and spacing <= 1e6.
Synthetic alternate use: UI/warehouse arrangement with seven items, three columns and spacing 12. Tests cover symmetry, partial rows, invalid inputs and all squad sizes up to 50. These are synthetic fixtures, not second-game validation.
PresentationMotion is retained unchanged for hit/command/stomp envelopes. Consumer chooses separate presentation and paused simulation clocks.
Acceptance: native automation, 18/50 unit delivery, restart, rendered preview. No packaging or performance certification.
