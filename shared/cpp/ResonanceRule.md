# Portable gameplay rules

`ResonanceRule.h` is a dependency-free C++ charge interaction rule. The consumer owns tone identifiers, range/visibility checks, presentation, and a monotonic clock. Invalid time, mismatched tones and cooldown rejection do not mutate progress. Completion is terminal until reset. Construct a new rule to change tuning.

Vendor this header into the consumer and record its SHA-256; shipped games must not include sibling checkout paths. Engine adapters and game-specific content remain in the consuming project. Tests should exercise wrong tones, cooldown boundaries, invalid time, terminal state and reset in the consumer's native runner.

Standalone regression: compile `tests/ResonanceRuleTests.cpp` with C++17 (assertions enabled), then run the executable. Covers rejected inputs, 500 rapid pulses, exact cooldown boundaries, clock rollback, 1,000 terminal commands, and reset.

Version 0.2.0 adds `RequiredPulses()` and a read-only `ReadyFraction(now)` for cooldown UI. The fraction is in [0,1]; 1 means ready, 0 means just fired, completed, invalid time or clock rollback. It never consumes a pulse. Use the same monotonic clock as Apply. Existing Apply/reset behavior is unchanged.
