# Portable buoyancy primitives

`Buoyancy.h` supplies mass/planar center-of-mass aggregation and a unilateral,
capped immersion spring/damper in SI units. Invalid inputs are rejected. It has
no engine dependencies and does not advance time or sample an ocean. Consumers
own coordinate conversion, fixed simulation steps, stability and gameplay.

First consumer: Flotsam Citadel, 3D Unreal 5.8.4 / Win64. Its adapter uses four
samples on one aggregate raft, analytic waves and bounded 120 Hz integration.
It is a reduced heave/roll/pitch experiment, not Chaos or hydrodynamics.
Consumer automation covers force boundaries, invalid values, mirrored mass,
frame-rate parity, settling and game lifecycle. Evidence belongs to the game.

Consumers vendor the header with a SHA-256 provenance manifest so runtime builds
do not require a sibling framework checkout. Do not include game rules here.

Portable contract check (C++17 compiler, assertions enabled):
`c++ -std=c++17 shared/cpp/tests/BuoyancyTests.cpp -o buoyancy-tests`, then run
`./buoyancy-tests`. MSVC equivalent: `cl /EHsc /std:c++17
shared/cpp/tests/BuoyancyTests.cpp`, then run `BuoyancyTests.exe`.
