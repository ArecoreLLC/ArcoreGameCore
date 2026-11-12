# Rechargeable reserve

Engine-neutral C++14 bounded reserve for stamina, batteries and limited-use abilities.
A valid positive capacity starts full; invalid capacities produce an inert, empty reserve.
`Spend(amount)` drains at most the available amount and returns the fraction supplied.
`Refill(amount)` saturates without overflow. Non-finite/nonpositive amounts never mutate
state. `Reset()` restores capacity. There is no clock, automatic regeneration, persistence
or authority logic: consumers supply amounts and decide when regeneration is allowed.

Gully Giants is the first consumer (Unreal 5.8.4, Win64, 3D): three seconds of glide
budget, recharged only when grounded. Its engine adapter owns input, gravity, camera,
checkpoints, exhaustion/redeploy rules and feedback. This does not prove engine parity.

Compile `tests/RechargeableReserveTests.cpp` with a C++14 compiler, assertions enabled.
Consumer automation also covers real descent, exhaustion, landing refill,
checkpoints and restart. Evidence belongs in the consuming project's
`Docs/GLIDER_VALIDATION.md` and hashed automation receipt.
