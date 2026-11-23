# Languages and reuse boundaries

GameCore contains several implementation languages, not one interchangeable
runtime. Search with MCP `module_search`, `language: cpp|csharp|gdscript|python`.
Summaries include `languages`; canonical details preserve engine/version constraints.

| Language | Location and examples | Integration boundary |
|---|---|---|
| C++ (`cpp`) | shared/cpp headers; attachment, buoyancy, combat windows, routing | Portable rules installed by tools/gamecore.py; engine adapters remain consumer-owned. Unreal framework integrations are documented separately in framework/UNREAL_INTEGRATION.md |
| C# (`csharp`) | autoload services/platform adapters; scripts/visual and scripts/definitions | Legacy Godot .NET foundation. Local ArcoreGameCore.csproj targets Godot.NET.Sdk 4.3.0 and net8.0; inspect/build for the intended target before adopting. These are not plain engine-neutral .NET utilities |
| GDScript (`gdscript`) | 3d/godot/world_life and music_video, editor plugin | Godot runtime helpers; ShammyVerse uses the 4.7.2 console engine for tests. Vendored bundles are hash-locked; no C#/.NET requirement is introduced by these helpers |
| Python (`python`) | tools, drawing-studio; consumer Blender authoring candidates | Development/production tooling. Blender bpy code needs Blender; generic Python and Blender Python are not interchangeable. These tools are not a shipped game runtime dependency |
| Rust | hub/src-tauri | Hub, SQLite persistence and MCP orchestration, not a gameplay module; currently outside module-search catalogs |
| JavaScript/TypeScript | hub UI and legacy porting CLI | UI/development tooling; no automatic runtime-language migration |

The three legacy C# catalog entries expose services, platform adapters and visual
components as source discovery only. Resource definitions remain documented in
the legacy guide. No C# build, export, missing Boot scene repair or port is claimed
by this change. Legacy SaveManager is not a drop-in replacement for ShammyVerse's
validated save rotation. Existing class names do not prove equivalent guarantees.

For reuse, choose the implementation matching the consumer's engine/language and
target. Port pure logic deliberately when needed; retain tests/behavioral contracts
and document the new implementation separately. Do not imply that importing a C++
header into Godot, copying a .cs file into a non-.NET build, or changing an export
preset translates languages or establishes platform compatibility.

Before adoption record language, engine/SDK version, runtime versus tool role,
dependencies, installer, supported/tested targets and validation gaps. Apply the
[specialization review](module-specialization.md) to each implementation; don't
merge unrelated language variants merely because they share a display name.

## Existing catalog data

The hub seed already contains 31 project records and 300 taxonomy records at this
review. Project engine descriptions, mechanic source references, reuse boundaries
and validation notes are useful donor evidence. `capability_ids` on procedure
entries reference that existing taxonomy; `source_project_ids` link to its project
IDs. For example, reef clearance links to `cap-terrain-height-sampling`, and save
rotation references the existing `shammyverse-3` autosave mechanic. These are
classification/source links, not promotions to verified/reused maturity.

Search can filter by `capability` using those IDs. Keep taxonomy labels and project
descriptions in the hub catalog rather than duplicating them in each module.
Seed records can lag current source; the live SQLite library can also have user
edits. This task links to seed IDs and does not overwrite live project records,
media, roadmap progress or historical evidence. Searching live mechanic text from
the module endpoint is not implemented; use the existing hub capability atlas.
