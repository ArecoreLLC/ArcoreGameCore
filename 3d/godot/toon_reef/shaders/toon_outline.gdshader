shader_type spatial;
render_mode cull_front, unshaded, shadows_disabled;

#include "underwater.gdshaderinc"

// inverted-hull ink outline (dark plum-charcoal).
uniform float width = 0.022;
uniform vec4 outline_color : source_color = vec4(0.12, 0.10, 0.16, 1.0);
// Must match the fade of the material this outlines.
uniform vec2 fade_range = vec2(0.0);

void vertex() {
	vec3 origin = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	VERTEX = (VERTEX + NORMAL * width) * uw_distance_keep(origin, MAIN_CAM_INV_VIEW_MATRIX[3].xyz, fade_range);
}

void fragment() {
	ALBEDO = outline_color.rgb;
}
