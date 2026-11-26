shader_type spatial;
render_mode specular_schlick_ggx;

#include "../../gamecore_toon_reef/shaders/underwater.gdshaderinc"

// storybook ground for overland and sky islands: painted grass on the flats
// with mown stripes and clover patches, sun-warmed meadow in the feature zone,
// layered rock on slopes, darker rock on overhang undersides, a sandy beach band
// at the water line, and the generator's baked crease shading (COLOR.r).
uniform vec3 grass_color : source_color = vec3(0.42, 0.80, 0.34);
uniform vec3 meadow_color : source_color = vec3(0.62, 0.86, 0.36);
uniform vec3 rock_color : source_color = vec3(0.62, 0.58, 0.54);
uniform vec3 under_color : source_color = vec3(0.46, 0.38, 0.50);
uniform vec3 sand_color : source_color = vec3(0.94, 0.86, 0.62);
uniform vec2 meadow_center = vec2(0.0, 0.0);
uniform float meadow_radius = 0.0;
// Beach band around this height (set far away to disable).
uniform float shore_level = -10000.0;
uniform float shore_width = 1.6;
uniform float occlusion_strength : hint_range(0.0, 1.0) = 0.8;
// Drifting cloud shadows (0 = none) and the height where snow begins.
uniform float cloud_shadow : hint_range(0.0, 1.0) = 0.2;
uniform float snow_level = 10000.0;
// Painted flower dots in the meadow, so it stays colorful beyond the real flowers' range.
uniform vec3 flower_a : source_color = vec3(1.0, 0.42, 0.48);
uniform vec3 flower_b : source_color = vec3(1.0, 0.86, 0.30);
// Burnt ground around a point (crash sites, campfires); radius 0 = none.
uniform vec2 scorch_center = vec2(0.0, 0.0);
uniform float scorch_radius = 0.0;

varying vec3 world_pos;
varying vec3 world_nrm;
varying float baked_ao;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	baked_ao = COLOR.r;
}

void fragment() {
	vec2 p = world_pos.xz;
	float footprint = max(length(dFdx(p)), length(dFdy(p)));
	float detail = 1.0 - smoothstep(0.08, 0.4, footprint);
	float up = world_nrm.y;
	float edge = (uw_noise(p * 0.7) - 0.5) * 0.16;
	float grass_mask = smoothstep(0.62 + edge, 0.78 + edge, up);

	// Grass: broad light/dark patches, soft diagonal stripes, clover dots.
	float patches = uw_noise(p * 0.08) * 0.6 + uw_noise(p * 0.31) * 0.4;
	float stripes = (step(0.5, fract((p.x + p.y) * 0.06 + uw_noise(p * 0.05) * 0.6)) - 0.5) * 0.06 * detail;
	vec3 grass = grass_color * (0.86 + patches * 0.24 + stripes);
	float clover = smoothstep(0.72, 0.76, uw_noise(p * 1.4)) * detail;
	grass = mix(grass, grass * 1.18 + vec3(0.02, 0.04, 0.0), clover * 0.5);
	if (meadow_radius > 0.0) {
		float meadow = smoothstep(meadow_radius + 10.0, meadow_radius * 0.6, length(p - meadow_center));
		grass = mix(grass, meadow_color * (0.9 + patches * 0.2), meadow * 0.75);
		vec2 cell = floor(p * 1.6);
		float dot_mask = step(0.8, uw_hash(cell)) * (1.0 - smoothstep(0.12, 0.3, length(fract(p * 1.6) - 0.5)));
		grass = mix(grass, mix(flower_a, flower_b, step(0.5, uw_hash(cell + 3.0))), dot_mask * meadow * smoothstep(0.02, 0.1, footprint));
	}

	// Rock: warped strata on slopes, darker plum-brown on overhangs.
	float side = uw_noise(vec2(p.x + p.y, world_pos.y) * 0.4);
	float strata_pos = world_pos.y * 0.45 + (uw_noise(p * 0.1) + side) * 1.4;
	float strata = floor(fract(strata_pos) * 3.0) / 2.0;
	vec3 rock = rock_color * (0.95 + strata * 0.2 + side * 0.12);
	rock = mix(rock, under_color * (0.9 + side * 0.2), smoothstep(0.05, -0.45, up));
	float moss = smoothstep(0.35, 0.6, up) * smoothstep(0.45, 0.6, uw_noise(p * 0.4 + 7.0));
	rock = mix(rock, grass_color * 0.85, moss * 0.6);

	vec3 base = mix(rock, grass, grass_mask);

	// Beach band at the water line, ripple-free and slightly wet below it.
	float beach = 1.0 - smoothstep(shore_width * 0.6, shore_width * 1.4, abs(world_pos.y - shore_level - 0.3 + edge * 4.0));
	base = mix(base, sand_color * (0.92 + patches * 0.12), beach * smoothstep(0.3, 0.6, up));
	base = mix(base, base * 0.78, step(world_pos.y, shore_level));

	if (scorch_radius > 0.0) {
		float burn = smoothstep(scorch_radius, scorch_radius * 0.35, length(p - scorch_center) + (uw_noise(p * 0.6) - 0.5) * scorch_radius * 0.5);
		base = mix(base, vec3(0.16, 0.13, 0.12) * (0.8 + patches * 0.5), burn * 0.85);
	}
	float snow = smoothstep(snow_level, snow_level + 8.0, world_pos.y + (patches - 0.5) * 10.0) * smoothstep(0.25, 0.6, up);
	base = mix(base, vec3(0.95, 0.97, 1.0), snow);
	vec2 drift = p + TIME * vec2(1.6, 0.5);
	float shade = uw_noise(drift * 0.011) * 0.65 + uw_noise(drift * 0.03) * 0.35;
	base *= 1.0 - cloud_shadow * smoothstep(0.52, 0.62, shade);

	float ao = mix(1.0, smoothstep(0.18, 0.92, baked_ao), occlusion_strength);
	base = mix(base * UW_SHADE_TINT, base, ao);
	base = uw_depth_tint(base, world_pos.y);

	ALBEDO = base;
	ROUGHNESS = 0.92;
	SPECULAR = 0.04;
	METALLIC = 0.0;
}

void light() {
	DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * uw_toon_band(dot(NORMAL, LIGHT)) * ATTENUATION / PI;
}
