# Painted companion lighting (Godot 4)

Module `gamecore.godot.painted-companion` 1.0.0: one shader include, `painted_lighting.gdshaderinc`. Part of the
[painted-animated-companions workflow](../../../workflows/painted-animated-companions/README.md). Vendor it with
`python tools/companion_pipeline.py vendor --target <blender folder> --godot <game>/addons/gamecore_painted_companion`.

A character with a painted albedo texture should look like its painting from every side. Ordinary toon bands put
most of the front in shadow, and a sky ambient lights tops far more than fronts. The include replaces both with
flatter bands, a damped ambient and an even fill, plus a soft pigment edge toward the silhouette.

```glsl
#include "res://addons/gamecore_painted_companion/painted_lighting.gdshaderinc"
void fragment() {
    ALBEDO = painted_albedo(texture(albedo_tex, UV).rgb * COLOR.rgb, NORMAL, VIEW);
    AO = paint_ambient;
    EMISSION += ALBEDO * paint_fill;
}
void light() { DIFFUSE_LIGHT += painted_diffuse(NORMAL, LIGHT, LIGHT_COLOR, ATTENUATION); }
```

The engine multiplies `DIFFUSE_LIGHT` by `ALBEDO` once. Do not multiply by albedo again in `light()`.

Uniforms: `paint_light`, `paint_shadow`, `paint_mid`, `paint_fill`, `paint_ambient`, `paint_edge`. The defaults were
tuned in one scene (ACES tonemap, warm key light, sky ambient) by measuring rendered colours against reference
paintings. Re-measure in your scene with `tools/companion_review.py compare`; treat the defaults as starting values.

The consumer owns the rest of its shader (texture sampling, effects such as a reveal clip, the unpainted path).
First consumer: ShammyVerse `game/shaders/sand_animal_reveal.gdshader`.
