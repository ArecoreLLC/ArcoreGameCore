# Planar move order

Header-only C++14 rule for a single unit-owned destination. `Issue(x,y)` replaces a goal atomically; finite coordinates within +/-1e9 are accepted. Invalid commands preserve the previous goal and state. `Cancel()` clears the order. States are Idle, Moving, Blocked and Arrived.

`Step(actualX, actualY, speed, seconds)` proposes a bounded displacement without advancing state. Nonpositive/nonfinite speed or time produces zero displacement. Finite extreme inputs cannot overflow or overshoot. The engine adapter sweeps this displacement, then calls `Observe` with the actual collision-resolved location, a blocked flag and a nonnegative arrival radius. Invalid observations preserve state. Arrival takes precedence over blocked when within tolerance. Blocked orders continue proposing steps so they can resume when the obstruction clears. Arrived/idle orders cannot restart through observations; issue a new command explicitly.

Keep this rule on a unit or simulation object, not a player controller. Camera/possession changes need not mutate orders. This is not pathfinding, avoidance, networking, a world-boundary policy or a physics implementation. Adapters own those features and their speed/time limits. Synchronous and not thread-safe. Tests are in `tests/PlanarMoveOrderTests.cpp`, compiled with assertions enabled (no NDEBUG).

First consumer: Box-Fort Brigade (Unreal 5.8.4 Win64); consumer automation separately checks controller possession and swept collision behavior. No other-engine parity claim.
