# Interaction rules (C++17)

Engine-neutral, header-only range and cooldown predicates. Use squared distances in a consistent unit, and an authoritative monotonic game clock for cooldowns. Boundaries are inclusive; negative and nonfinite distance/radius inputs fail closed. Callers own actor identity, authority, line of sight, ownership and cooldown mutation. These predicates alone do not validate an interaction.

First consumer: Haunt and Haul, UE 5.8.4 / Win64. The consumer stages a SHA-256-pinned copy into its source tree so packaged builds do not depend on sibling checkouts. Unreal automation covers valid boundaries and invalid values alongside the game's authoritative interactions. Live multiplayer acceptance remains separate.

## Version 0.2.0: nearest eligible candidate

`NearestCandidate::Consider(index, squaredDistance, radius, eligible)` retains the closest valid candidate and returns whether the choice changed. Invalid IDs, nonfinite or negative distances, out-of-range and ineligible candidates do not mutate the selection. Equal distances preserve the first candidate; consumers must supply a stable ordering if ties require deterministic identity. Visibility, authority and ownership remain caller-owned.

Haunt and Haul now shares its target resolver between context prompts and authoritative actions, and uses this helper for props and capture targets. The registry pins version 0.2.0; prior installed header copies remain independent. `tests/InteractionRulesTests.cpp` provides standalone assertions, and the consumer also runs native Unreal boundary, selection and gameplay regressions.
