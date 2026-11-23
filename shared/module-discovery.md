# Module discovery and growth architecture

Review date: 2026-11-22. Runtime code, installation metadata, discovery and project
assets have different owners. Keep a single authoritative source for each fact.

| Source | Owns | Entry point |
|---|---|---|
| shared/modules.json | Portable C++ module versions, hashes, dependencies and install contracts | tools/gamecore.py modules / sync / check |
| shared/reusable-modules.json | Procedure capabilities, source/docs, extraction status and reuse decisions | MCP reusable_modules (legacy) and module_search |
| tools/game_music_video.py MODULES | Godot vendor bundle membership; source files carry versions | vendor --module world-life or music-video |
| workflows/index.json and each wizard.json | Guided workflows and their stages | Workflow validator and hub wizard |
| hub/data and hub Store | Game projects, taxonomy and owned media | Project/media hub UI and tools |
| shared/ecosystem.json | Downstream service routing | Hub MCP only |

## Implemented discovery

The desktop **Modules** workspace uses the same Rust search function as MCP through
the `search_modules` command. It loads on demand, debounces queries, ignores stale
responses, pages results and exposes language/capability/reuse filters. Results
distinguish reusable source, game-specific candidates and legacy source; pilot or
extracted maturity is still shown separately. No category is a portability guarantee.
The C++ catalog's Unreal adapters are labeled Unreal C++, not portable C++.

Select a module for boundaries, source/consumer/test references, versions, and
examples extracted from its Markdown guide. Guides are read only through a known
catalog key and a path constrained to the original GameCore checkout. Missing or
moved guides show an explicit error; examples are rendered as text and never run.
Browser preview directs users to the desktop app; it does not pretend to be live search.

**Game catalog tags:** module details can add/remove a qualified module key on a
game. Adding also adds its language tags, preserving languages inferred from old
engine descriptions. Removing a module retains language tags because other code may
still use them. Edit project → Language tags changes the saved language list.
Game library filters accept both language and saved module references. Games with
no saved languages use conservative inference from their existing engine text;
unknown languages are not guessed. No catalog-wide metadata rewrite occurs on load.
Tags are discovery references, not verified installs or automatic vendoring. They
do not change capability maturity, source files, lockfiles or game runtime behavior.

See the [language guide](module-languages.md) for C++, C#, GDScript and tooling
boundaries. Search additionally supports `language` and `capability` filters;
capability IDs reuse the existing hub taxonomy. Summaries expose languages,
capability IDs and source project IDs. Legacy C# entries are source-only, not
newly tested or vendored modules.

`module_search` federates the two module catalogs without duplicating their install
rules. It parses and normalizes metadata once per hub process, precomputes search
text and uses a hash index for exact qualified keys. No code or assets are loaded
or executed for search. Portable and procedure IDs are namespaced to avoid collisions.

```json
{"query":"terrain clearance","limit":20}
{"catalog":"procedures","state":"extracted","query":"cue"}
{"key":"procedures:reef-clearance","details":true}
{"key":"portable:buoyancy","details":true}
```

Whitespace query terms are case-insensitive AND substrings of ID, name/description,
engine, dimension, tags and aliases. Filters catalog/state/engine/dimension are exact;
use values returned in summaries. Portable modules use engine `portable-cpp` and
dimension `any`. This is deterministic metadata search, not semantic similarity.
Add useful aliases/tags to canonical entries when common vocabulary misses a module.
Consumer paths and limitations are available in details, not indexed as capabilities.

Default limit 20, maximum 100; use `next_offset` until null. Results sort by qualified
key so paging is stable within a build. `details: true` includes the original entry;
default responses stay compact. Unknown exact keys return zero results. Candidate
and pilot status remain visible; finding a module does not certify reuse or install it.
`reusable_modules` remains backward-compatible and unpaged; prefer `module_search`
for new discovery flows. Legacy registry parsing is now cached too.

Catalogs are embedded at compile time. Rebuild and restart the hub after registry
changes; a long-running older process keeps its prior snapshot. Releases should pin
the hub build alongside catalogs. No hot reload or external search service is present.

## Growth decisions

- Keep engine-specific runtime code separate from neutral contracts. Game content
  stays in adapters; enforce the reuse suitability review before new shared APIs.
- Keep module IDs stable. A display-name change must not change a key. Add dependencies
  to the authoritative installer contract, not to a parallel search-only graph.
- Preserve hash-locked vendoring and explicit upgrades. Runtime games must not depend
  on the hub, registry or another local checkout being available.
- The current world-life bundle is convenient but broad (21 files). If independent
  release cadence or footprint becomes a problem, introduce additive focused bundles
  (coverage, timeline, terrain) with explicit dependencies; retain the old bundle as
  a compatibility aggregate. Do not silently move consumer paths or fork shared code.
- Catalog editing is still centralized JSON. Split into per-module manifests only
  when merge contention or ownership warrants it; generate the aggregate deterministically
  and validate unique keys/links/dependencies in CI rather than hand-maintaining copies.
- Search is O(N) over precomputed metadata for free-text/filter queries, O(1) expected
  lookup for exact keys, O(N) memory. Pagination bounds output, not matching work.
  A 10,000-entry synthetic debug-build test took about 116 ms to construct and 4 ms
  for search on the development machine. This is one measurement, not an SLA or
  a production benchmark. Profile realistic catalogs before choosing an inverted
  index/SQLite FTS; use a measured latency or memory problem as the trigger.
- Workflow and game-project search remain separate. This change federates module
  discovery only; it does not claim a universal search over assets or workflow text.
- The current UI build emits a roughly 2 MB JavaScript chunk (about 347 KB gzip).
  Lazy-load large workspace routes if startup measurements show a bottleneck;
  this review does not claim UI bundle splitting or native atlas search changes.

## Admission and validation

For every addition: stable ID, clear capability name, engine/dimension, source and
guide links, limitations, reuse decision, and focused tags/aliases. Run registry
link/unique-ID tests and the selected module/consumer regressions. Search tests cover
both catalogs, exact lookup, multiple query terms, invalid arguments, pagination
and a 10,000-entry synthetic catalog. Keep manual review of portability and rendering
separate from registry integrity checks.
