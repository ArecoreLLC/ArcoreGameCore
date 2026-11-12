# Wheel contact 0.1.0

Engine-neutral, stateless C++14 force rules in SI units. `SuspensionForce` takes positive compression (metres), positive compression rate (metres/second), spring stiffness (N/m), damping (N s/m) and a force cap (N). It returns a nonnegative capped contact force. Zero/negative compression has no contact force, including damping. Invalid/nonfinite inputs and overflow return zero.

`LimitTireForce` shares the available friction budget (`normalLoad * friction`) between longitudinal and lateral requests. It preserves direction, cannot exceed the friction circle, and returns zero for unloaded wheels or invalid input.

Consumers own contact queries, surface normals, wheel geometry, sprung mass, unit conversion, force application, integration/substeps, visuals and network authority. These are raycast-wheel building blocks, not a complete tire, constraint or drivetrain simulator. Snap Rally is the first consumer; no second-engine parity is claimed.

Regression source: `tests/WheelContactTests.cpp` (C++14, assertions enabled). Covers compression/rebound signs, clipping, unloaded tires, combined traction, invalid values and a damped quarter-car settling at 30/60/120 Hz. Unreal integration evidence belongs to the consuming game.
