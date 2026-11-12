# Attachment grid

`AttachmentGrid.h` validates bounded, unique, face-connected integer cells independently of an engine. Limits: 256 cells, radius 0–1024. Invalid input returns false without modifying input. Coordinates are checked before distance arithmetic. Consumers own root identity, block types, sockets, physics, save versions and UI.

Snap Rally is the first consumer (3D, Unreal 5.8.4, Win64). Its automation covers disconnected graphs, duplicate cells, bounds, removal bridges and valid assemblies. This is attachment topology validation, not mechanical stability or physics constraints. Include at compile time and pin SHA-256; no runtime sibling-directory dependency.

Version 0.2.0 adds `CanRemoveAttachmentCell(cells, removed, radius)`: validates
the original graph, requires the target to exist, and rejects empty/disconnected
results without changing input. Flotsam Citadel uses this to protect construction
bridges when dismantling. The game separately protects its central deck and owns
refunds. Existing `ValidAttachmentGrid` behavior is unchanged.

Compile `shared/cpp/tests/AttachmentGridRemovalTests.cpp` with C++17 and assertions
enabled, then run it. Covers bridges, alternate routes, absent targets, sole-cell
removal, invalid originals, coordinate bounds and input preservation.
