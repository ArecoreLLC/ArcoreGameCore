# HoldRepeat 0.1.0

Engine-neutral C++11 input repeat scheduler. `Update(held, monotonicSeconds)`
returns true immediately on a valid press, then once per interval (default 0.5s).
Release stops repetition. Invalid time and clock rollback cannot emit. Invalid
intervals use 0.5s. A long frame emits at most one event and starts a fresh interval;
missed events are never replayed in a burst.

`CancelUntilRelease()` prevents a held input carrying into a new context. Call on
restart, respawn, completion or focus loss. A subsequent release re-arms it.
The consumer owns input/focus sampling, pause handling, target selection, cooldown,
range and resource validation. Rapid fresh taps are intentionally not rate limited.

Initial consumer: Echo-Forge, Unreal 5.8.4 Win64, hold E to pulse. No cross-engine
parity or second-consumer validation is claimed. Standalone assertions cover press,
release, cancellation, boundaries, invalid clocks, rollback and hitch suppression.
