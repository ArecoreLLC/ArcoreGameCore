# Timed window 0.2.0

Engine-neutral C++14 one-shot opportunity for input buffering and grace periods.
Starts closed. `Refresh()` opens/restarts the configured duration; `Advance(seconds)`
subtracts finite positive elapsed time, saturating at zero. The exact expiry boundary
is closed. Invalid elapsed values are ignored. Invalid/nonpositive durations stay
closed. `Consume()` reports whether the window was open and closes it; `Reset()`
closes it without reporting. No engine clock, input, movement or persistence policy.

`TryConsume(eligible)` admits a request exactly once only when eligible. A rejected
attempt preserves its remaining lifetime; expiry still wins over eligibility.
Scrapshift Arena uses this for 140ms dodge/parry requests, cancels pending requests
at wave transitions and defeat, and snapshots dodge direction when admitted.

The caller chooses ordering: advance old windows, refresh current eligibility, then
consume if the action succeeds. Do not refresh eligibility after spending it until
the underlying action becomes eligible again. Floating-point boundary comparisons
follow the caller's supplied times; this is not a deterministic networking clock.

Compile tests/TimedWindowTests.cpp with C++14 and assertions enabled. Gully Giants
uses separate 120ms ledge grace and 150ms jump input windows; its Unreal adapter owns
ground contact, the jump impulse and cancellation on grapple/recovery/reset.
Consumer runtime evidence belongs in Docs/JUMP_VALIDATION.md. No cross-engine claim.
