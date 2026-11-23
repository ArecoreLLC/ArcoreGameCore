# Adaptive music 0.1.0

Engine-neutral C++14 runtime for Sonic Alchemist `arcore-adaptive-v1` scores: aligned
looping layers, named states with per-layer dB gains, and one quantized transition rule.
It is the runtime half of the [adaptive-music-stems workflow](../../workflows/adaptive-music-stems/README.md);
Sonic Alchemist authors and exports the stems, the game plays them.

- `AdaptiveScore` holds tempo, beats per bar, loop bars, fade beats, boundary
  (`Immediate`, `Beat`, `Bar`, `Phrase` = one loop), master dB, layer/state names and the
  `[state][layer]` gain table. A gain at or below −60 dB is silent, matching a disabled
  layer in design.json. `Valid()` applies Sonic Alchemist's own limits. `TargetGain`
  returns the linear runtime gain with the master included, the same values Sonic
  Alchemist exports as `assets.json` `runtime.states[].linearGains`.
- `AdaptiveMixer` waits for the next boundary of the music clock before changing state,
  then fades rising layers on sin and falling layers on cos (equal power), as Sonic
  Alchemist auditions transitions. The fade starts on the boundary itself, even when it
  falls mid-frame, so results do not depend on frame partitioning. `Advance(dt, state)`
  runs a free clock; `AdvanceTo(musicSeconds, state)` follows an audio clock measured
  from the moment the layers started. An earlier time resynchronizes without a
  transition. Desired state −1 (or an unknown index) holds the current state.
  `SecondsToBoundary()` supports stingers and HUD cues.
- `EngagementHold` keeps a state engaged for a while after activity so music does not
  flap between bursts. The caller decides what counts as activity and whether pause
  stops the countdown.

Invalid scores keep every layer silent; nonfinite or negative times are ignored.
Callers own the audio voices, sample-locked starts, the clock source, state choice,
ducking and user volume. Use [AdaptiveMusicPlayer](../../3d/unreal/AdaptiveMusicPlayer.md)
for Unreal. A Godot or Unity adapter needs only to start the layers on one audio-clock
boundary and feed `AdvanceTo` from that clock.

Tests: `c++ -std=c++14 tests/AdaptiveMusicTests.cpp -o adaptive-music-tests` covers
boundary waits for each boundary kind, equal-power midpoints, fade alignment, frame
partition invariance, hold, clock resynchronization, zero-length fades, invalid scores
and the engagement hold. Tower Assault (`TowerAssault.Audio.*`) is the first consumer;
audible synchronization is consumer-validated, not proven by these tests.
