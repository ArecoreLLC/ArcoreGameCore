# Cooperative work

`CooperativeTask.h` is an engine-neutral C++14 work accumulator. The consumer supplies the count of eligible workers actually in range, elapsed seconds and their rate. Progress pauses below the minimum; completed work persists until explicit reset. Advance returns true only on the completion edge. Invalid/non-finite input is ignored, overflow saturates to completion, and excess work is discarded. This utility owns no workers, movement, authority or persistence.

First consumer: Pebblekin Command, Unreal 5.8.4 Win64, bridge construction and shared loot lifting. Consumer automation covers quorum, paused progress, completion edge, reset and invalid input. This is not evidence of Godot parity or multiplayer safety. Pin a vendored copy for standalone builds; runtime needs no external checkout.

Portable regression fixture: `tests/cooperative_task_test.cpp`. From an MSVC developer prompt, compile with `cl /EHsc /std:c++14 tests/cooperative_task_test.cpp /Fe:cooperative_task_test.exe` and run the executable. Or use `c++ -std=c++14 tests/cooperative_task_test.cpp -o cooperative_task_test` on a C++14 toolchain. Run without NDEBUG; assertions cover quorum, rate scaling, invalid values, overflow saturation and completion/reset. The MSVC x64 fixture was compiled and executed successfully for the first consumer; other compiler/platform commands are reproduction instructions, not executed evidence.

## Worker readiness

`RequiredWorkers()`, `MissingWorkers(present)` and `CanWork(present)` expose the same quorum rule used by Advance. MissingWorkers saturates at zero for large counts and deliberately remains meaningful after completion: consumers may need continuing escorts for a completed lifting task. CanWork is false once complete. Queries do not mutate work. Pebblekin uses these queries for command previews, live task feedback and escort movement; its smoke fixture checks paused planning before delivery. Portable and Unreal tests cover readiness before/after completion and reset. Existing Advance behavior is preserved.
