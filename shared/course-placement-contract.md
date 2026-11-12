# Course placement contract v1

`tools/course_contract.py` validates engine-neutral placement rectangles and emits an optional dependency-free C++17 header. This is a source preflight, not a route-solvability, physics, multiplayer, or playtest certificate. Runtime behavior belongs to the consumer.

A manifest declares `schema_version: 1`, `units: "centimeters"`, a `grid` in 0.001–10,000,000 cm, `max_pieces` (1–1024), `bounds: [min_x, min_y, max_x, max_y]`, `protected_zones` rectangles, and `pieces`. Each piece has a unique `id`, positive `half_extent: [x,y]`, and nonnegative `travel: [x,y]`. Absolute numeric values are limited to 10,000,000 cm for safe native float generation. The conservative motion envelope is half extent plus maximum anchor displacement on each axis. Rectangles that only touch do not overlap. Use inflated extents when clearance is required.

`placement(data, kind, x, y, occupied)` checks finite coordinates, grid alignment, full envelope containment, protected zones, occupied envelope rectangles and capacity. Call `validate` on the manifest first. The engine adapter must repeat these checks on its authority, validate height separately and enforce phase, inventory and ownership rules. Clients must not authorize placement.

```powershell
python tools/course_contract.py <consumer>/Config/Course.json --header <consumer>/Source/CourseContract.h
python -m unittest discover -s tools/tests -p test_course_contract.py -v
```

The generated header embeds the source SHA-256 and contains no absolute path or runtime checkout dependency. Keep the manifest, generated header and generator source hash in consumer evidence. Run generation before native builds; unchanged output is not rewritten. Values are XY in centimeters; the consumer supplies the vertical placement plane. Moving pieces must remain within their declared travel envelope. An engine automation test must check adapter boundaries against this contract.

Initial consumer: Skybound Sabotage (Unreal 5.8.4, Win64, 3D). Its rules, native actors, map and playtest evidence remain in that project. Legacy Godot runtime is unchanged. This addition does not claim general navigation or networking support.
