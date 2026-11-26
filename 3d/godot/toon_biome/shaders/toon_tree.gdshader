shader_type spatial;
render_mode cull_disabled, specular_disabled;

#include "../../gamecore_toon_reef/shaders/underwater.gdshaderinc"

// two-part toon tree for arcore_procgen `tree` meshes: vertex COLOR.r marks
// trunk (0) or foliage (1), COLOR.g a seeded shade per foliage piece. Each
// instance picks a leaf color from the palette; foliage sways in the wind and
// gets a bright cel rim so canopies read as soft cartoon blobs.
uniform vec3 leaf_a : source_color = vec3(0.30, 0.72, 0.30);
uniform vec3 leaf_b : source_color = vec3(0.46, 0.80, 0.28);
uniform vec3 leaf_c : source_color = vec3(0.22, 0.60, 0.36);
uniform vec3 leaf_d : source_color = vec3(0.70, 0.82, 0.26);
uniform int leaf_count : hint_range(1, 4) = 1;
uniform vec3 trunk_color : source_color = vec3(0.50, 0.33, 0.22);
uniform float tree_height = 7.0;
uniform float sway_amount = 0.12;
uniform vec3 rim_color : source_color = vec3(1.0, 0.98, 0.86);
// Distance (start, end in meters) over which a tree shrinks away; end 0 = never.
uniform vec2 fade_range = vec2(0.0);

varying vec3 leaf;
varying float part;
varying float shade;
varying float height01;
varying vec3 world_pos;

void vertex() {
	vec4 pick = INSTANCE_CUSTOM;
	int index = clamp(int(pick.x * float(leaf_count)), 0, leaf_count - 1);
	leaf = index == 0 ? leaf_a : (index == 1 ? leaf_b : (index == 2 ? leaf_c : leaf_d));
	leaf *= 1.0 + (pick.y - 0.5) * 0.2;
	part = COLOR.r;
	shade = COLOR.g;
	height01 = clamp(VERTEX.y / max(tree_height, 0.01), 0.0, 1.0);

	vec3 origin = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	VERTEX *= uw_distance_keep(origin, MAIN_CAM_INV_VIEW_MATRIX[3].xyz, fade_range);
	float phase = origin.x * 0.13 + origin.z * 0.17 + pick.z * 6.2831;
	float bend = height01 * height01 * sway_amount;
	float gust = sin(TIME * 0.7 + origin.x * 0.02) * 0.5 + 0.5;
	VERTEX.x += sin(TIME * 1.1 + phase) * bend * (0.6 + gust);
	VERTEX.z += cos(TIME * 0.9 + phase * 1.3) * bend * 0.6;
	// Leaves rustle a little on top of the sway.
	VERTEX += NORMAL * part * sin(TIME * 3.0 + VERTEX.y * 2.0 + phase) * 0.03;
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 bark = trunk_color * (0.85 + 0.3 * uw_noise(vec2(world_pos.y * 3.0, atan(world_pos.x, world_pos.z) * 2.0)));
	vec3 foliage = leaf * mix(0.82, 1.12, shade) * mix(0.85, 1.08, height01);
	vec3 base = mix(bark, foliage, step(0.5, part));
	base = uw_depth_tint(base, world_pos.y);
	float fresnel = pow(1.0 - clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 3.0);
	ALBEDO = base;
	EMISSION = rim_color * smoothstep(0.45, 0.6, fresnel) * 0.18 * part;
	ROUGHNESS = 0.95;
}

void light() {
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * uw_toon_band(dot(NORMAL, LIGHT)) * ATTENUATION / PI;
}
