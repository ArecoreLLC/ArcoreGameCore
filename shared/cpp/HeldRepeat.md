# Held repeat 0.1.0

Reuse review (2026-11-24): extract-adapter. Responsibility: caller-clocked held
input repeat with separate first delay and subsequent interval. No engine, key,
actor, asset, or game dependency. ActionCooldown handles absolute-time admission
but has no held-input lifecycle or first-repeat delay; retain it unchanged.
Press returns true once until Release; Advance returns at most one repeat per
call. Invalid/nonpositive deltas preserve state; a hitch drops backlog. Consumers
own target locking, action eligibility, opposing inputs, focus-loss and terminal
reset. This contract deliberately favors predictable controls over catch-up.
Constructor rejects invalid timings using defaults (.4/.18 seconds).

Synthetic menu stepping and dial adjustment use different timings in the portable
tests; these are not second-game evidence. Lumen-Weaver owns mirror target/range
checks and uses Release on target loss. Existing module APIs are unchanged.
Tests: shared/cpp/tests/HeldRepeatTests.cpp; consumer Interaction.Focus.
Workflow: game-project-integration, 3D; UE 5.8.4 Win64 C++, existing dirty working
tree baseline. Acceptance: single press, delay, repeat, hitch, release/repress,
invalid input, target loss and restart. Actual results in consumer validation.
