# Portable C++ recipe clock

Version 0.2.0 adds `RestoreFraction(double)` for save adapters. Only finite
values in [0, 1) are accepted; rejection preserves current progress. A completed
recipe is represented by the consumer's inventory, never by a saved fraction of
one. Consumers must validate their entire snapshot before committing any state.
The 0.1.0 timing behavior remains unchanged.

`ProductionClock.h` is an engine-neutral, header-only production timer. Consumers
own inventory, authority, worker welfare, persistence and recipe completion.
`Advance(seconds, canWork)` retains partial progress when blocked but does not
bank blocked time. A call completes at most one recipe and discards overshoot;
use bounded simulation steps when frame-rate-independent throughput is required.
Invalid time is ignored; invalid duration falls back to four seconds. Reset
clears progress. This is not an offline production or catch-up scheduler.

First consumer: Critter Contraptions, Unreal 5.8.4, Win64, 3D. Its sync script
stages a source-hashed local copy; packaged games require no sibling checkout.
Native automation in that consumer covers pause/resume, invalid time, overshoot,
reset, autonomous production and worker recovery. Build/playtest evidence belongs
to the consumer, not to this contract.

Standalone regression: compile `tests/ProductionClockTests.cpp` with a C++11 or
newer compiler and run the executable with assertions enabled (no `NDEBUG`).
This covers invalid input, pause/resume, reset and overshoot without Unreal.
