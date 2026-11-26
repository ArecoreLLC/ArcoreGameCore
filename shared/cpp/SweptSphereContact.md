# Swept sphere contact 0.1.0

`GameCore::SweptSphereContact(from, to, combinedRadius)` takes relative center
positions as `std::array<double,3>`. It tests the closest point on a finite linear
segment against a sphere at the origin. Endpoints and tangencies count. Invalid
coordinates and negative/nonfinite radii return false; zero radius is supported.
Normalization prevents overflow before subtraction and squared distance.

No state, allocation, engine types, clock or gameplay policy. Requires C++17.
Consumers own authority, motion sampling, reset/teleport exclusion, collision
response and optional subdivision of curved paths. This is not a full physics
sweep and does not return contact time or normal.

Reuse review: extract stable geometry; retain damage, radii and motion in the
consumer. Portable tests include a synthetic tiny proximity sensor and extreme
coordinates, not second-game validation. First adapter: Skybound-Sabotage's
server wrecking-ball contact. See its Docs/POLISH_PASS.md for executed evidence.
