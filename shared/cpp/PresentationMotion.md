# Presentation motion 0.4.0

Engine-neutral C++11 header for exponential interpolation and retriggerable feedback.
`ResponseAlpha(dt, halfLife)` returns a lerp weight in [0,1]. A constant target
closes half its remaining distance every half-life, independent of frame partition.
Invalid/nonpositive inputs return zero. This is visual smoothing, not physics.

`FeedbackPulse(duration)` starts idle. Trigger resets its remaining duration;
Advance consumes caller time and Value returns a smooth decay from one to zero.
Invalid/nonpositive deltas do nothing. Reset clears it. Consumers own pause,
target selection, colors, transforms, and event detection. Do not save transient
pulses as gameplay state. No engine headers or heap allocation are required.

Critter Contraptions uses this for job transitions, selection breathing feedback,
interaction squash, and delivery celebration. Tests cover frame partition,
retrigger, expiry, invalid inputs, and hitch saturation. Gully Giants also consumes ResponseAlpha for camera FOV easing and FeedbackPulse
for landing and success feedback. Its November 12, 2026 Win64 editor build and
four-test automation suite passed; see the consumer Docs/POLISH_VALIDATION.md.
This establishes a second native consumer, not cross-engine or packaged parity.

Version 0.2.0 adds IsActive and linear Progress (zero at trigger, one when idle or expired). Use Progress for expanding scan rings; Value retains its smooth decay behavior. Haunt-and-Haul adopts both for authoritative action feedback and camera response.

Version 0.3.0 adds optional Trigger(strength): finite positive strength clamps to one; zero, negative and nonfinite events leave an existing pulse untouched. Value scales by strength; Progress remains a normalized timeline. The latest valid trigger replaces intensity and restarts duration. Skybound Sabotage uses this for landing compression and event accents, with consumer-owned replication and camera tuning.

Lumen-Weaver adopts FeedbackPulse for mirror turns, with native decay/reset checks
in LumenWeaver.Light.Chamber. Its Docs/VALIDATION.md records consumer evidence.

## 0.4.0: normalized easing

`SmoothStep01(progress)` clamps finite progress and returns cubic easing with zero
endpoint velocity. Nonfinite input returns zero. Use for scalar opacity or spatial
interpolation; consumers own time and endpoints. See [reuse review](TugboatMotionReview.md).

Version 0.4.0 adds `TriggerPeak(strength)`: restarts duration while preserving the greater of current visible intensity and incoming strength. Invalid/nonpositive strengths are no-ops. Existing Trigger replacement behavior is unchanged. Synthetic camera and UI tests exercise clustered events; timing, camera direction and game policy remain consumer-owned.

## 0.5.0: finite transitions

FiniteTransition(duration) supplies explicit Start/Reset, linear Progress and cubic
Value. Advance(delta) returns true exactly once on completion. Idle/reset is zero;
completed is one. Nonpositive/nonfinite deltas are no-ops; hitches saturate without
overshoot. Invalid durations default to one second. Restart begins at zero; callers
own interruption policy, transforms and collision. Existing APIs are unchanged.

Reuse review: parameterize engine-neutral elapsed time and easing; no game state or
asset dependencies. Echo-Forge owns gate/bridge endpoints and clearance. Synthetic
opacity reveal and frame-partition tests cover an alternate use; a second game for
FiniteTransition has not been validated. Consumer review: Docs/REFINEMENT_REVIEW.md.
