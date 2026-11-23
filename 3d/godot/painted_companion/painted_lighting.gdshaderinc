// gamecore.godot.painted-companion 1.0.0
// Even, paper-like lighting for characters that carry a painted albedo texture, so the colour on
// screen stays close to the painted colour from every side instead of sinking into shadow.
//
// Use from a spatial shader:
//   #include "res://addons/gamecore_painted_companion/painted_lighting.gdshaderinc"
//   void fragment() {
//       ALBEDO = painted_albedo(texture(albedo_tex, UV).rgb * COLOR.rgb, NORMAL, VIEW);
//       AO = paint_ambient;                      // damp the sky ambient, which lights tops far more than fronts
//       EMISSION += ALBEDO * paint_fill;         // even fill in its place
//   }
//   void light() { DIFFUSE_LIGHT += painted_diffuse(NORMAL, LIGHT, LIGHT_COLOR, ATTENUATION); }
//
// The engine multiplies DIFFUSE_LIGHT by ALBEDO once; do not multiply by albedo again in light().
// The defaults were tuned by measuring rendered colours against reference paintings under an ACES
// tonemap with a warm key light and a sky ambient. Re-measure in your own scene (see the
// painted-animated-companions workflow): these are starting values, not constants of nature.
uniform float paint_light = 0.30;     // key light strength
uniform float paint_shadow = 0.89;    // brightness of faces turned away from the light
uniform float paint_mid = 0.95;       // brightness of grazing faces
uniform float paint_fill = 0.36;      // even self-fill, as a fraction of albedo
uniform float paint_ambient = 0.35;   // how much of the scene's ambient light is kept
uniform float paint_edge = 0.55;      // pigment gathering toward the silhouette

vec3 painted_albedo(vec3 albedo, vec3 normal, vec3 view) {
    float edge = pow(1.0 - clamp(dot(normalize(normal), normalize(view)), 0.0, 1.0), 3.0);
    return pow(albedo, vec3(1.0 + paint_edge * edge));
}

vec3 painted_diffuse(vec3 normal, vec3 light, vec3 light_color, float attenuation) {
    float ndl = dot(normalize(normal), light);
    float band = mix(paint_shadow, paint_mid, smoothstep(-0.18, 0.28, ndl));
    band = mix(band, 1.0, smoothstep(0.35, 0.80, ndl));
    return light_color * band * mix(0.80, 1.0, attenuation) * paint_light / PI;
}
