# Grid route contract

Version 0.2.0 adds `BuildGridDistanceField` and `NextGridStep` for many agents
sharing a goal. Cache a field until occupancy changes; each step then examines
at most four neighbours. Unreachable/blocked cells contain -1; invalid fields
return empty and invalid step queries return -1. At the goal, a step returns the
current cell. Equal routes prefer right/down/up/left. The original route API is
unchanged. Fields are caller-owned snapshots: stale fields must never be used
after construction edits. Tests compare field distances and complete step walks
against independent relaxation for all 41,472 small-grid endpoint cases.

`GridRoute.h` is an engine-neutral C++17 breadth-first route query for bounded,
four-neighbour, row-major construction grids. Nonzero occupancy blocks a cell.
Results include start and goal; invalid or unreachable queries return empty.
Neighbour order is deterministic: right, down, up, left. Dimensions above 4096
are rejected. Query on cell/route changes, not once per rendered enemy.

Consumers own world/grid conversion, movement and spawn/goal rules. Before
committing construction, query every spawn and active agent's reserved destination
against proposed occupancy. Reject overlap with agents and in-flight destinations.
This is not continuous physics, navmesh navigation or replication.

First consumer: Pocket Fort Patrol, Unreal 5.8.4 Win64. Consumer automation covers
shortest paths, edge wrapping, invalid input, sealed routes and rerouting.
Stage this header into a consumer dependency folder and record SHA-256;
packaged builds must never resolve a sibling checkout at runtime.

Standalone regression: compile `tests/GridRouteTests.cpp` as C++17 with assertions
enabled. It exhausts 512 occupancy masks and 81 endpoint pairs per mask, comparing
routes with independently relaxed distances (41,472 queries), plus invalid-input
and row-wrap checks. The consumer also runs this header in Unreal automation.
