shader_type spatial;
render_mode specular_schlick_ggx;

#include "underwater.gdshaderinc"

// three-tone toon prop (rocks, corals, sponges). Works on single
// meshes and on MultiMesh batches: with per-instance custom data each instance
// picks a palette color and a slight brightness shift, so one draw call paints
// a varied reef.
uniform vec3 color_a : source_color = vec3(0.98, 0.46, 0.68);
uniform vec3 color_b : source_color = vec3(0.98, 0.46, 0.68);
uniform vec3 color_c : source_color = vec3(0.98, 0.46, 0.68);
uniform vec3 color_d : source_color = vec3(0.98, 0.46, 0.68);
uniform int palette_size : hint_range(1, 4) = 1;
uniform float brightness_variation : hint_range(0.0, 0.5) = 0.12;
// Model-space height over which the base-to-tip gradient runs.
uniform float gradient_height = 1.5;
uniform float gradient_strength : hint_range(0.0, 1.0) = 0.35;
uniform vec3 rim_color : source_color = vec3(1.0, 0.92, 0.96);
uniform float rim_strength = 0.30;
uniform float emission_strength = 0.08;
// Gentle current sway for soft growth (0 for rocks).
uniform float sway_amount = 0.0;
// Distance (start, end in meters) over which an instance shrinks away; end 0 = never.
uniform vec2 fade_range = vec2(0.0);

varying vec3 world_pos;
varying vec3 world_nrm;
varying vec3 tint;
varying float height01;

void vertex() {
	vec4 pick = INSTANCE_CUSTOM;
	int index = clamp(int(pick.x * float(palette_size)), 0, palette_size - 1);
	vec3 chosen = index == 0 ? color_a : (index == 1 ? color_b : (index == 2 ? color_c : color_d));
	tint = chosen * (1.0 + (pick.y - 0.5) * 2.0 * brightness_variation);
	height01 = clamp(VERTEX.y / max(gradient_height, 0.001), 0.0, 1.0);

	vec3 origin = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	VERTEX *= uw_distance_keep(origin, MAIN_CAM_INV_VIEW_MATRIX[3].xyz, fade_range);
	if (sway_amount > 0.0) {
		float phase = origin.x * 0.31 + origin.z * 0.27 + pick.z * 6.2831;
		float bend = height01 * height01 * sway_amount;
		VERTEX.x += sin(TIME * 1.3 + phase) * bend;
		VERTEX.z += cos(TIME * 1.0 + phase * 1.3) * bend * 0.7;
	}
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	// Darker where the prop meets the seabed, brighter toward the tips.
	vec3 base = tint * mix(1.0 - gradient_strength, 1.0 + gradient_strength * 0.35, height01);
	base = uw_depth_tint(base, world_pos.y);
	float fresnel = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.6);

	ALBEDO = base;
	EMISSION = base * emission_strength
		+ rim_color * fresnel * rim_strength
		+ UW_CAUSTIC_COLOR * uw_caustics(world_pos, world_nrm) * 0.3;
	ROUGHNESS = 0.92;
	SPECULAR = 0.05;
	METALLIC = 0.0;
}

void light() {
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * uw_toon_band(dot(NORMAL, LIGHT)) * ATTENUATION / PI;
}
