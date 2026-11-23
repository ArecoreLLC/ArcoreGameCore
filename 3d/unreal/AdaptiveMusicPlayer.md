# Unreal adaptive music player 0.1.0

Unreal 5.8 adapter for [adaptive-music](../../shared/cpp/AdaptiveMusic.md). Select both
modules; install them side by side (for example `Source/<Game>/Public/ThirdParty/`).
Add `AudioMixer` and `Json` to the consumer module's dependencies.

```cpp
// Owner: a long-lived actor such as the GameState. Keep the player in a TUniquePtr member.
Music = MakeUnique<Arcore::Unreal::FAdaptiveMusicPlayer>(MyScore());
Music->Start(*this, {StringsWave, PercussionWave, DrumsWave, BrassWave}, TEXT("MyGameMusic"));
// Each tick (also while paused if the score should keep fading):
Music->Tick(DeltaSeconds, DesiredState, UserVolume * Duck);
// EndPlay:
Music->Stop();
```

- **Sample-locked start.** Every stem is queued on a stopped Quartz clock with
  fire-on-start, then the clock starts after `LeadSeconds` (default 0.25 s) so streamed
  stems can prepare. All voices begin together at transport 0 with an S-curve fade-in
  (one bar by default).
- **Audio-clock transitions.** The mixer follows the Quartz transport, which advances
  with rendered audio, so boundaries stay on the music's beats through hitches and long
  sessions. Without an audio device or Quartz (for example `-nosound` or a null device),
  stems start directly and the mixer runs on frame time.
- **Lifetime.** Audio components are created with the owner actor as outer and are
  destroyed with it; the player also reports them and the Quartz handle to the garbage
  collector through `FGCObject`. Do not hold it beyond the owner's world.
- **Waves.** Stems must be in score layer order. The player sets looping and
  `PlayWhenSilent` in memory; the Sonic-v001 importer sets both on the assets. Cook the
  music folder when stems are loaded with `LoadObject`.
- `ParseAdaptiveDesign(json, score, &error)` reads a design.json into a score. Use it in an
  editor contract test that compares a game's compiled score with its exported design,
  or at runtime when the design file is staged with the build.

Volumes floor at −80 dB rather than zero while music is audible, so silent layers remain
real voices. `Level` 0 silences everything. The caller owns state choice, pause and
ducking policy, and per-player clock names. Validation is consumer-owned: Tower Assault
checks four playing stems on a running clock in its sound-enabled playtest. Audible
alignment and packaged behavior on other platforms are not yet verified.
