# Planar placement (0.1.0)

Engine-neutral deterministic bounded ring search for deployment and arrival reservations.
`FindPlanarPlacement` tries the preferred point, then each ring beginning on +X.
The callback supplies map legality and occupancy. A successful result must be
committed by the caller before processing the next reservation. Failed searches
leave the output untouched; callers must preserve the prior order or purchase.

Inputs require finite coordinates, positive finite spacing, 0–64 rings and
1–256 samples. Nonfinite generated candidates are skipped. Maximum callback count
is `1 + rings * samples`. Search exhaustion is not proof that no free point exists.
This is not pathfinding, continuous collision avoidance, network authority or
cross-platform lockstep trigonometry. Consumers choose occupancy layers and clearance.

Initial consumer: Sandbox Kingdoms, Unreal 5.8.4 Win64, solo/LAN arrival and
recruitment. Tests in `tests/PlanarPlacementTests.cpp` cover deterministic first
choice, exhaustion, output preservation, search bounds and invalid inputs.
Consumer runtime evidence is recorded in that game's Docs/ArrivalReservations.md.
