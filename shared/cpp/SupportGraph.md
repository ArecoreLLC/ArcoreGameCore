# Portable support connectivity

`SupportGraph.h` is a header-only, engine-neutral C++14 rule in namespace `GameCore`. Nodes have positive finite health and an optional ground anchor; undirected edges represent authored structural joints. It has no engine, physics, IO or sibling-checkout dependency.

`Configure(nodes, edges)` validates the entire input before replacing state. Out-of-range edges, self-edges, nonpositive/nonfinite health and initially detached nodes are rejected. Duplicate edges and empty graphs are valid. Components without a living anchor immediately detach, including isolated cycles. Configure is a new topology, not a runtime reconnection API.

`Damage(index, amount)` accepts only finite positive damage to attached nodes, clamps health at zero and recomputes reachability from living anchors. It returns whether damage was accepted, not whether collapse occurred. A redundant route preserves support. Detached nodes stay detached until reset or configure. Read `GetNodes()` before and after a mutation to find newly detached pieces; references are invalidated by configure/reset.

`Reset()` restores original health/topology and recomputes connectivity. The adapter owns damage targeting, rendering, debris limits, physics, transforms and velocity reset. Ground anchors are authored facts, not inferred from collision contacts. This models connectivity, not load-bearing capacity or cardboard deformation. Execution is synchronous, single-threaded, with O(V*E) traversal: intended for small authored forts, not large destruction simulations.

First consumer: Box-Fort Brigade, Unreal 5.8.4 Win64. Its `BoxFortBrigade.GameCore.SupportGraph` automation covers chain failure, redundant anchors, upper cuts, reset, overkill, terminal state, malformed input, NaN/infinity, cycles and empty topology. Engine compilation and physics/playtest evidence are separate. Consumers should vendor a hash-pinned copy and retain engine adapters locally; shipped games need no framework checkout.
