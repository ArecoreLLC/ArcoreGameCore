# Hair, fur and card textures: ModelForge HairLab handoff

Status: exploratory; 3D consumers. Procedural generation is **experimental**, and the Unreal generator path is currently blocked (see below).

[ModelForge's HairLab owns the pipeline](https://github.com/ArecoreLLC/ArcoreModelForge/blob/main/texture-lab/README.md):
the Blender card baker, atlas packer, GLB export, shell-fur sets, procedural recolor, the Shading Lab and Shell
Fur Lab, and the library import. GameCore coordinates the handoff and in-game acceptance. Do not copy its steps
or scripts into GameCore.

## Pipeline overview

```
strands (Blender procedural hair nodes)
  -> cards: albedo (neutral), alpha, AO, normal, depth, id, gradient      hair_cards.py
  -> atlas + atlas.json (UV rects, world size)                           pack_atlas.py
  -> card GLBs with LODs, palette recolors (15)                          cards_to_glb.py, recolor_cards.py
  -> shell fur sets (tileable layers, per-shell RGBA)                    fur_shells.py
  -> ModelForge library: texture-set assets, versioned, via the          import_texture_set (ModelForge MCP)
     agent API; Shading Lab / Shell Fur Lab to tune look in real time
  -> consumer imports the approved set and recolors with the shader recipe (Godot, three.js, Unreal)
```

Two representations: **cards** (flat alpha-tested quads, cheap, hold up from every angle only when three
crossed quads are used) and **shell fur** (instanced layers; cost = mesh triangles x shells). Colour is
procedural on neutral albedo, not baked per colour.

An experimental side path runs Unreal's Hair Card Generator headless for comparison. It is not part of the
accepted pipeline: groomed Alembic input built from Blender strands does not yet produce a valid result.

## Handoff

1. Record the consumer project, engine and version, target platform, the hair/fur need (style, colour,
   LOD/triangle budget, card or shell), and a consumer-owned output location.
2. Follow HairLab's canonical README to bake or select a set. Ask it for the preset, seed, palette and
   atlas size; it chooses tools and settings. Use ModelForge's agent API only through the GameCore hub.
3. Receive the texture-set or card-model asset ids and versions, the manifest, palette used and any
   unresolved issues. A generated set is a review candidate, not an approved asset.
4. Import only an approved version. Verify on the actual target engine and platform: alpha sorting or
   hashed alpha, overdraw cost, shader recipe output, LOD switching, and frame time. HairLab's own
   Shading Lab results are in three.js and do not prove engine rendering.

## Version and update check

HairLab publishes its version in
[`texture-lab/hairlab.json`](https://github.com/ArecoreLLC/ArcoreModelForge/blob/main/texture-lab/hairlab.json)
with the tool versions it was tested against (Blender, Unreal, Hair Card Generator plugin) and its known
blockers. GameCore records which version a handoff used in [`pin.json`](pin.json).

Check without opening any editor, from the ModelForge checkout:

```bash
python texture-lab/hairlab_version.py          # report; exit 1 if a tool differs from the tested version
python texture-lab/hairlab_version.py --json   # same, machine-readable
```

Compare `pin.json` to the manifest's `version`. A newer HairLab version or a differing installed tool means
re-run the bake and lab smoke tests before trusting new output. The checker reads installed versions only;
it never starts Unreal or Blender's UI.

Use the [worked handoff](example.md), [integration workflow](../game-project-integration/README.md) and
[shared contract](../../shared/migration-contract.md). This handoff adds no downstream MCP connection.
