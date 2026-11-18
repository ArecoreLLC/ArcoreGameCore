# Rate ramp 0.1.0

Engine-neutral C++11 nonnegative rate and integrated travel budget. `Advance(dt,
target, acceleration)` returns distance while accelerating or braking to a fixed
target rate. It integrates the ramp and any remaining cruise time exactly; a
stationary target produces the same rate and distance across frame subdivisions.
All values use consumer-defined consistent units. `Value()` returns current rate.
`Reset(rate)` defaults to rest and sanitizes invalid or negative rates to zero.

Nonpositive/invalid time or acceleration and negative/invalid targets return zero
without mutation. Arithmetic overflow also fails closed without mutation. Zero
target is valid. A hitch is integrated, not clamped: consumers should discard
unused distance on collision or route changes, and own pause policy and sweeps.
This is a travel budget, not a collision solver or a moving-target path planner.

Gully Giants uses it for each grapple route segment, accelerating from rest and
discarding overshoot at corners. Tests cover braking, cruise, partition invariance,
invalid input, reset and overflow. Engine validation remains consumer-owned.

## 0.2.0: reversible rates

SignedRateRamp has the same interface and failure semantics, but admits negative
initial and target rates. It integrates signed displacement through zero exactly;
the original RateRamp still rejects negative rates. Consumers own directional
speed limits, brake selection, collision and substeps for changing headings.
Tugboat Tumble uses this for loaded acceleration, reverse and braking.
