# Timed stacks — 0.1.0

Header-only C++14, independent of engine and damage rules. Add refreshes a shared expiry, clamps to the supplied positive cap, and starts at one after expiry. Count is a pure query over [last mutation, expiry). Consume returns the live count exactly once. Invalid/nonfinite/backwards mutation times, nonpositive durations/caps and overflow leave state untouched. Reset starts a fresh simulation clock. Pass consistent double-precision simulation seconds; paused clocks freeze expiry. Caller owns synchronization and cap policy.

Scrapshift Arena uses this for saw-applied conductive stacks consumed by arc attacks. Damage, chain targets and effects remain in the game. Tests cover cap, refresh, exact expiry, invalid inputs, overflow, consume and reset; listed tests alone are not execution evidence.

Compile `tests/TimedStacksTest.cpp` with C++14 and assertions enabled, then execute it. Unreal consumer automation is `Scrapshift.TimedStacks`.
