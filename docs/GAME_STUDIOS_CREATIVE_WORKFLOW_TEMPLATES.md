# AreCore Forge creative workflow starter library

Date: 2026-11-05. Companion to [the repository gap review](GAME_STUDIOS_GAP_REVIEW_2026-11-05.md), later phase 5. Scope: reusable video, model, audio and game-iteration playbooks. All 30 starter templates remain **draft/manual-assisted**, not implemented GameCore runner commands. T01 is now grounded in a captured, registered `logo-sting-video` scaffold with a real production record; parameterization and second-use verification remain open. Tool-specific functionality may already exist; a complete automated workflow still needs provider adapters and acceptance evidence.

## Capture a workflow once; reuse it without the original conversation

Keep three separate artifacts:

1. **Template:** stable ID/version, intended outcome, typed parameters, required capabilities, dependency graph, review gates, outputs and recovery rules. Use placeholders for project identity and media.
2. **Project binding:** actual assets/file IDs/hashes, model and composition revisions, licenses, style references, cue sheet, camera/scene choices, output profile and local path mapping. Keep proprietary assets and credentials out of generic templates.
3. **Run receipt:** exact template/binding hashes, tool/build versions, resolved parameters, provider job IDs, step states, cache decisions, produced artifact hashes, actual durations, errors/retries and review decisions. Link retained logs and screenshots rather than depending on chat history.

Capture manual work too: a composition decision, animation timing correction, selected instrument, rejected take or visual framing adjustment is part of the process. Record the reason and resulting parameter/artifact. A prompt alone is not a reproducible workflow; retain the model/tool version, reference hashes, seed when supported, and accepted output. Do not promise byte-identical AI output when the provider cannot supply it.

### Common contract for every template

| Field | Required content |
|---|---|
| Identity | Stable template ID, semantic version, parent/fork, status and responsible repository. |
| Inputs | Required and optional inputs; exact model/audio IDs and versions; hashes with named algorithms; licenses and source parents. |
| Creative controls | Subject, audience, style references, camera/light preset, action/shot plan, music mood/BPM/key, cue IDs and branding. |
| Timing | Rational frame rate such as `24/1`, zero-based output timeline, source frame origin, frame range/count, sample rate and explicit retime map. |
| Steps | Typed operation, adapter/capability, dependencies, inputs/outputs, timeout, resume boundary, retry/idempotency behavior and manual gate. |
| Versions | Tool/engine/renderer versions, template/schema version, preset hash, font/instrument/model dependency identity. |
| Outputs | Editable source, interchange files where valid, image sequence, stems/mix, cue sheet, delivery media, contact sheet and receipt. |
| Acceptance | Technical validations and separate visual/listening/design decisions; start each check at `not_run`. |
| Recovery | Cache fingerprint, staging location, provider job reconciliation, incomplete-file handling and non-destructive rerun policy. |
| Portability | Resolve machine-specific paths from bindings; verify capabilities; never silently change render hardware or omit required media. |

Build reusable operations for `pin_inputs`, `prepare_scene`, `preview`, `render_shots`, `prepare_audio`, `align_cues`, `mix`, `composite`, `encode`, `validate` and `publish_receipt`. These are **proposed operation names**, not current MCP tools. Adapters must discover actual provider schemas and preserve provider validation. Publication here means saving approved deliverables to the project/catalog; uploading publicly is a separate explicit action.

## First captured reference: the logo animation with soundtrack

The producing agent’s [GameCore logo-sting guide](../workflows/logo-sting-video/README.md) and [worked example](../workflows/logo-sting-video/example.md) now identify the V3 Pro 1.5× cut and capture its detailed procedure. Use this guide as T01’s canonical process and the example as its historical production record. The [ModelForge source workflow](../../ArcoreModelForge/design/arcore-logo/README.md) remains the underlying source reference; the GameCore [index](../workflows/index.json) registers the workflow as a 3D scaffold.

| Observed component | Existing evidence | Extraction needed |
|---|---|---|
| Editable scene and animation | V3 Pro Blender scene workflow; [retime script](../../ArcoreModelForge/design/arcore-logo/v3-pro-15x/render_15x.py) | Subject/scene binding, shot ranges, camera/light preset and renderer/device profile. |
| Retiming | 384 source frames → 256 output frames at 24 fps using 3:2 Blender remapping | Explicit origin/rate mapping; parameterize rather than dropping alternate encoded frames. |
| Music/Foley/synthesis | [soundtrack.py](../../ArcoreModelForge/design/arcore-logo/v3-pro-15x/soundtrack.py): GeneralUser GS bank from Sonic Alchemist's local library, SoundCore Kenney effects, synthesized layers, seed 7 | Pin the bank/effects by hashes and license records; extract notes, cue locations, gains, pan and synthesis parameters from code. |
| Frame synchronization | Existing cue mapping `t(f) = f/36 - 1/24` for this specific cut | Preserve that formula as historical evidence; derive a new explicit mapping for other edits. Do not assume a universal frame-origin convention. |
| Separate audio outputs | `soundtrack.wav`, `music.wav`, `sfx.wav`, 48 kHz stereo | Retain editable composition/recipe plus stems, not only final mixed AAC. |
| End card and encode | [finish_15x.py](../../ArcoreModelForge/design/arcore-logo/v3-pro-15x/finish_15x.py), version-folder end-card generator | Parameterize text, font, safe area and overlay timing. Historical “Foundry” wording remains evidence; new outputs should use the approved Forge branding. |
| Delivery checks | [stored receipt](../../ArcoreModelForge/design/arcore-logo/v3-pro-15x/mp4-validation.json): 1080p, 24 fps, 256 frames, H.264/AAC, ~10.667 s | Reuse validation intent; rerun against each new output. The existing script stages before replacing the final video and fully decodes it. |

This reference uses an instrument bank located in Sonic Alchemist's workspace through an offline Python scoring script. It does **not** establish a saved Sonic desktop project or full Sonic MCP orchestration. Capture the actual path now; later AU-01/AU-03 adapters can replace manual/scripted steps without rewriting the template's creative intent.

The existing [GPU render helper](../../ArcoreModelForge/design/arcore-logo/render_gpu.py) skips existing frames and selects HIP. A reusable runner must additionally validate frame fingerprints and actual device availability. Existing filenames alone cannot distinguish reusable frames from frames rendered before a scene change.

### Capture checklist for the user's completed video

- [x] Identify the captured production: the new GameCore worked example names `AreCore_Logo_V3_Pro_1.5x.mp4`, its source scene and version lineage.
- [ ] Inventory editable scenes, scripts, fonts, texture dependencies, audio takes, banks, stems, end cards and licenses.
- [x] Locate the producing agent’s step/command record, cue sheet, tool versions and failure/fix history. These are authored historical evidence, not a newly executed replay.
- [ ] Extract all project-specific constants into a binding; leave only reusable behavior in the template.
- [ ] Record the cue sheet in source and output time, including starts, impacts, transitions and tails.
- [ ] Preserve the historical final result and its checks before rerunning anything.
- [ ] Reproduce a short representative segment first, then the full output; review timing, framing and audio by a person.
- [ ] Run the same template with a different subject or project and record what still required source-code edits.
- [ ] Promote only the proven reusable scope; leave unresolved automation steps explicitly manual or blocked.

The two completed capture items are grounded in the producing agent’s newly supplied guide/example. Full dependency hashes, portable bindings, replay and second-project reuse remain open. The example explicitly records audio audition and end-card copy approval as `not_run`; do not upgrade them from a level plot or successful decode.

### What is already captured, and what still needs implementation

| Already recorded by the producing agent | Remaining reuse work |
|---|---|
| Scene lineage, exact stage commands and named timing events | Hash and preserve scripts/scenes; replace absolute local paths with bindings. |
| Source-to-cut timing and per-beat music/Foley choices | Machine-readable cue IDs, rational time mapping and retime invalidation. |
| Tool versions, HIP rendering and interruption recovery | Capability preflight, verified frame fingerprints and provider job receipts. |
| Music/SFX stems, instrument bank, mix recipe and end-card settings | Pin bank/effect/font identities and licenses; retain the score script as editable source rather than inventing a Sonic project. |
| MP4 validation and contact-sheet review reported passed | Human audio audition and copy approval remain open; replay and second use are not run. |
| Documented production scripts and a copied final MP4 | Scripts in ModelForge `design/` are ignored by Git; preserve them in versioned storage before calling the recipe durable. |

Use the existing guide’s production-record and cue-sheet templates first. Extend their fields with the common contract above rather than maintaining two incompatible formats. T30 should now ingest the captured record and focus on missing pins, portable parameters, recovery and second-use proof.

Preserve incident context: the historical render hit a HIP queue failure; `drawtext` failed in fontconfig for that production; the offline scorer used a dependency workaround; the AgX flash required a compositor adjustment. These should become tested, version-specific fallback options, not blanket rules. Keep the old Foundry wording in the historical record and obtain approval for new delivery text.

## Starter templates: 30 reusable workflows

Abbreviations: **MF** ModelForge/its Blender bridge; **SA** Sonic Alchemist; **SC** SoundCore; **CAD** ArcoreCAD; **OW** OpenWorld; **WF** WorldFramework. GameCore is the proposed coordinator for every row. “Media adapter” means the existing FFmpeg/FFprobe approach generalized into a bounded adapter, not a new video-editing capability attributed to MF or SA.

### A. Video and presentation

| ID / template | Inputs and adjustable controls | Sequence / tools | Deliverables and completion gate |
|---|---|---|---|
| T01 — Animated logo sting ([captured guide](../workflows/logo-sting-video/README.md)) | Logo/scene, action timing, camera/light, brand text, music mood, output rate | MF prepare/preview/render → SA score → SC Foley → media adapter composite/mux | Native scene, stems, cue sheet, final MP4/contact sheet; readable logo, synchronized impacts, full decode and human playback. |
| T02 — Model turntable with sonic identity | Pinned model, orbit radius/elevation, background, loop duration, optional sonic tag | MF inspect/frame/orbit → SA short bed → encode | 360° reel, source camera recipe and thumbnail; no clipping, consistent scale and deliberate loop seam. |
| T03 — Character action reveal | Rig/version, approved clips, pose/animation range, action beats | MF prepare/preview/render → SC character Foley → SA accent music | Action reel plus clip/cue map; deformation and frame-timed sound reviewed independently. |
| T04 — Engineered product explainer | CAD revision/parameters, assembly order, labels, motion constraints | CAD export → MF finish/exploded animation → SA/SC sound → captions/composite | Explainer/source/part map; units retained, no unintended interpenetration, readable labels. |
| T05 — Environment flythrough | Pinned scene, route, shot list, time of day, ambience plan | OW capture or MF render → SC ambience → SA bed → encode | Film, camera route and sources; shot coverage and listening acceptance; film FPS is not benchmark data. |
| T06 — Gameplay teaser/trailer | Owned gameplay captures, hook/shot order, music markers, title/end card | Consumer capture → SA score/stems → SC transitions → media assembly | Edit decision list, stems, trailer and source receipts; no unsupported gameplay claim or accidental debug overlays. |
| T07 — Feature tutorial/demo | Actual interaction recording, script, callouts, optional narration/captions | Capture → trim/annotate → SA cleanup/mix → encode | Tutorial, caption file if supplied, narration/source record; steps match product behavior and text remains legible. |
| T08 — Multi-aspect delivery variants | Approved master/source shots, 16:9/9:16/1:1 presets, title-safe regions | Reframe shot cameras or approved crops → reposition text → mix/mux variants | Named outputs per aspect; inspect each framing/text/audio stream rather than stretching the master. |
| T09 — Seamless animated background | Scene/animation loop, camera, duration, optional ambient loop | MF loop/preview/render → SC loop preparation → media adapter | Loop video and recipe; first/last transition visually and audibly reviewed without forced fades hiding a bad seam. |
| T10 — Version comparison reel | Two pinned model/scene versions, fixed camera/light and annotation plan | MF/OW matched captures → split-screen/sequence → optional commentary | Comparison reel and change manifest; identical comparison conditions and explicit version labels. |

### B. Sound and music

| ID / template | Inputs and adjustable controls | Sequence / tools | Deliverables and completion gate |
|---|---|---|---|
| T11 — Frame-synchronized Foley | Shot/event cue sheet, exact SC source IDs, gain/pan/variant policy | SC search/audition/derive → SA place/mix → media mux | Foley stem, cue sheet and parent licenses; event timing and non-clipping mix checked. |
| T12 — Short branded musical sting | Duration, melody/reference, instrument bank, tempo/key, end-hit frame | SA compose/render → audition/revise → SC publish | Editable recipe, music stem and catalog receipt; end-hit timing and bank/source rights reviewed. |
| T13 — Adaptive exploration/combat score | States/intensity, layers, BPM/meter, transition boundary, loop length | SA author/audition/export → consumer runtime adapter | Stems/design plus runtime fixture; transitions and tails pass packaged-game and listening checks; adapter still required. |
| T14 — Layered environment ambience | Scene zones, weather/time cues, SC loops, mix budget | SC collect/prepare → SA layer/mix → consumer import | Zone beds/stems, loops and cue map; seams, repetition and simultaneous voices reviewed. |
| T15 — Footstep/surface variation set | Surface IDs, donor samples, pitch/gain ranges and variation seed | SC batch recipe → human audition → publish → game cue mapping | Per-surface variants and manifest; audible consistency without duplicate-only variations or clipped peaks. |
| T16 — Impact/ability sound family | Attack/body/tail sources, weight/intensity levels, event IDs | SC layer/transform → SA mix/polish → SC catalog | Family of sounds with shared recipe; attack readability, tail duration and lineage retained. |
| T17 — Voice/Foley capture queue | Requirement prompts, performer/license context, take selection | SA Asset Coach record → cleanup → raw/clean audition → accept → SC publish | Raw and processed takes, completion IDs; never fulfill a requirement before durable publication confirmation. |
| T18 — Loop preparation and repair | Source ID, intended loop points, crossfade/silence/peak settings | SC inspect/preview/render → SA detailed repair when needed → audition | Reusable loop/preset/source receipt; seam and tail checked, original retained. |
| T19 — Mastered trailer mix | Music/SFX/dialogue stems, ducking intent, delivery loudness/peak profile | SA balance/EQ/limiter → measure → listen → mux | Master plus unmastered stems/settings; measured levels and intelligibility, with profile-specific targets. |
| T20 — Library ingestion and licensed handoff | Audio folder/bank, source/author/license, consumer project ID | SC publish/search/review → manifest → deliver → copy/verify → acknowledge | Managed catalog IDs and portable project media; all parents/licenses retained and offline reopen passes. |

### C. Asset creation and iteration

| ID / template | Inputs and adjustable controls | Sequence / tools | Deliverables and completion gate |
|---|---|---|---|
| T21 — Reuse-first model intake | Subject/role, dimensions, style, target budgets | MF search/inspect → choose candidate → WF source checks → pin | Candidate set and accepted source pin; unknown license/scale remains unresolved, not approved. |
| T22 — CAD-to-game prop | Parameterized CAD source, unit/pivot contract, visual/export profile | CAD revise/export → MF/Blender UV/PBR/LOD → WF engine checks | Editable CAD/STEP, game export, finishing recipe; dimensions and engine material/collision fixture pass. |
| T23 — Material/look variation pack | Pinned geometry, palette/material recipes, shared lighting | MF duplicate by version/iterate/render → compare → catalog | Variants/contact sheet; source geometry retained, material-slot and texture dependency checks pass. |
| T24 — Budgeted export/LOD family | Source model, platform/profile, triangle/texture/material budgets | MF existing decimate/convert tools → WF preflight → consumer comparison | Pinned LOD/export family with reports; silhouette/deformation/appearance checked, not merely triangle counts. |
| T25 — Rig/animation compatibility check | Original rig, target engine, clips/pose samples, source timing | MF inspect/export → WF rig/pose/material checks → consumer fixture | Compatibility report and clips; bone/pose/scale/timing evidence, no parity claim from bone count alone. |
| T26 — Model review island submission | Pinned model versions, review profile and baseline | WF preflight → OW dedicated fixture → close views/human review → MF evidence | Version-specific review/capture receipt; static proxies do not claim rig/physics validation. |

### D. Integrated iteration and workflow maintenance

| ID / template | Inputs and adjustable controls | Sequence / tools | Deliverables and completion gate |
|---|---|---|---|
| T27 — First playable micro-scene | Brief, one interaction/model/cue, engine/platform and budgets | MF/CAD + SC/SA → consumer adapter → build/playtest/package | Tiny playable slice and receipts; actual interaction and offline packaged launch, not only imported assets. |
| T28 — Performance regression sweep | Pinned build/content/profile, route/density matrix, hardware | WF/OW capture → raw-sample analysis → baseline comparison → isolate suspects | Performance report and visual tradeoffs; coverage/metadata verified, capture video excluded from FPS evidence. |
| T29 — Weekly progress/review reel | Accepted captures, version diffs, open issues and narration plan | MF/OW comparison shots → SA/SC mix → titles/encode | Review reel, issue-to-shot map and source receipts; distinguish implemented, planned and failed work. |
| T30 — Capture, generalize and replay a successful workflow | Completed run, sources/logs, manual decisions and second-use brief | Inventory → parameterize → dry run → fixture replay → second project → promote | Template/binding/run trio, preview and limitations; second use succeeds without project-specific code edits. |

## Expanded playbook 1: T01 logo sting

**Required inputs:** editable logo/model scene, approved brand text, action/shot plan, duration and frame rate, output profile, available render device, instrument bank/source pins and sound rights. Optional: score reference, pre-existing composition, alternate aspect ratios. A 10.667-second 24 fps cut is one reference binding, not a fixed default for every project.

1. Pin source files/tool versions and preserve the historical source. Resolve library IDs and local bindings; preflight Blender, audio tools, FFmpeg/FFprobe and output capacity.
2. Create the action/shot sheet with stable event IDs such as `landing`, `bulb_burst`, `core_ignite` and `hero_hold`; record source frame and output timeline position separately.
3. Preview representative frames and motion cheaply. Approve composition, logo readability, lighting, motion cadence and card text before the expensive final render.
4. Render shots to a fresh run directory with a matching fingerprint. Record expected frame indices/dimensions and verify complete, nonempty images. Resume only verified compatible frames.
5. Use T12 for music and T11 for Foley. Preserve dry stems, synthesized recipes and source metadata. Place cues against the approved output timeline and preserve release tails.
6. Composite end card/branding; generate a staged master with video and the intended audio stream. Validate dimensions, rational rate, frame count, audio duration/sample rate, full decode and output profile.
7. Inspect a contact sheet and play the whole result with audio. Record visual and listening decisions independently of media-structure checks.
8. Save the native scene, source composition/recipe, interchange export if applicable, cue sheet, stems, master, contact sheet and receipt. Publish reusable assets to their owning catalogs through supported adapters.

**Recovery:** if audio fails, retain valid rendered frames. If card text changes, rerun overlay/encode. If motion timing changes, invalidate affected shots and cue timing. If a render is cancelled, keep the partial attempt but do not mix incompatible revisions. The final accepted output is replaced only by a validated staged revision.

**Promotion gate:** use the same template for a second emblem/subject with a different action duration and sound set; explain any remaining manual operations. New soundtrack production and visual replay were not executed during this update.

## Expanded playbook 2: T06 gameplay teaser

**Required inputs:** genuine gameplay captures or a reproducible consumer capture route, target duration, approved messaging, shot selection, music/stems, sound rights and end card. Optional: narration/captions and platform aspect variants.

1. Freeze a consumer build/content identity and record source shots with camera/input/settings metadata. Mark rendered concept footage separately from gameplay footage.
2. Create an edit decision list with source in/out points, shot IDs, output placement, transitions and intended beats. Choose timing before detailed Foley.
3. Assemble a low-cost edit; review the hook, feature readability, pacing and whether each caption accurately describes implemented behavior.
4. Compose/select music in SA and prepare SFX in SC. Use stable marker IDs so picture edits can identify invalidated cues; do not silently time-stretch the entire score after every change.
5. Mix narration/music/SFX, then composite and encode through the selected delivery profile. Preserve the edit list and unmastered stems.
6. Run stream/decode checks and watch/listen end-to-end. Produce per-aspect reframed variants from source shots, not an unreviewed automatic crop.

**Recovery:** retain source captures and approved audio; changing a shot invalidates its transitions/cues and final assembly, not unrelated asset creation. Missing shots or rights block delivery rather than being substituted silently.

**Promotion gate:** a second game/feature uses the same shot-list contract and adapters with new inputs; no claim of one-click game capture until a consumer adapter is implemented and tested.

## Expanded playbook 3: T30 capture-to-template

**Required inputs:** one completed deliverable, its editable sources and available logs, plus a different second-use brief. Missing history is allowed but must remain a named reconstruction gap.

1. Work backward from the final output: enumerate upstream shots, scenes, fonts, materials, audio stems, source parents, settings and encode checks.
2. Reconstruct an ordered run ledger with real commands and manual actions. Distinguish observed facts, user-reported steps and inferred steps; confirm inference before treating it as a replayable recipe.
3. Separate invariants from parameters. Remove machine paths and project-specific text from template logic; retain them in the historical binding.
4. Group repeated operations into reusable subworkflows. Specify each boundary's input/output contract, required tool capabilities, review gate and failure recovery.
5. Dry-run capability/input validation. Replay a small fixture and compare against declared visual/audio/timing tolerances; record nondeterminism rather than hiding it.
6. Run the second-use brief. Log source-code edits still required; convert those into missing parameters/adapters or explicitly narrow the template scope.
7. Promote the proven version and attach a preview, compatibility matrix, validation receipt, cost/timing observations and limitations. Keep historical versions available.

**Promotion gate:** successful creation of a document or parameter form is not enough. A template reaches `reused` only after a distinct second use passes its review gates.

## Proposed machine-readable recipe shape

Illustrative schema for later implementation. This JSON is not an installed workflow and must not be sent verbatim to a tool. Bindings and operation names require the GC-01/03 and VP-01/04 implementation work.

```json
{
  "schema_version": 1,
  "template_id": "forge.video.logo-sting",
  "template_version": "0.1.0",
  "status": "draft",
  "binding": "project-owned-bindings.json",
  "timeline": {
    "fps": {"numerator": 24, "denominator": 1},
    "output_origin_frame": 0,
    "frame_count": 256,
    "audio_sample_rate": 48000,
    "retime_map": "project-owned-retime-map.json"
  },
  "steps": [
    {"id": "preflight", "operation": "pin_inputs", "depends_on": []},
    {"id": "preview", "operation": "preview", "depends_on": ["preflight"], "review_gate": "visual_timing"},
    {"id": "frames", "operation": "render_shots", "depends_on": ["preview"]},
    {"id": "audio", "operation": "prepare_audio", "depends_on": ["preview"], "review_gate": "listening"},
    {"id": "assembly", "operation": "composite", "depends_on": ["frames", "audio"]},
    {"id": "encode", "operation": "encode", "depends_on": ["assembly"]},
    {"id": "validate", "operation": "validate", "depends_on": ["encode"], "review_gate": "final_playback"},
    {"id": "receipt", "operation": "publish_receipt", "depends_on": ["validate"]}
  ],
  "required_artifacts": ["editable_scene", "audio_recipe", "stems", "cue_sheet", "final_video", "contact_sheet", "run_receipt"],
  "checks": [{"id": "second-use-replay", "status": "not_run"}]
}
```

A cue record should carry `cue_id`, source event/frame origin, mapped output frame or rational time, source audio ID/hash, offset, gain/pan, trim/fade policy and expected tail. Define rounding once when converting frame time to samples. Keep intended sync tolerances explicit; codec padding and subjective timing require separate checks.

## Wizard delivery requirement for every template

The [GameCore Tauri hub design](GAMECORE_HUB_AND_WIZARD_DESIGN.md) defines the guided execution path for this library. Each template must supply typed inputs, defaults, presets, asset selectors, preview operations, review gates, capability checks and recovery behavior. The wizard, CLI and optional agent share one runner and validation service; no separate AI-only logic is allowed for routine steps.

Display assistance level explicitly: **No AI required**, **Optional AI help**, or **AI generation required**. A no-AI badge requires an actual supported run without a terminal, source edits or LLM calls. Offline readiness is a separate tested property. Unsupported bespoke creation must be an explicit editor handoff, not a hidden prompt requirement.

T01 uses forms for logo/scene, look, motion/timing, music/effects, end-card text and delivery. T02 provides the first small execution pilot. Preserve the captured production as source evidence while replacing its project-specific script constants with supported parameters. Extend the other 28 templates through shared widgets and adapters, not individual duplicate applications.

The hub is proposed as a new Tauri app under GameCore `hub/`, separate from legacy Godot code. This document does not claim that those forms or adapters already exist.

## Rollout and verification

**Start now:** use the captured T01 guide/example as T30 input; preserve its sources, extract portable bindings and structure its existing cue sheet. Do not recapture already documented steps. This is useful even before full automation. **First implementation set:** T01, T02, T11, T26 and T06. Then add sound families, asset finishing and iteration templates using shared operations.

Template lifecycle: `draft` → `captured` → `parameterized` → `fixture_verified` → `reused`; `deprecated` preserves history and points to a replacement. These are proposed template lifecycle values, separate from run-check states and the current GameCore workflow registry's scaffold statuses.

Documentation update checks: confirm all local evidence links, 30 unique template IDs, six later-phase backlog IDs, valid example JSON and paired Markdown code fences. No media render, encode, replay, listening review or new performance measurement is part of this document update. Previous audit test results remain historical results, not newly rerun checks.
