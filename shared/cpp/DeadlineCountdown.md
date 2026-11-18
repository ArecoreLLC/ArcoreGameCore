# Deadline countdown 0.1.1

Portable C++14 presentation and expiry checks for an absolute caller-clock deadline.
`SecondsLeft(deadline, now)` rounds positive remaining time upward, clamps to the
integer range and returns zero at/after expiry. `HasElapsed` includes the exact
boundary. Nonfinite inputs return zero seconds and false expiry, so an invalid
clock never authorizes a transition. Finite subtraction overflow saturates the display.

Consumers own clock synchronization, authority, phase transitions and clock resets.
Use a monotonic clock within a session; do not accumulate per-peer frame deltas.
A displayed zero does not authorize a transition: use `HasElapsed` on the authority.
Compile tests/DeadlineCountdownTests.cpp with assertions enabled. Skybound Sabotage
uses a replicated server deadline for its race preparation phase; networking and
camera/movement acceptance remain consumer-owned.
