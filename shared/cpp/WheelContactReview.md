# Wheel contact 0.2.0 reuse review

Responsibility: stateless, engine-neutral SI force calculations, now including a
signed normalized drive envelope with independent positive forward/reverse limits.
No Unreal imports, assets, object names, input bindings or game-state dependencies.

Decision: parameterize. Speed limits attenuate only motion in the requested
direction. Acceleration, grip, braking priority, contact eligibility and integration
remain consumer-owned. Existing suspension and friction APIs are unchanged.

Synthetic alternate adapter: a utility vehicle with 4 m/s forward and 2 m/s reverse
limits, including half input and opposing overspeed. This is portable math evidence,
not a second-game playtest. WheelContactTests.cpp also covers saturation and invalid
inputs. Snap Rally consumes the canonical header through its version/hash lock.

Portable MSVC C++14 assertions passed on 2026-11-24. Consumer native and rendered
evidence is recorded in Snap Rally's Docs/REFINEMENT_PASS.md. Remaining limits:
single game integration, no second-engine parity, no drivetrain or tire simulation.
