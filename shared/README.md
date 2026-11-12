# Shared contracts

[Portable production clock](cpp/ProductionClock.md) provides a bounded recipe timer;
consumers own simulation steps, inventory and worker welfare.

[Portable grid routing](cpp/GridRoute.md) supplies deterministic construction-grid
paths and exhaustive route regressions. Consumers own placement transactions,
world coordinates and movement; no engine navigation parity is implied.

[Portable C++ stock ledger](cpp/README.md) provides bounded inventory transfers and overflow-safe sales without engine dependencies. Consumers own catalog identities, persistence and transaction authority.

[Migration contract](migration-contract.md) defines the common inputs, outputs and evidence for every workflow. Reuse it rather than copying a long process into each guide.

[Wizard templates](wizard/README.md) define guided workflows once (fields, stages, artifacts, checks); the GameCore hub, runner and ArcoreFlow nodes all derive from them.

[Subject profile taxonomy](subject-taxonomy/README.md) defines engine-neutral canonical parts, aliases, construction geometry, and composable subject-family profiles for assisted 2D, 3D, rigging, and gameplay tooling.

This directory is intended for engine-neutral schemas and contracts, not a universal wrapper around every engine. Save payload versions, content identifiers and validation conventions may be shared; scenes, physics and rendering implementations remain engine-specific.
