# Roadmap feedback revision - November 11, 2026

Applied `review-2026-11-11-v1` to the live Windows SQLite catalog and built the release launcher target. The review now covers 50 games, 146 distinct capability targets and 330 assignments, with at least two planned consumers per target. The 143 original gaps remain assigned; three failure-case capabilities were added. No game capability was promoted to implemented/verified/reused.

Passed: `npm test` (12 tests), `cargo test --manifest-path src-tauri/Cargo.toml` (9 tests), `npm run tauri -- build --no-bundle`, `node tests/roadmap-smoke.mjs` and `node tests/roadmap-export-smoke.mjs`, all from `hub/`, with `CARGO_TARGET_DIR=X:/Projects/ArcoreGameCore/hub/src-tauri/target-json-export`. Native tests use isolated libraries and owned process trees. The stage-control label failure found on the first native pass was fixed; the final pass includes editing and persisting a later-stage gate. Vite's bundle-size warning remains non-blocking.

Upgrade tests cover preservation of owner, notes, priority and target state; archival of retired target evidence; stale-edit rejection; new taxonomy insertion; and idempotent startup. Live comparison confirmed all 31 project records, all 46 media records, all original taxonomy rows and all matching/archived target progress were preserved. SQLite integrity passed with zero foreign-key violations. The pre-update SQLite backup and 50 original roadmap history records are retained. Native roadmap screenshot visually checked.

[Review decisions and per-capability consumer inventory](evidence/roadmap-feedback-2026-11-11/decisions.json), [live update receipt](evidence/roadmap-feedback-2026-11-11/live-update.json), and [exact source/executable hashes, base revision and checks](evidence/roadmap-feedback-2026-11-11/validation-receipt.json) record the result. The original external review is retained alongside them. Its incomplete-count claims were corrected, and engine-specific bug claims were not adopted as facts.

Not run: game builds, gameplay tests, cross-engine adapters or asset-rights admission. These are planned acceptance tasks, not outcomes of this catalog update. Repository workflow/wizard scaffolds were not changed in this revision.

---

# Catalog validation on November 11 2026

## Roadmap JSON export follow-up

Added a review JSON preview with copy, manual selection fallback and native UTF-8 file export. It reads current saved records, labels unsaved draft edits, exports all games independent of filters, normalizes donor/capability definitions, and includes larger-game context and review questions. No catalog or progress writes are performed by export.

Passed: `npm test` (11 tests), `cargo test --manifest-path hub/src-tauri/Cargo.toml` (8 tests), production Tauri build, and `node tests/roadmap-export-smoke.mjs` from `hub/`. The native test confirms 50 games/143 definitions, filter independence, current draft labeling without saving, exact clipboard-handler payload, manual-selection fallback, unique export filenames, parsed file equality and no page errors. The system clipboard was deliberately untouched by the test; clipboard writing was intercepted, while selection fallback and native disk writes were exercised. The OS folder picker uses the existing dialog integration. Screenshot visually inspected.

The user's open executable was preserved. Built with `CARGO_TARGET_DIR=X:\Projects\ArcoreGameCore\hub\src-tauri\target-json-export`; launcher now prefers this updated release. [Native result](evidence/roadmap-export-2026-11-11/result.json), [export dialog](evidence/roadmap-export-2026-11-11/export-dialog.png), and [source/executable hashes](evidence/roadmap-export-2026-11-11/receipt.json) are retained. Executable SHA-256: `02fed6fd5fbb9136b3e20a3353ba351c9d7f4214b425be6d6f9cec13c9740716`. Existing non-fatal Vite chunk advisory remains. No game builds/playtests or external LLM submissions were performed.

## Fifty-game roadmap follow-up

Workflow: `game-project-integration`; starting dimension `3d`, with 2D and XR tracks retained. Same baseline/toolchain below; working-tree implementation, not a committed release. Scope is roadmap planning and evidence tracking, not game implementation or automated acceptance execution.

The live library now contains 50 roadmap games, 285 game–capability assignments, all 143 original gaps assigned, and 315 indexed donor code references across game cards. Additional tracks exercise second consumers and combined mechanics. All targets start planned. Existing 31 catalog projects, taxonomy and 46 media records were compared before/after and preserved; SQLite integrity and foreign keys passed. [Initialization counts](evidence/roadmap-2026-11-11/live-initialization.json), [pre-update backup](evidence/roadmap-2026-11-11/backup.json), and [source/executable hashes](evidence/roadmap-2026-11-11/validation-receipt.json) identify the exact result.

Passed checks:

| Command | Result |
|---|---|
| `npm test` in `hub/` | 10 tests; includes 50-track coverage, all donor IDs, 285 assignments and prerequisite milestone semantics |
| `cargo test --manifest-path hub/src-tauri/Cargo.toml` | 8 tests; includes seed expansion without reset, persistence, stale-edit rejection, evidence requirements, cycle rejection and indexed file containment |
| `npm run tauri -- build --no-bundle` in `hub/` | Optimized Windows executable, `src-tauri/target/release/gamecore-library.exe` |
| `node tests/roadmap-smoke.mjs` in `hub/` | Actual release WebView with isolated copy of current user library: priorities, owner/status, prerequisite target selection, source/asset pinning, verification gate, backup and restart persistence |
| `$env:GAMECORE_TEST_EXE='X:\Projects\ArcoreGameCore\hub\src-tauri\target\release\gamecore-library.exe'; node tests/native-smoke.mjs` in `hub/` | Existing catalog edit/search/media approval/export/backup/restart regression check |
| `python tools/validate_workflows.py`; `python tools/validate_wizards.py`; `python tools/mcp_registry.py` | Passed |
| `python -m unittest discover -s tools/tests -v` | 91 passed |

[Native roadmap receipt](evidence/roadmap-2026-11-11/result.json) and [live view](evidence/roadmap-2026-11-11/live-roadmap.png) are retained. Screenshots were visually reviewed; the native test checks page errors and horizontal overflow. The roadmap seed is additive; versioned updates are transactional and history is included in ordinary SQLite backups. Prerequisite checks are advisory for starting independent work; completion requires accepted records for every target. Evidence fields record user claims, not an automatic replay of the tests.

Resolved during development: Windows case-insensitive module resolution required distinct `RoadmapView.tsx` and `roadmap.ts` basenames. The isolated native fixture was updated to preserve the user's current 46 media rather than assume the earlier 44-item snapshot. No outstanding failing checks. Vite reports a non-fatal frontend chunk-size advisory (918 KB uncompressed, 189 KB gzip).

Not run: implementation or playtests of the 50 proposed games, verification of external donor behavior, fresh hashing of every indexed donor file, provider asset/license admission, or automatic promotion from roadmap claims into catalog coverage. Code links reveal indexed files; missing or moved sources require reindexing. The older user-owned app window was left undisturbed; reopen the launcher to use the new roadmap.

## Marketing curation and capability expansion follow-up

Same workflow, dimension, baseline and Windows toolchain as below. Scope: curate existing local media, preserve originals, extend source classifications and present explicit backlog/evidence filters. No game runtime or engine migration changed.

The live `%APPDATA%/com.arcore.gamecore/catalog.sqlite3` now holds 44 imported assets (38 screenshots, 6 videos), 297 taxonomy records (57 domains plus 240 specific capabilities), and 107 new source-backed classification links. All 44 source and managed-copy hashes match. SQLite integrity and foreign-key checks passed. [Import receipt](evidence/marketing-2026-11-11/import-receipt.json) records the pre-update backup. [Readiness report](evidence/marketing-2026-11-11/readiness-report.json) lists all 31 projects and suggested next capture subjects.

The atlas has 97 capabilities with candidates and 143 not yet evidenced, across 30 groups. No new runtime verification claims were inferred from broad tags. The marketing backlog has 12 screenshot/reshoot gaps, 30 gameplay/scene-clip gaps and 31 trailer gaps. Gully Giants and the VR beach have reference-only screenshots. Existing video asset demos and the long story walkthrough remain distinct from gameplay clips and trailers. Publication approval remains pending.

Passed on the final build:

| Command | Result |
|---|---|
| `npm test` in `hub/` | 7 tests; includes independent detailed coverage and marketing readiness distinctions |
| `python -m unittest discover -s hub/tools -p test_*.py -v` | Idempotent import, user-edit preservation, pre-update backup, source preservation, hash rejection |
| `cargo test --manifest-path hub/src-tauri/Cargo.toml` | 4 database/media tests |
| `cargo fmt --manifest-path hub/src-tauri/Cargo.toml --check` | Passed |
| `npm run tauri -- build --no-bundle` in `hub/` | Optimized Win64 `gamecore-library.exe`; 24,500,224 bytes |
| `$env:GAMECORE_TEST_EXE='X:\Projects\ArcoreGameCore\hub\src-tauri\target\release\gamecore-library.exe'; node tests/native-smoke.mjs` in `hub/` | Fresh seed, edit, source search, image preview, approval/export, backup, restart persistence |
| `node tests/marketing-smoke.mjs` in `hub/` | Isolated online copy of populated library; 19 cover images decode; actual video playback; metadata save; all readiness filters and detailed gaps; no page errors/overflow |
| `python tools/validate_workflows.py`; `python tools/validate_wizards.py`; `python tools/mcp_registry.py` | All passed |
| `python -m unittest discover -s tools/tests -v` | 91 passed; fixture now includes new root README link targets |

Release SHA-256: `1a162de6c071f94a5f2d1d285ce6a9f8bb6b47df29cd12f3cbcba651ccbc46a2`. [Final native receipts and source hashes](evidence/marketing-2026-11-11/validation-receipt.json) identify the working-tree snapshot. The new executable name allows the user's older `gamecore-hub.exe` window to remain undisturbed; close that window and reopen the launcher before editing, to avoid stale catalog state.

Resolved during validation: Python backup connections initially remained open on Windows; explicit closing fixed the cleanup failure. Two scaffold fixture tests initially omitted the new hub README/launcher link targets; the fixture now includes them. No outstanding test failure. Vite reports a non-fatal 725 KB frontend chunk size advisory.

Not run: new game captures, game playtests/builds, headset comfort tests, complete editorial playback or audio audition of every clip, external license clearance, signed installer creation. Video review used six sampled frames per shortlisted clip plus complete ffmpeg decode checks; the native test played the selected sailing clip. Contact sheets, per-asset rationale and video review metadata remain in this evidence directory. These checks establish catalog/media behavior, not gameplay correctness.

## Original implementation validation

Baseline GameCore revision: `be8748519106250dee0adc70d0aedbfa1a9d9983`. The implementation is an uncommitted working-tree addition. Existing unrelated changes were preserved. Exact application/source hashes and check records are in [the receipt](evidence/2026-11-11/receipt.json).

Selected workflow: `game-project-integration`, starting dimension `3d`; the catalog includes 2D, 3D and XR. Scope is catalog/media storage, not engine migration or game runtime changes. The baseline had a proposed Tauri hub design and no `hub/` application.

Environment: Windows 11 Pro 10.0.22631 x64; Rust 1.99.1, Cargo 1.99.1, Node 24.11.0, Python 3.14.0. Locked dependencies include Tauri 2.12.5, rusqlite 0.32.1, React 19 and Vite 7.3.8. SQLite is bundled; media preview uses the installed WebView2 runtime.

## Passed

| Command | Scope and result |
|---|---|
| `npm.cmd test` in `hub/` | 5 catalog/filter/coverage tests, including all 16 Games-folder consumers and 21 registered arcade games |
| `cargo test --manifest-path hub/src-tauri/Cargo.toml` | 4 database/media tests: non-destructive seeding, reopen, approval rules, path preservation, corrupt-media export rejection and backup restoration |
| `npm.cmd run tauri -- build --no-bundle` in `hub/` | TypeScript/Vite production frontend and optimized Win64 desktop executable |
| `$env:GAMECORE_TEST_EXE='X:\Projects\ArcoreGameCore\hub\src-tauri\target\release\gamecore-hub.exe'; node tests/native-smoke.mjs` in `hub/` | Actual release WebView UI, SQLite seed/search/edit, image import/preview/dimensions, approval/export/backup, capability gap and restart persistence |
| `python tools/validate_workflows.py` | Workflow/document link integrity |
| `python tools/validate_wizards.py` | Wizard definition integrity |
| `python tools/mcp_registry.py` | Registry structure; no live downstream services invoked |
| `python -m unittest discover -s tools/tests -v` | 91 scaffold tests passed |
| `npm.cmd audit --omit=dev` in `hub/` | 0 reported production npm vulnerabilities |

The native test uses a fresh isolated library, original app-icon fixture and owned process tree. It does not alter a player's save or the default user library. [Native results](evidence/2026-11-11/result.json), [library screenshot](evidence/2026-11-11/library.png), [mechanics screenshot](evidence/2026-11-11/mechanics.png), and [gap screenshot](evidence/2026-11-11/capability-gap.png) are retained. Library and mechanic screenshots were visually inspected for readable layout; the native test also checks horizontal overflow and JavaScript errors.

## Failed checks corrected during development

- Initial frontend typing of imported JSON and missing Windows icon blocked first builds; corrected before successful builds.
- The arcade extractor initially included an interface definition as an empty extra record; corrected and protected by the 21-game regression.
- The existing documentation checker does not decode spaces in local URLs; launcher changed to `Launch-GameCore.cmd` and links revalidated.
- Initial older development-test dependencies reported vulnerabilities; Vitest was updated and the subsequent npm install/audit reported none.

## Not run and limits

- Game builds, actual gameplay, asset import correctness, rig/LOD/collision evaluation, music listening and licensing approval. The catalog's historical evidence is not a new acceptance pass.
- Large video import/codec matrix, full motion-video playback and trailer playback across devices. Backend tests exercise byte-preserving storage and hash integrity; the native test validates a real image preview. Codec support depends on WebView2.
- Signed installer, other operating systems, independent PC installation, multi-process concurrent editing, crash/power-loss stress and extensive accessibility/device testing.
- Downstream ModelForge/SoundCore/SonicAlchemist live APIs and exact provider asset IDs. Current links are editable references/folder handoffs.
- Automatic in-app filesystem rescan/merge and automatic seed updates to an existing edited database. The audit script is available, and startup deliberately preserves editorial data.

No checks remain blocked. Non-failing diagnostics: Vite reports a frontend chunk above 500 KB (including the bundled read-only seed); an existing Python HTTP cleanup test emits a ResourceWarning. `git diff --check` also found a pre-existing trailing blank line in `tools/ecosystem.py`, which this task did not modify.

The local release executable is `hub/src-tauri/target/release/gamecore-hub.exe` (24,300,544 bytes at validation); its SHA-256 is recorded in the receipt. No installer or executable is committed to source control.
