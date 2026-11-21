# Animate integration

GameCore owns orchestration and pipeline receipts; ArcoreAnimate owns editing,
tracking, retargeting, move baking, companion packs and durable worker jobs.
Register only the GameCore MCP hub with clients. The `arcore-animate` downstream
provider is declared in `shared/ecosystem.json` and uses Drawing Atelier's vision
Python from sibling checkouts. Build the hub after changing this integration.

`animation_production` accepts `operation` plus `arguments`. Use operation
`tools/list` with `{}` arguments to discover all 22 downstream schemas. Start the
case with `animate_app` (`action: start`, `case_id`), then use the case-specific
operations. The thin stdio provider connects to the app's authenticated loopback
service; it does not maintain independent editor state.

`animation_pipeline` accepts actions `start`, `status`, `cancel`. Start requires
`case_id` and a `stages` list drawn from `track`, `refine`, `retarget`, `bake_moves`.
Baking also requires the current `moves_revision` from `animate_moves`; `sequence`
may supply a list of move IDs including repeats. Status/cancel require `run_id`.
Poll status until terminal: status calls advance stages, not a background scheduler.

Receipts live in `GAMECORE_DATA_DIR/animation-runs`, defaulting to
`%APPDATA%/com.arcore.gamecore/animation-runs`. Deterministic stage request IDs allow
retry after a lost response without duplicating Animate jobs. A hub crash can leave
a `.lock` file; inspect the run and active processes before removing it. Failed,
cancelled or interrupted stages stop the run. Animate service restarts mark its
unfinished jobs interrupted. Rendering never automatically approves or publishes
assets to a game.

Full setup, operation coverage, companion limits and validation:
[Move Workshop guide](https://github.com/ArecoreLLC/ArcoreAnimate/blob/main/docs/MOVE_WORKSHOP.md).
The opt-in `studio/hub_smoke.py` in Animate discovers the provider through this hub
and bakes a repeated Poofy choreography, requiring local game assets and retarget
outputs. The regular `hub/tests/media-mcp-smoke.py` checks hub discovery and existing
media behavior without those assets.
