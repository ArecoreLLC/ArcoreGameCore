# CaptureObjective 0.1.0

Engine-neutral continuous occupancy objective. Configure a finite positive hold
duration (default three seconds), then call Update with prerequisite eligibility,
occupancy and elapsed seconds. Multiple occupants do not multiply capture speed.
The caller owns spatial queries, team filtering, prerequisite rules and hitch caps.

Locked → Ready → Capturing → Complete. Leaving the zone or losing eligibility
clears partial progress. Complete is latched until Reset or successful Configure.
Reset preserves duration. Invalid configuration/time values are rejected without
changing state; zero-time updates can observe eligibility or departure. Completion
is inclusive at the duration boundary and progress remains within [0, 1].

Header-only C++14, no dependencies. tests/CaptureObjectiveTests.cpp exercises
interruption, relocking, duration boundaries, terminal state, reset and nonfinite
inputs. Test references are not execution evidence. The initial consumer is
Box-Fort-Brigade; cross-engine and second-consumer adoption remain unverified.
