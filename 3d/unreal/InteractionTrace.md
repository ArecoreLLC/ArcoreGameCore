# Unreal interaction trace 0.1.0

Unreal 5.8.4 / Win64 pilot, header-only; requires Core, CoreUObject and Engine.
`TraceInteraction` returns the first blocking hit within a preview distance and
whether its surface is within the inclusive action reach. Direction is normalized;
units are Unreal world units. The optional ignored actor is normally the player.
The default channel is Visibility. Zero direction, invalid/nonfinite geometry,
negative reach, nonpositive preview range and reach greater than preview range
return an empty result. Starting inside a blocker never grants action eligibility.

Consumers filter the returned actor, own terminal-state/authority rules and use
the same query for prompts and actions. Query again at action time; never authorize
from cached HUD state. This helper does not search through occluders or choose
nearby off-axis targets. Components must block the selected trace channel.

Initial consumer: Lumen-Weaver. `LumenWeaver.Interaction.Focus` tests native world
occlusion, range, invalid inputs, ignored player, mirror rotation and terminal
states. Actual execution evidence is in the consumer's Docs/VALIDATION.md and
Saved/GameCore receipts. No multiplayer, packaged or second-consumer claim.
