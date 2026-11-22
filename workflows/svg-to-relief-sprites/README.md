# SVG to relief models and animated sprites

Runnable CLI pilot for 2D games with editable 2.5D source models. This workflow is not a full anatomical reconstruction or rigging service. The workflow index remains scaffold status because no hub form/wizard is implemented.

Use one manifest and one finishing recipe for the entire cast. ModelForge owns imported models, Blender jobs and saved model versions; PhotoMaster owns non-destructive image finishing. The consuming game owns SVGs, output directories, editable Blender copies, recipes, frames, atlases and acceptance evidence. No game-specific assets belong in GameCore.

## Run

Install Python dependencies in `requirements.txt`, start ModelForge with its existing agent API enabled, and ensure the registry's PhotoMaster executable exists. Discovery uses `shared/ecosystem.json`; tokens remain in memory. No additional MCP server registration is needed. The CLI uses GameCore's registry/provider adapters. The installed legacy hub binary may not expose model production; the CLI is the verified entry point for this workflow.

```
python tools/svg_relief_pipeline.py <consumer-manifest.json> <new-output-directory>
```

See [the generic example](example.md). Existing output directories are rejected. Intermediate originals and failed job outputs are retained; retry to a fresh version directory. Do not overwrite library files. ModelForge imports a seed and saves a new Blender version; the optional environment stage generates an original scene without retaining seed geometry.

## Contract

- Input: solid hex fills/strokes, SVG path/circle shapes, flattened coordinates, square viewBox recommended. Quadratic/cubic curves are sampled. Transforms, embedded raster images, gradients, filters and text are unsupported. Keep holes as explicit foreground/background design layers; this initial converter does not implement compound fill rules. Source ownership/license belongs in the consumer manifest or art documentation.
- Geometry: consistent four-unit normalization, layered raised ink, modest solidify/bevel, original colors. Relief models are editable but are not full 360-degree characters. Preserve source silhouette and readability.
- Geometry revision 2 uses Shapely 2.1+ constrained triangulation and checks polygon area preservation. Revision 1 filtered unconstrained triangles, which could leave gaps in concave ribbons and outlines; regenerate affected production assets rather than editing their source SVGs to compensate. Receipts now record `geometry_version`.
- Render: one orthographic camera, shared lighting/material recipe, 384px RGBA frames, sixteen frames (four clips of four frames: idle/cast/guard/hit), one 1536px atlas per character. Procedural motion is a first pass, not skeletal animation. Use the same pipeline for every subject; explicit design overrides require a new recipe version.
- Finish: one PhotoMaster character recipe, separate environment recipe, preview, new project file, new PNG export. No source pixels are overwritten.
- Runtime: load only the hero and current opponent atlas, not the whole roster. Preserve static reduced-motion frames and an independent combat resolution timeline. Frame markers must never apply damage twice.
- Receipt: source hashes, ModelForge model/job identity, saved versions, output hashes, clip layout and image recipes. A finished render is not proof of mobile performance or gameplay balance.

## Modular family variants

For large rosters, render neutral family bodies once and render a small shared library of equipment/effect overlays through the same manifest pipeline. Each overlay is a transparent full-canvas SVG with the same viewBox, orthographic camera, finish settings and four-clip contract. Consumers compose the current family and selected overlay at the same frame index, with bounded whole-body proportions and a palette tint from a deterministic recipe. Keep both textures under the same reaction transform and defeat fade/slicing. This is runtime 2D composition of pre-rendered relief; it does not create a separately rigged 3D model for every variant.

Only load the current family and current kit. A 1536-square uncompressed RGBA8 sheet is 9 MiB; a second kit sheet adds another 9 MiB, not the entire roster's memory. The CLI closes each PhotoMaster document after saving its project and export, allowing batches beyond the editor's open-document limit. Original projects and images remain intact.

Author semantic SVG groups and family-specific anchor sidecars when part-level modification is desired. The converter flattens group geometry and does not consume attachment anchors; consumers can reposition kit regions using the authored SVG-space anchors. Match the orthographic scale and clip deformation before projecting attachment offsets, so attachments follow both idle and action frames. This is authored placement, not automatic anatomical inference. Inspect every silhouette for face occlusion, ground alignment and clipping. Preserve existing individual artwork as references when changing production strategy.

## Acceptance evidence

CLI production has been exercised in a Godot consumer: thirteen character atlases and one environment, with original sources kept by the consumer. Shared unit tests cover conversion/rejection and source preservation. Device FPS, save behavior and gameplay evidence must be recorded by each consumer separately; do not infer a passed port from this workflow. More advanced stroke/fill rules, fully rigged models, frame interpolation and a guided hub wizard remain future work.


## Volume and editable animation recipe (volume-v2)

Set `"render_recipe": "volume-v2"` in the consumer manifest for a new production directory. The original `relief-v1` remains the default. This shared recipe uses a convex 0.42-unit surface displacement, 0.24-unit solid depth, 0.025-unit bevel and identical lighting for every subject. It preserves the SVG silhouette; it does not reconstruct unseen anatomy or create a skeletal rig.

Sixteen editable morph poses provide idle, cast anticipation/strike/recovery, guard and hit clips. Four NLA actions interpolate these poses in Blender/GLB. Tablet layout stays at 384px per frame, 4×4 cells, so existing sprite memory and clip indices remain compatible. The different action motion needs consumer review of modular attachment alignment; old anchor equations are not exact for this recipe.

`relief_bake_morphs.py` bakes the neutral modifiers once before creating fixed-topology morph targets. This avoids bevel topology changing between poses. It writes new `editable-volume.blend` and `animated-volume.glb` files, preserving the original render master. The GLB has real backs/beveled edges and four clips; its morph data is intended for desktop review, not mobile runtime loading. Consumer receipt records the export job. Keep predecessor models, recipes and hashes for comparison.

Acceptance for the first five-actor consumer slice: inspect silhouette/transparency and changed action frames; verify all four GLB clips deform vertices in the browser; check reduced-motion stills and presentation-only idle updates; run the consumer's device battle tests. Do not infer readiness of the rest of a roster from this pilot.


## Authored articulated limbs (articulated-v1)

Set `render_recipe` to `articulated-v1`; each subject must include a `rig` path relative to the manifest. A rig sidecar contains `source_sha256`, ordered `bones` (name, parent, head/tail in the source 512×512 SVG space), layer-binding `rules`, and four named `clips` (idle/cast/guard/hit). Each clip maps bone names to four rotation angles in degrees. Neutral/anticipation/impact/recovery poses interpolate in the exported 24-fps NLA actions. A missing bone angle defaults to neutral.

Rules bind zero-based SVG path/circle layers to one rigid bone, or to two bones with an axis/split/blend band and optional x limits. This supports bent elbows/knees inside an existing polygon without moving face, torso or weapon layers accidentally. The original converter's layer depth spacing is part of this contract. Changing an SVG invalidates the source hash and requires reviewing the authored bindings; do not guess joint locations from a silhouette. Explicit source-space mappings belong to the consumer, not GameCore.

The renderer applies the shared convex-volume/material recipe, bakes neutral solidify/bevel, normalizes interpolated skin weights, and then adds an Armature modifier. The weapon and hand can share the same forearm bone. Outputs: editable Blender armature with four NLA tracks, skinned `animated.glb`, sixteen 384px frames and the existing PhotoMaster atlas. This is a front-oriented articulated relief character, not reconstructed rear anatomy. Existing morph and static recipes remain unchanged.

Acceptance: verify all bones have weighted vertices, weights sum to one, four clips contain changing joint transforms, all rendered frames preserve transparent margins, and weapon contact remains intact. Review the neutral pose, strike, guard and recoil in both 3D and the consumer's battle screen. Equipment attachment rules are still consumer-owned; skeletal articulation does not automatically rig old overlay kits. Pilot consumer evidence covers two actors; it does not certify an entire roster.
