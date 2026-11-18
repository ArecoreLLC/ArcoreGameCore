# Unreal game-feel helpers

The GameCore Unreal runtime provider, ArcoreWorldFramework, owns the version 1
`FArcoreInputBuffer` and `FArcoreFeedbackPulse` contracts in
`Unreal/ArcoreFrameworkRuntime/Source/ArcoreFrameworkRuntime/Public/ArcoreGameFeel.h`.
Enable and depend on `ArcoreFrameworkRuntime`; include `ArcoreGameFeel.h`.

Read the provider workflow at `../ArcoreWorldFramework/docs/workflows/game-feel.md`
for update order, expiration and reset semantics. Gameplay eligibility, input
bindings, visuals and tuning stay with the consumer. Native regression suite:
`Arcore.Runtime.GameFeel`. These are Unreal helpers, not cross-engine or multiplayer
certification. Package the plugin with shipping consumers; sibling source checkouts
are only a development setup.
