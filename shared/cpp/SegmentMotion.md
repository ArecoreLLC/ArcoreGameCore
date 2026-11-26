# Segment motion 0.1.0

`GameCore::AdvanceSegment(distance, speed, seconds)` returns traveled distance,
consumed seconds and arrival. Inputs use consistent caller-owned units. Finite
nonnegative distance/time and finite positive speed are required; invalid inputs
return an empty, non-arrived result. Zero distance arrives without consuming time.
Callers must bound loops over coincident waypoints. No allocation or engine types.

Reuse suitability: **split-module**. This is time-budget math, independent of
routing and presentation. The consumer owns transforms, routes, collision, timers,
speed policy and arrival events. It supports synthetic conveyor and patrol paths
with distinct segment speeds. Tests cover frame partition, zero distance, invalid
inputs and overshoot. Pocket Fort Patrol is the first consumer; second-game,
collision-physics and network determinism validation are not claimed.
