# Combat windows (v1)
Engine-neutral, header-only C++14 timing for dodge, parry and attack recovery. Times are monotonic simulation seconds; active intervals exclude the end. Recovery includes the active period. Invalid input and starts during recovery leave state untouched. Reset when starting a new run. Pausing the simulation clock pauses windows. Consumers own damage, input, authority and animation.

Scrapshift Arena is the initial Unreal consumer. It vendors this one header with a SHA-256 pin using Scripts/Sync-GameCore.ps1; shipped builds do not need GameCore. Its Scrapshift.CombatWindow automation covers boundaries, rejected starts, invalid values and reset. This is not multiplayer or cross-engine parity evidence.
`Unreal 5.8 GetTimeSeconds()` returns double. Preserve that precision at both start and query; narrowing only the query to float can move it before the window start. The consumer integration smoke test exercises same-frame guards.

Standalone regression: from a C++14-capable developer shell, compile `shared/cpp/tests/CombatWindowTest.cpp` and execute the result (for MSVC: `cl /EHsc /std:c++14 shared/cpp/tests/CombatWindowTest.cpp`). Assertions cover invalid values, overflow, half-open boundaries, recovery, precise clock values and reset. Build outputs should go to a consumer's temporary/evidence directory.
