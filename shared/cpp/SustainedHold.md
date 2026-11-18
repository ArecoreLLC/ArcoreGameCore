# Sustained hold 0.1.0

Engine-neutral continuous eligibility timer. Construct with a positive finite duration,
then call `Advance(seconds, eligible)` on the authority. Returns true exactly once
when the duration is reached; further eligible updates remain complete without
repeating the event. `Fraction()` is clamped to [0,1].

Ineligibility, negative/nonfinite delta, or `Reset()` discards progress, including
completed state. Zero delta is valid. Invalid durations never complete. Large finite
deltas may complete once without overflowing. No excess time is banked.

The consumer owns eligibility, actor identity, networking, deadlines and resetting
on ownership changes. This timer samples eligibility on updates; it cannot detect
movement between samples. It differs from ProductionClock, which pauses on blocked
work and repeats recipes. Test source is not evidence of execution.
