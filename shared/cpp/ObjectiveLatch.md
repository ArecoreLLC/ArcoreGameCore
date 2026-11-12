# Objective latch

`ObjectiveLatch.h` supplies an engine-neutral collection of up to 64 uniquely
indexed objectives. `Activate(index)` returns true only for the first valid
activation. Invalid indices and duplicate events leave progress unchanged.
Zero or more than 64 configured objectives never complete; `Reset()` clears all
progress. Consumers own range, visibility, authority, persistence and rewards.

Gully Giants is its first Unreal 5.8.4 / Win64 / 3D consumer. Its
`Scripts/Sync-GameCore.ps1` stages the header and a SHA-256 receipt so builds and
packaged runtime do not require this checkout. `GullyGiants.GameCore.ObjectiveLatch`
tests duplicate/out-of-order events, invalid indices/counts, reset and the 64-bit
boundary. Runtime traversal tests belong to the consumer and are separate from
this state contract. Run `Scripts/Test.ps1` there after building the editor target.

Standalone regression: compile and run `tests/ObjectiveLatchTests.cpp` with a
C++14-or-newer compiler and assertions enabled. MSVC 14.44 `/EHsc /std:c++14`
compilation and execution passed on Windows on 2026-11-11. This proves the
portable state rules, not a rendered or packaged Unreal game.
