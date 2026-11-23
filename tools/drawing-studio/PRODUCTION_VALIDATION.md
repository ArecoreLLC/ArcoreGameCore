# Drawing production validation

Baseline: GameCore `283e5b3` plus the working changes introducing `drawing_production`.
Platform: Windows, Python 3.14.0, Pillow 12.1.0, Node v24.11.0; Rust debug and release
hub builds. Consumer: ShammyVerse, Godot 4.7.2, 3D Canvas Cay red panda study.

Passed commands:

- `python -m unittest discover -s tools/drawing-studio -p test_production.py -v`: 7 tests.
- `python -m unittest discover -s tools/drawing-studio -p test_render_gif.py -v`: 4 tests,
  including Draw & Paint producing visible drawing in its first interval, with zero
  construction strokes and no blank construction lead-in.
- `cargo test --manifest-path hub/src-tauri/Cargo.toml`: 15 tests.
- `cargo build --manifest-path hub/src-tauri/Cargo.toml` and its `--release` variant.
- `python tools/validate_workflows.py`, `python tools/validate_wizards.py`,
  `python tools/mcp_registry.py`: passed.
- `python -m unittest discover -s tools/tests -v`: 163 tests, one optional Godot
  component test skipped because that test's `GODOT` environment variable was unset.

Real hub MCP checks (not just direct Python dispatch):

- `tools/list` exposes `drawing_production` in the release executable.
- Nested discovery returns guide/import/validate/render/job schemas.
- Imported the consumer reference; exact original retained, fitted lesson returned.
- Empty-guide personal lesson rendered in `trace` mode.
- Authored red panda lesson rendered in `advanced` mode (390 frames, 51 s).
- Disconnected after launch, then polled durable job receipts to `passed`.
- Repeated both render requests: `reused: true`, same job paths, output hashes verified.

Consumer evidence stays under `X:/Projects/GameVideo/ShammyVerse/art-studies/` and
its game repository's `Design/Iterations/red-panda-painting-v001/work/`. The private
reference is not copied into GameCore. The edited consumer movie passed ArcoreCut's
8,121-frame and continuous-audio equality checks. Gameplay was tested separately.

Limits: no full user study, no automatic anatomical correctness, no arbitrary
personal-art 3D reconstruction, no in-game upload UI, no second-game/engine
portability claim. CLI/import provenance does not establish artwork rights or
human visual approval. No publication was performed.
