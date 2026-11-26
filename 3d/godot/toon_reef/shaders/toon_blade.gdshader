shader_type spatial;
render_mode cull_disabled, specular_disabled;

#include "underwater.gdshaderinc"

// swaying blade (kelp, sea grass). Double-sided, base-to-tip
// gradient, per-instance sway phase and tint when the batch carries custom data.
uniform vec3 base_color : source_color = vec3(0.10, 0.62, 0.38);
uniform vec3 tip_color : source_color = vec3(0.42, 0.94, 0.52);
// Model-space blade length (recipe mesh `length`).
uniform float blade_height = 5.5;
uniform float sway_speed = 1.6;
uniform float sway_amount = 0.38;
uniform float tint_variation : hint_range(0.0, 0.5) = 0.18;
// Light glowing through the blade toward the tip.
uniform float translucency : hint_range(0.0, 1.0) = 0.22;
// Distance (start, end in meters) over which a blade shrinks away; end 0 = never.
uniform vec2 fade_range = vec2(0.0);

varying float blade_h;
varying float shade;

void vertex() {
	blade_h = clamp(VERTEX.y / max(blade_height, 0.001), 0.0, 1.0);
	shade = 1.0 + (INSTANCE_CUSTOM.y - 0.5) * 2.0 * tint_variation;
	vec3 origin = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	VERTEX *= uw_distance_keep(origin, MAIN_CAM_INV_VIEW_MATRIX[3].xyz, fade_range);
	float phase = origin.x * 0.23 + origin.z * 0.19 + INSTANCE_CUSTOM.z * 6.2831;
	float wave = sin(TIME * sway_speed + phase + blade_h * 2.4);
	float cross_wave = cos(TIME * sway_speed * 0.75 + phase * 1.3 + blade_h * 1.8);
	float bend = blade_h * blade_h * sway_amount;
	VERTEX.x += wave * bend;
	VERTEX.z += cross_wave * bend * 0.65;
}

void fragment() {
	vec3 color = mix(base_color, tip_color, smoothstep(0.10, 0.95, blade_h)) * shade;
	ALBEDO = color;
	EMISSION = tip_color * translucency * blade_h * blade_h;
	ROUGHNESS = 0.7;
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
}

void light() {
	// Thin leaves catch light from both sides; two tones are enough at this size.
	float ndl = abs(dot(NORMAL, LIGHT));
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * mix(0.55, 1.0, smoothstep(0.42, 0.48, ndl)) * ATTENUATION / PI;
}
