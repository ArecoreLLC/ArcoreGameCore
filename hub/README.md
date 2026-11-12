# GameCore studio library

A Windows Tauri 2 desktop catalog backed by local SQLite. Browse games, compare reusable mechanics, inspect source and asset indexes, classify portfolio capabilities, and curate marketing media without modifying the original game projects.

## Run

Open `Launch-GameCore.cmd` in the repository root. It prefers the release build and falls back to the development build. Microsoft Edge WebView2 must be installed.

From `hub/` in PowerShell:

```powershell
npm.cmd ci
npm.cmd run tauri -- dev
```

Build a standalone Windows executable:

```powershell
npm.cmd run tauri -- build --no-bundle
```

Output: `src-tauri/target/release/gamecore-library.exe`. Rust/MSVC C++ build tools and WebView2 are required to build. This first version has no installer or signing configuration. `npm.cmd run dev` is a read-only browser preview; it does not substitute browser storage for SQLite.

## Library contents

Initial audit: November 11, 2026. There are **31 primary game/collection records, 88 named mechanic records, 21 embedded ShammieQuest arcade games and 240 specific capabilities in 30 groups, plus 57 broad classification domains**. The file index contains **5,623 source records and 52,653 asset records**. These are file/version counts, not unique licensed models or verified reusable modules.

The scope includes all 16 consumers directly under `X:/Projects/Games`, game projects directly under `X:/Projects`, and detected older games/educational collections in `Repo-Library`. ShammyVerse VR is a separate runtime entry. Plumpy Adventures' Godot port is a variant of its Phaser game. The extra TowerAssault source copy under ArcoreClaw and ShammyVerse publishing snapshots are identified, not counted as new games. Conversation play contexts in `plumpy-dot` are references, not independent game implementations. GameCore, ModelForge, SoundCore and WorldFramework are tooling rather than games.

Discovery combined engine descriptors, package dependencies, top-level directories and targeted source/README inspection. Build outputs, dependency/cache directories, publishing snapshots and junctions are excluded from traversal. A curriculum collection can contain plans and worksheets alongside working activities; inclusion does not certify every lesson as a playable game. Unknown unrecognized game formats may need manual addition.

Descriptions identify current rules, source entry points, reuse boundaries, asset types, engine/platform and historical evidence. Historical pass records are explicitly separate from fresh tests. **No game was built, launched or playtested as part of this catalog audit.** The hub itself has separate native tests.

## Use the catalog

1. Search the library by game, mechanic or asset description. Filter by engine or capability.
2. Open a game. Overview explains the loop and constraints; Mechanics records individual rules and source locations.
3. Assets describes available characters/props/worlds/rigs/materials/audio and searches the indexed original paths. Source files have audit hashes; binary assets remain unpinned and rights-unreviewed until admitted for reuse.
4. Provider cards link to **ArcoreModelForge**, **ArcoreSoundCore**, and **ArcoreSonicAlchemist** folders. Edit each card to record the exact asset/collection/project ID and version. These are references, not new direct MCP connections or mirrored provider databases. The ecosystem hub remains the only registered agent MCP entry point.
5. Evidence retains revision, source document paths, historical checks, and documented commands. Run future checks in the consuming game's own environment.
6. Edit a record or add a new project. Adding a record does not create/alter a game folder. The capability atlas highlights existing donors and uncovered areas; see [classification guidance](TAXONOMY.md).

## Game roadmap

The **Game roadmap** view contains 50 proposed game tracks in six waves, with 330 game–capability assignments covering all 143 original capability gaps plus 3 failure-case capabilities. Additional tracks demonstrate second consumers and integrated gameplay; an assignment is not implementation evidence. The source plan is [capability-roadmap.json](data/capability-roadmap.json).

Choose **Export JSON** on the roadmap or a game detail to preview a review package, then **Copy JSON** or **Save JSON file**. It exports all games regardless of filters, reads the current saved roadmap, and includes any current unsaved game draft with an explicit marker. The package includes capability definitions, donor code/asset descriptions and provider references, priorities, milestone dependencies, progress/evidence, larger-game combinations and questions for another LLM. Shared descriptions are normalized; empty progress fields are omitted. Notes and local reference paths are included, but source/media file contents are not. Export is a snapshot, not a round-trip import feature. If clipboard access is unavailable, the text is selected for manual copying. Native file export chooses a folder and writes a uniquely named UTF-8 JSON file without overwriting earlier exports.

The current launcher prefers the JSON-export release in `src-tauri/target-json-export/release/`, built separately to leave an already-running app undisturbed. To rebuild that release, set `$env:CARGO_TARGET_DIR='X:\Projects\ArcoreGameCore\hub\src-tauri\target-json-export'` before `npm run tauri -- build --no-bundle` from `hub/`.

Open a track to edit priority (lower numbers first), owner, status and notes. Prerequisites reference specific capability milestones; select the required targets rather than waiting for every stretch goal of a predecessor. Dependency and downstream links navigate between tracks. Cycles are rejected; an unmet prerequisite is visible but does not prevent independent work.

Each capability has planned, in-progress, blocked, implemented, verified and reused states. Verified targets require revision/build, platform/hardware, test procedure and evidence. Reused also requires a second consumer and its acceptance evidence. A game cannot be marked completed until all its targets are verified/reused. These are recorded acceptance claims, not automatically executed tests. Roadmap progress does not silently change the source catalog or capability atlas.

Donor cards include code entry points matched to the file index, asset descriptions, game-record links, and source/provider folders. Search indexed source or asset files and pin exact references to the selected target, including version/hash and notes. File links reveal the indexed file in Explorer without running it; stale/missing files report an error. Provider folders retain ModelForge, SoundCore and SonicAlchemist ownership and existing integration boundaries.

SQLite adds `roadmap` and `roadmap_history` tables without replacing projects, taxonomy or media. Startup inserts missing tracks only; existing priorities, progress and notes survive reseeding. Version checks prevent stale windows from overwriting roadmap changes. Ordinary library backup includes both tables. Browser preview is read-only. Save changes before leaving a track; the app prompts before discarding unsaved edits.

Roadmap checks: `npm test`, `cargo test --manifest-path src-tauri/Cargo.toml`, and `node tests/roadmap-smoke.mjs` from `hub/`. The native roadmap test snapshots the current library into an isolated directory, edits only that copy, and tests reference pinning, evidence gates, dependencies, backup and restart persistence. It reserves port 9449 for its bounded lifetime.

## Marketing media

Each game has separate marketing copy and a media collection. Import PNG/JPEG/WebP screenshots or MP4/WebM/MOV videos/trailers. Imports stream into content-hashed managed storage; originals are preserved. Display order, captions, alt text, rights notes, credits and review state are editable. Image/video dimensions and video duration are captured when the native preview decodes them and the review is saved.

Media starts as **draft**. Approval requires a title, caption and rights note, plus alt text for images. Review is a human decision, not automatic legal clearance. Retiring media keeps its source and history-bearing record. Preview codec support depends on WebView2; a stored MOV or MP4 is not a promise that its codec will play. No transcode, trailer generation, remote download or publishing service is included.

Export creates a new, uniquely named press-kit folder containing approved media, hashes, captions, rights/credits, `press-kit.json` and `README.txt`. Private source paths, technical catalog records and internal marketing notes are excluded. Copies are hash-verified. Failed exports retain an `EXPORT_INCOMPLETE.txt` marker. Nothing is uploaded or published.

The November 11 curation imported 38 screenshots and 6 videos across 21 projects into the default library. Two images are reference-only. The backlog currently flags 12 projects needing screenshots/reshoots, 30 needing a gameplay/scene clip, and all 31 needing a trailer. See [the selection manifest](data/marketing-selection.json) for source hashes, captions and review rationale. Editorial selection and publication approval are independent. Asset demos and long story walkthroughs do not satisfy the gameplay-clip or trailer requirement.

Discovered capture candidates are original project paths, not pre-approved promotional material. They must be imported and reviewed before export. No game captures or trailers are fabricated by the catalog.

## Storage and recovery

Default Windows storage: `%APPDATA%/com.arcore.gamecore/`:

```text
catalog.sqlite3       SQLite schema version 1, WAL mode, foreign keys
media/                Content-addressed managed image/video copies
```

Projects, taxonomy, indexed files, media and seed metadata use separate tables. Project metadata remains extensible JSON inside the project table. Seed import is transactional and runs once; rebuilding/relaunching never replaces editorial changes. No credentials are stored in the catalog seed.

**Back up library** uses SQLite's online backup API and copies managed media into a new directory. To restore: close GameCore, preserve the existing data folder, and replace its database/media with the backup. Do not retain old `catalog.sqlite3-wal` or `catalog.sqlite3-shm` alongside a restored database. On startup, managed media paths rebase to the current storage directory. A restored library retains source project/provider paths, which may require relinking on another machine.

`GAMECORE_DATA_DIR` overrides storage for isolated tests. Native smoke tests use a fresh directory under `test-results/` and never operate on the user's default library. Do not set this variable for ordinary launch unless intentionally selecting a different library.

## Refreshing the source audit

```powershell
python scripts/audit_catalog.py
```

The script refreshes only known catalog roots and filesystem-derived evidence. It does not execute game code, contact asset services or alter editorial mechanic/description/provider records. It writes `data/catalog.json` and `data/files.jsonl`. Review generated differences before including a new seed in a build. Existing live SQLite libraries are intentionally not overwritten by a rebuilt seed; edit records in the app. An interactive rescan/merge workflow is future work.

The source index is a point-in-time inventory. It can become stale as other projects change. For reuse, reopen the source, pin its version, inspect direct dependencies, verify rights/units/pivot/rig/collision/materials, and validate a small slice in the receiving engine. Reuse across engines requires an explicit adapter or port.

## Checks

```powershell
npm.cmd test
npm.cmd run build
cargo test --manifest-path src-tauri/Cargo.toml
npm.cmd run tauri -- build --debug --no-bundle
node tests/native-smoke.mjs
```

The native smoke launches an isolated WebView2 app with a temporary local debugging port, tests actual UI/database/media commands, verifies restart persistence, records screenshots/results and closes only its owned process tree. It needs the development executable, or `GAMECORE_TEST_EXE` pointing at another built executable. Do not run two copies of this smoke test concurrently; port 9447 is reserved for its bounded lifetime.

Repository checks run from the GameCore root:

```powershell
python tools/validate_workflows.py
python tools/validate_wizards.py
python tools/mcp_registry.py
python -m unittest discover -s tools/tests -v
```

See [validation record](VALIDATION.md) for executed results. The broader workflow hub, wizard runner and downstream service automation remain the separately proposed design in `docs/GAMECORE_HUB_AND_WIZARD_DESIGN.md`.

## Apply this catalog update to another existing library

Close older app windows before editing in the new build to avoid saving stale records. Run from the repository root, with the original media sources available:

```powershell
python hub/tools/apply_catalog_update.py --library "$env:APPDATA/com.arcore.gamecore"
```

The updater backs up SQLite and existing managed media, verifies source hashes, and merges missing classifications and media. It preserves existing project prose, marketing copy and media edits; repeat runs do not duplicate selections. Fresh libraries receive the expanded taxonomy from the seed, but local marketing binaries are imported explicitly rather than bundled into the executable. Browser previews do not expose local media.

## Feedback revision (November 11, 2026)

The review revision retains 50 stable track IDs and assigns each of 146 capabilities to at least two planned consumers. The taxonomy now has 243 capability leaves and 57 domains. Gravity Parcel is repurposed as Relic Rematch; Salvage Submersible becomes Relic Gallery. Their overlapping chapters move into Moonbase Freight and Reef Keeper. Creative/visual briefs are inspiration, separate from acceptance scope.

Prerequisites now name producer capabilities and distinguish first-slice gates from later milestones. The readiness filter uses first-slice gates. Cross-engine donors identify behavior contracts and consumer-owned adapters. JSON exports include review decisions, creative briefs, stages, provenance requirements, archived target progress and an ID inventory to check completeness.

On startup the native app applies the revision transactionally to existing SQLite libraries. Ownership, notes, priority and matching target progress survive; removed target progress and prior dependencies are archived, and each original row is retained in roadmap history. Plan dependencies are replaced with the reviewed graph. Completed tracks with new unaccepted targets reopen as active. Versions advance to reject stale writes; repeated startup is idempotent. Project records, marketing records and media files are untouched. Back up an existing library before upgrading. The supplied review and editorial decisions are preserved in `evidence/roadmap-feedback-2026-11-11/`.
