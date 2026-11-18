# ActionCooldown 0.1.0

Portable C++14 action admission using a finite, nonnegative caller clock.
`TryConsume(now)` admits immediately when unused, then only at or beyond the
interval since the last admitted action. Rejected calls do not move the deadline.
Releasing input does not reset recovery. Long hitches admit one action per poll,
without catch-up bursts. Backward time is rejected until the prior deadline;
call `Reset()` when intentionally starting a new clock epoch or round.
`ReadyFraction(now)` is bounded [0,1] for UI. Invalid time fails closed.
Invalid intervals use 0.25 seconds. No engine, input, authority or damage policy.

Box-Fort-Brigade owns Unreal firing, focus, reset and visual-feedback validation.
Standalone assertions: `tests/ActionCooldownTests.cpp`. This reference is not
execution evidence; see consumer validation records.
