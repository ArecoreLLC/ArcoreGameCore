# Combat windows (v1)
Engine-neutral, header-only C++14 timing for dodge, parry and attack recovery. Times are monotonic simulation seconds; active intervals exclude the end. Recovery includes the active period. Invalid input and starts during recovery leave state untouched. Reset when starting a new run. Pausing the simulation clock pauses windows. Consumers own damage, input, authority and animation.

Scrapshift Arena is the initial Unreal consumer. It vendors this one header with a SHA-256 pin using Scripts/Sync-GameCore.ps1; shipped builds do not need GameCore. Its Scrapshift.CombatWindow automation covers boundaries, rejected starts, invalid values and reset. This is not multiplayer or cross-engine parity evidence.
`Unreal 5.8 GetTimeSeconds()` returns double. Preserve that precision at both start and query; narrowing only the query to float can move it before the window start. The consumer integration smoke test exercises same-frame guards.

Standalone regression: from a C++14-capable developer shell, compile `shared/cpp/tests/CombatWindowTest.cpp` and execute the result (for MSVC: `cl /EHsc /std:c++14 shared/cpp/tests/CombatWindowTest.cpp`). Assertions cover invalid values, overflow, half-open boundaries, recovery, precise clock values and reset. Build outputs should go to a consumer's temporary/evidence directory.

## 0.2.0: active countdown queries

`ActiveRemaining(now)` returns seconds until the active interval ends, or zero
for inactive, pre-start and nonfinite queries. It never changes state. Unlike
`Remaining`, it excludes recovery after the active interval. This supports hit
protection and encounter-entry cues without duplicating gameplay timestamps.
Existing start, active and recovery semantics are unchanged. Scrapshift Arena
uses the versioned module manifest and lock; normal builds never sync headers.

## 0.3.0: active work progress

`Progress(now)` returns completion in [0,1]. Idle/reset, nonfinite and pre-start queries return zero; completion and later finite queries return one. Successful zero-duration windows are immediately complete. Failed starts preserve progress. Flotsam Citadel uses this for salvage reeling and repair feedback. Existing APIs are preserved.
